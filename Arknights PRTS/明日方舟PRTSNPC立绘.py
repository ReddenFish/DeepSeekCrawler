import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests
from urllib.parse import unquote, urljoin, urlparse

# 设置Chrome选项
chrome_options = Options()
# chrome_options.add_argument("--headless")  # 调试时先注释掉
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

# 替换为你的chromedriver路径
driver_path = "C:/Users/mimsd/.cache/selenium/chromedriver/win64/135.0.7049.114/chromedriver.exe"
service = Service(driver_path)

# 初始化浏览器
driver = webdriver.Chrome(service=service, options=chrome_options)

# 目标网页URL
base_url = "https://prts.wiki"
target_url = "https://prts.wiki/w/%E5%89%A7%E6%83%85%E8%B5%84%E6%BA%90%E6%A6%82%E8%A7%88"

driver.get(target_url)
time.sleep(15)  # 等待页面加载

# 第一部分：获取NPC部分的所有图片链接
image_links = []

# 直接查找所有带有class="image"的<a>标签，这些是图片链接
a_tags = driver.find_elements(By.XPATH, '//a[@class="image"]')

for a_tag in a_tags:
    # 检查这个<a>标签是否在NPC部分（通过检查父级结构中是否有NPC标题）
    try:
        # 获取href属性
        href = a_tag.get_attribute("href")
        if href and ("文件:" in href or "File:" in href or "Avg_avg_npc" in href):
            # 补全URL
            full_url = urljoin(base_url, href)
            image_links.append(full_url)
            print(f"找到图片链接: {full_url}")
    except Exception as e:
        print(f"处理链接时出错: {str(e)}")

print(f"共找到 {len(image_links)} 个图片链接")

# 第二部分：访问每个图片页面并下载原始图片
if not os.path.exists("NPC立绘"):
    os.makedirs("NPC立绘")

for img_page_url in image_links[700:]:
    try:
        print(f"\n正在处理: {img_page_url}")
        driver.get(img_page_url)
        time.sleep(2)  # 等待页面加载
        
        # 获取原始图片URL - 直接从img标签获取srcset中的最高分辨率图片
        img_tag = driver.find_element(By.XPATH, '//div[@class="fullImageLink"]//img')
        
        # 尝试获取srcset中的最高分辨率图片
        srcset = img_tag.get_attribute("srcset")
        if srcset:
            # 获取srcset中最大的图片（通常是最后一个）
            image_url = srcset.split()[-2]  # 获取倒数第二个元素（URL）
        else:
            # 如果没有srcset，则使用src属性
            image_url = img_tag.get_attribute("src")
        
        # 移除URL中的查询参数
        image_url = image_url.split('?')[0]
        
        # 获取图片文件名
        alt_text = img_tag.get_attribute("alt")
        if alt_text.startswith(("文件:", "File:")):
            clean_name = alt_text.split(":", 1)[1].strip()
        else:
            clean_name = alt_text
        
        # 清理文件名
        clean_name = unquote(clean_name)
        clean_name = clean_name.replace("™", "TM").replace(" ", "_")
        clean_name = "".join(c for c in clean_name if c not in '\/:*?"<>|').strip()
        
        # 从URL中提取文件扩展名
        parsed_url = urlparse(image_url)
        filename = os.path.basename(parsed_url.path)
        file_ext = os.path.splitext(filename)[1] or ".png"
        
        # 确保文件名不重复
        file_path = os.path.join("NPC立绘", f"{clean_name}{file_ext}")
        
        print(f"图片URL: {image_url}")
        print(f"文件名: {clean_name}{file_ext}")
        
        # 下载图片
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"已保存: {file_path}")
        else:
            print(f"下载失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"处理 {img_page_url} 时出错: {str(e)}")

# 关闭浏览器
driver.quit()
print("任务完成")