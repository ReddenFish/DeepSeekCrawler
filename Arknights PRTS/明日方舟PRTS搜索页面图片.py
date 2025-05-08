import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import requests

def wait_for_user_confirmation():
    print("\n请手动打开目标网页并确认页面已完全加载...")
    print("确认页面加载完成后，请在此处输入'y'并按回车键继续爬取")
    print("或输入'n'取消操作")
    while True:
        user_input = input("是否继续?(y/n): ").lower()
        if user_input == 'y':
            return True
        elif user_input == 'n':
            return False
        else:
            print("无效输入，请输入'y'或'n'")

def get_image_links(driver):
    # 找到所有table.searchResultImage中的a.image元素
    image_links = driver.find_elements(By.CSS_SELECTOR, "table.searchResultImage a.image")
    return image_links

def download_images(driver, detail_urls):
    # 创建保存图片的目录
    if not os.path.exists("prts搜索"):
        os.makedirs("prts搜索")
    
    for i, url in enumerate(detail_urls, 1):
        try:
            print(f"\n正在处理第 {i}/{len(detail_urls)} 个页面: {url}")
            driver.get(url)
            
            # 等待用户确认页面加载完成
            time.sleep(2)
            
            # 获取图片元素
            full_image_link = driver.find_element(By.CSS_SELECTOR, "div.fullImageLink a")
            img_element = full_image_link.find_element(By.TAG_NAME, "img")
            
            # 获取图片URL和名称
            image_url = full_image_link.get_attribute("href")
            image_name = img_element.get_attribute("alt").replace("文件:", "").strip()
            
            print(f"图片URL: {image_url}")
            print(f"图片名称: {image_name}")
            
            # 下载图片
            response = requests.get(image_url, stream=True)
            if response.status_code == 200:
                # 清理文件名中的非法字符
                safe_name = "".join([c for c in image_name if c not in r'\/:*?"<>|'])
                file_path = os.path.join("prts搜索", f"{safe_name}.png")
                
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                print(f"图片已保存为: {file_path}")
            else:
                print(f"下载失败，状态码: {response.status_code}")
                
        except Exception as e:
            print(f"处理第 {i} 个页面时出错: {str(e)}")
            continue

def main():
    # 设置Chrome选项 - 不使用无头模式以便观察
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # 替换为你的chromedriver路径
    driver_path = "C:/Users/mimsd/.cache/selenium/chromedriver/win64/135.0.7049.114/chromedriver.exe"  # 或者指定完整路径如 "C:/path/to/chromedriver.exe"
    service = Service(driver_path)

    # 初始化浏览器
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # 第一步：等待用户手动打开目标网页
        print("请手动在浏览器中打开PRTS Wiki的搜索结果页面")
        print("例如: https://prts.wiki/w/特殊:搜索?search=宣传图&fulltext=1&ns6=1")
        print("等待页面完全加载后返回此处继续...")
        
        if not wait_for_user_confirmation():
            print("操作已取消")
            return
        
        # 获取当前浏览器URL
        target_url = driver.current_url
        print(f"开始爬取当前页面: {target_url}")
        
        # 获取所有图片链接
        image_links = get_image_links(driver)
        
        # 构建完整的URL列表
        base_url = "https://prts.wiki"
        detail_urls = [link.get_attribute("href") for link in image_links]
        
        print(f"\n找到 {len(detail_urls)} 个图片页面")
        print("即将开始下载图片...")
        
        # 第二步：下载图片
        download_images(driver, detail_urls)
            
    finally:
        # 关闭浏览器
        driver.quit()
        print("\n爬虫运行结束")

if __name__ == "__main__":
    main()
    print("所有操作完成")