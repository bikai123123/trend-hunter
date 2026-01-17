import json
import requests
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

# --- 配置区 ---
# 什么值得买 (Smzdm) 官方 RSS 源
# 国内精选: https://feed.smzdm.com/guonei/
# 发现频道: https://feed.smzdm.com/faxian/
SMZDM_RSS_URL = "https://feed.smzdm.com/guonei/"

# Pollinations AI (免费、国内可用)
POLLINATIONS_URL = "https://text.pollinations.ai/{}"

def get_ai_insight(title, description):
    """用 AI 分析中文商品"""
    try:
        # 这里的 description 通常包含价格信息，很有用
        clean_desc = description[:50].replace('<br>', '')
        
        # 构造 Prompt: 角色是电商选品专家
        prompt = f"分析这款中国电商热门商品。用一句话（30字内）犀利点评它的卖点或价格优势。商品: '{title}'。详情: '{clean_desc}'"
        
        target_url = POLLINATIONS_URL.format(quote(prompt))
        # 增加 model=openai 参数，获取更好质量
        response = requests.get(target_url + "?model=openai", timeout=20)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "热度极高 (AI 分析暂缺)"
            
    except Exception as e:
        print(f"⚠️ AI 错误: {e}")
        return "超值好价"

def fetch_domestic_data():
    print("🚀 启动国内电商雷达 (Smzdm RSS)...")
    
    # 模拟浏览器 User-Agent，防止 RSS 接口拒绝 GitHub IP
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(SMZDM_RSS_URL, headers=headers, timeout=15)
        # 强制设置编码，防止中文乱码
        response.encoding = 'utf-8' 
        
        if response.status_code != 200:
            print(f"❌ 无法连接源站: {response.status_code}")
            return []

        # 解析 XML
        root = ET.fromstring(response.text)
        channel = root.find('channel')
        items = channel.findall('item')[:8] # 取前 8 条

        products = []
        for i, item in enumerate(items):
            title = item.find('title').text
            # 价格通常在 title 里，或者 description 里
            description = item.find('description').text
            link = item.find('link').text
            
            print(f"[{i+1}/8] 发现: {title[:15]}...")
            
            # AI 分析
            ai_reason = get_ai_insight(title, description)
            # 清洗文案
            ai_reason = ai_reason.replace("'", "").replace('"', '').replace("\n", "")

            # 简单的关键词 Emoji
            emoji = "🎁"
            if "电脑" in title or "Apple" in title or "手机" in title: emoji = "💻"
            elif "酒" in title: emoji = "🍺"
            elif "鞋" in title or "衣" in title: emoji = "👕"
            elif "券" in title: emoji = "🎫"

            # 提取价格 (粗略提取)
            price = "好价"
            # 尝试从标题提取数字 (比如 "199元")
            price_match = re.search(r'(\d+(?:\.\d+)?)(元|kw|万)', title)
            if price_match:
                price = price_match.group(0)

            products.append({
                "id": i + 888, 
                "platform": "什么值得买", # 标记来源
                "title": title, 
                "price": price, 
                "sales": "🔥 Hot", 
                "score": 99 - i, 
                "emoji": emoji, 
                "aiReason": ai_reason
            })
            
            time.sleep(2) # 礼貌抓取
            
        return products

    except Exception as e:
        print(f"❌ 解析失败: {e}")
        # 如果 XML 解析失败，打印出来看看内容
        return []

def update_html(new_data):
    if not new_data: return
    try:
        with open("index.html", "r", encoding="utf-8") as f: content = f.read()
        
        js_data = ""
        for p in new_data:
            js_data += "                {\n"
            js_data += f"                    id: {p['id']}, platform: '{p['platform']}', title: '{p['title']}', price: '{p['price']}', sales: '{p['sales']}', score: {p['score']}, emoji: '{p['emoji']}',\n"
            js_data += f"                    aiReason: '{p['aiReason']}'\n"
            js_data += "                },\n"

        pattern = r"(// DATA_START\n)(.*?)(// DATA_END)"
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, f"\\1{js_data}                \\3", content, flags=re.DOTALL)
            with open("index.html", "w", encoding="utf-8") as f: f.write(new_content)
            print("🎉 国内数据更新成功！")
    except: pass

if __name__ == "__main__":
    data = fetch_domestic_data()
    update_html(data)
