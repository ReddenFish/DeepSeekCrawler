import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import re

# 配置
WAIT_TIME = 3  # 每次请求间隔3秒
OUTPUT_DIR = "新增时装"  # 输出目录
BASE_URL = "https://prts.wiki"

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

def sanitize_filename(filename):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def download_image(url, filepath):
    """下载图片并保存"""
    if not url.startswith("http"):
        url = "https:" + url
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)

def collect_specific_operators(driver):
    """收集'新增时装'部分的干员信息"""
    operator_list = []
    
    # 等待页面加载
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "mp-operators")))
    
    # 获取"新增时装"部分的干员
    new_skin_title = driver.find_element(By.XPATH, "//div[contains(@class, 'mp-operators-title') and contains(., '新增时装')]")
    new_skin_section = new_skin_title.find_element(By.XPATH, "./following-sibling::div[1]")
    skin_operators = new_skin_section.find_elements(By.TAG_NAME, "a")
    
    for operator in skin_operators:
        try:
            operator_url = operator.get_attribute("href")
            chinese_name = operator.get_attribute("title")
            # 从URL提取英文名（作为备用，可能不准确）
            english_name = os.path.basename(operator_url)
            operator_id = f"SKIN_{len(operator_list)+1}"  # 生成临时ID
            
            operator_info = {
                "chinese_name": chinese_name,
                "english_name": english_name,
                "operator_id": operator_id,
                "operator_url": operator_url
            }
            operator_list.append(operator_info)
        except Exception as e:
            print(f"跳过无效元素(新增时装): {str(e)}")
    
    return operator_list

def process_operator(driver, operator_info):
    """处理单个干员，下载所有立绘"""
    chinese_name = operator_info["chinese_name"]
    english_name = operator_info["english_name"]
    operator_id = operator_info["operator_id"]
    operator_url = operator_info["operator_url"]
    
    print(f"\n处理干员: {chinese_name} ({operator_id})")
    
    try:
        # 使用新标签页访问详情页
        driver.execute_script(f"window.open('{operator_url}');")
        driver.switch_to.window(driver.window_handles[1])
        
        # 等待立绘区域加载
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "charimg-wrapper")))
        
        # 查找所有立绘img标签
        img_elements = driver.find_elements(By.CSS_SELECTOR, "#charimg-wrapper img")
        
        img = img_elements[-1]
        img_id = img.get_attribute("id")
        img_src = img.get_attribute("src")
        
        if img_src and img_id:
            # 清理干员名中的非法字符
            safe_chinese = sanitize_filename(chinese_name.strip())
            safe_english = sanitize_filename(english_name.strip())
            
            # 构建文件名
            filename = f"{operator_id}_{safe_chinese}_{safe_english}_{img_id}.png"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            print(f"正在下载: {filename}")
            download_image(img_src, filepath)
            time.sleep(WAIT_TIME)
                
    except Exception as e:
        print(f"处理干员 {chinese_name} 时出错: {str(e)}")
    finally:
        # 关闭详情页标签页并切换回主标签页
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

def main():
    driver = webdriver.Chrome()
    driver.maximize_window()
    
    try:
        print("请手动导航到PRTS首页: https://prts.wiki/w/首页")
        input("准备好后按Enter键继续...")
        
        # 第一步：收集特定部分的干员信息
        print("\n正在收集'近期新增'和'新增时装'干员信息...")
        operator_list = collect_specific_operators(driver)
        print(f"共找到 {len(operator_list)} 个干员")
        
        # 第二步：逐个处理干员
        print("\n开始下载立绘...")
        for operator_info in operator_list:
            process_operator(driver, operator_info)
            
        print("\n所有干员处理完成!")
        
    except Exception as e:
        print(f"程序出错: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()