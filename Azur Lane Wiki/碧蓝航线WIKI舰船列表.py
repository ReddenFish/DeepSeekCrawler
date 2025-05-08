import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 基础配置
BASE_URL = "https://azurlane.koumakan.jp"
SHIP_LIST_URL = f"{BASE_URL}/wiki/List_of_Ships"
IMAGE_BASE = "https://azurlane.netojuu.com/images"
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# 创建保存目录
os.makedirs("立绘", exist_ok=True)
os.makedirs("插画", exist_ok=True)

def clean_filename(filename):
    """清理文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def get_original_image_url(img_element):
    """
    从img元素中获取原始尺寸图片URL
    现在更精确地构造原始图片URL
    """
    src = img_element.get('src', '')
    if not src:
        return None
    
    # 处理缩略图URL
    if '/thumb/' in src:
        try:
            # 示例: https://azurlane.netojuu.com/images/thumb/b/bd/Universal_BulinEvent.png/531px-Universal_BulinEvent.png
            # 转换为: https://azurlane.netojuu.com/images/b/bd/Universal_BulinEvent.png
            match = re.match(r'https?://azurlane\.netojuu\.com/images/thumb/([^/]+)/([^/]+)/([^/]+\.(?:png|jpg|jpeg|gif))', src)
            if match:
                hash1, hash2, filename = match.groups()
                return f"{IMAGE_BASE}/{hash1}/{hash2}/{filename}"
        except Exception as e:
            print(f"解析图片URL出错: {e}")
            return None
    
    # 处理普通URL
    if src.startswith(IMAGE_BASE):
        return src
    
    # 处理相对URL
    return urljoin(IMAGE_BASE, src) if not src.startswith('http') else src

def download_image(url, filename, folder):
    """下载图片并保存"""
    try:
        if not url or not url.startswith('http'):
            print(f"无效的URL: {url}")
            return False

        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': BASE_URL,
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        }

        # 创建会话并设置重试策略
        session = requests.Session()
        retry = requests.adapters.HTTPAdapter(max_retries=3)
        session.mount('http://', retry)
        session.mount('https://', retry)

        # 随机延迟1-3秒
        time.sleep(2)

        response = session.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()

        # 验证内容类型
        if 'image' not in response.headers.get('Content-Type', '').lower():
            print(f"非图片内容: {url}")
            return False

        os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, clean_filename(filename))
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"成功下载: {filename}")
        return True
        
    except Exception as e:
        print(f"下载失败 {filename} | URL: {url} | 错误: {str(e)}")
        return False
    finally:
        session.close()

def get_ship_list():
    """获取所有舰船列表"""
    print("正在获取舰船列表...")
    try:
        response = requests.get(SHIP_LIST_URL, headers={'User-Agent': random.choice(USER_AGENTS)})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        ships = []
        tables = soup.find_all('table', {'class': ['wikitable', 'sortable']})
        
        for table in tables:
            for row in table.find_all('tr')[1:]:  # 跳过表头
                cells = row.find_all('td')
                if not cells:
                    continue
                    
                # 获取编号
                number = cells[0].get('data-sort-value', '').strip()
                
                # 获取角色页面链接
                link = cells[1].find('a')
                if not link:
                    continue
                page_url = urljoin(BASE_URL, link['href'])
                
                # 获取阵营
                faction = cells[-7].find('a')
                faction_name = faction.text.strip() if faction else "Unknown"
                
                ships.append({
                    'number': number,
                    'page_url': page_url,
                    'faction': faction_name.upper(),
                    'cn_name': None  # 稍后获取
                })
        
        print(f"共找到 {len(ships)} 艘舰船")
        return ships
    
    except Exception as e:
        print(f"获取舰船列表失败: {str(e)}")
        return []

def process_artwork(soup, ship_info):
    """处理插画下载"""
    gallery_div = soup.find('div', {'class': 'shipgirl-gallery'})
    if not gallery_div:
        return

    print(f"正在处理 {ship_info['number']} 的插画...")
    
    for img in gallery_div.find_all('img', {'class': 'mw-file-element'}):
        # 直接获取原始URL
        original_url = get_original_image_url(img)
        if not original_url:
            continue
        
        # 只使用原文件名
        filename = os.path.basename(original_url)
        
        download_image(original_url, filename, "插画")

def process_skins(soup, ship_info):
    """处理立绘下载 - 现在确保获取原始尺寸图片"""
    print(f"正在处理 {ship_info['number']} 的立绘...")
    
    for div in soup.find_all('div', {'class': 'shipskin-image'}):
        img = div.find('img', {'class': 'mw-file-element'})
        if not img:
            continue
        
        # 获取原始尺寸图片URL
        original_url = get_original_image_url(img)
        if not original_url:
            continue
        
        # 获取原始文件名（不带尺寸信息）
        original_name = os.path.basename(original_url)
        if 'px-' in original_name:
            original_name = original_name.split('px-')[-1]
        
        # 生成文件名：编号-中文名-阵营-原文件名
        filename = f"{ship_info['number']}-{ship_info['cn_name']}-{ship_info['faction']}-{original_name}"
        
        download_image(original_url, filename, "立绘")

def process_ship(ship):
    """处理单个舰船"""
    print(f"\n开始处理舰船: {ship['number']} - {ship['page_url']}")
    
    try:
        # 获取角色页面信息
        response = requests.get(ship['page_url'], headers={'User-Agent': random.choice(USER_AGENTS)})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 获取中文名
        headline = soup.find('div', {'class': 'card-headline'})
        if headline:
            cn_span = headline.find('span', {'lang': 'zh'})
            if cn_span:
                ship['cn_name'] = cn_span.text.strip()
        
        if not ship.get('cn_name'):
            ship['cn_name'] = "未知"
        
        # 跳转到Gallery页面
        gallery_url = f"{ship['page_url']}/Gallery"
        response = requests.get(gallery_url, headers={'User-Agent': random.choice(USER_AGENTS)})
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 处理立绘和插画
        process_skins(soup, ship)
        process_artwork(soup, ship)
        
    except Exception as e:
        print(f"处理舰船 {ship['number']} 时出错: {str(e)}")

def main():
    """主函数"""
    ships = get_ship_list()
    
    # 可以选择只处理前几个作为测试
    # ships = ships[:5]
    
    for ship in ships[555:]:
        process_ship(ship)
        # 每个舰船处理完后稍作休息
        time.sleep(random.uniform(2, 5))
    
    print("\n所有舰船处理完成！")

if __name__ == "__main__":
    main()