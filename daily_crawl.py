import json
import requests
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

# --- 📡 v3.3 双保险稳定源 ---
SOURCES = [
    {
        "category": "科技",
        "name": "IT之家",
        "url": "https://www.ithome.com/rss/",
        "emoji": "⚡",
        "max_items": 20
    },
    {
        "category": "财经",
        "name": "中新财经", # 【替换】改用和时事一样的源，确保能连通
        "url": "http://www.chinanews.com.cn/rss/finance.xml", 
        "emoji": "💰",
        "max_items": 20
    },
    {
        "category": "时事",
        "name": "中新要闻",
        "url": "http://www.chinanews.com.cn/rss/importnews.xml",
        "emoji": "🏛️",
        "max_items": 20
    }
]

# --- 🧠 AI 分析内核 ---
POLLINATIONS_URL = "https://text.pollinations.ai/{}"

def get_ai_summary(title, category):
    """AI 极速总结"""
    try:
        if category == "财经":
            prompt = f"As a financial analyst, summarize market impact in 1 sentence (Chinese). Title: '{title}'"
        elif category == "时事":
            prompt = f"Summarize event objectively in 1 sentence (Chinese). Title: '{title}'"
        else:
            prompt = f"Explain tech innovation in 1 sentence (Chinese). Title: '{title}'"
        
        # 增加 model=openai 参数，并对 prompt 进行 URL 编码
        target_url = POLLINATIONS_URL.format(quote(prompt))
        response = requests.get(target_url + "?model=openai", timeout=8) # 缩短超时，加速
        
        if response.status_code == 200:
            return response.text.strip()
        return "点击查看详情"
    except:
        return "点击阅读原文"

def fetch_rss_data(source_config):
    """RSS 抓取引擎 (智能编码版)"""
    category = source_config['category']
    print(f"📡 连接 [{category}] {source_config['name']}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(source_config['url'], headers=headers, timeout=15)
        
        if resp.status_code != 200:
            print(f"❌ 连接失败: {resp.status_code}")
            return []

        # --- 智能编码处理 ---
        # 先尝试自动识别，如果失败则回退到 utf-8，最后尝试 gbk
        content_decoded = ""
        try:
            # 优先使用 response 推测的编码，如果为空则默认 utf-8
            encoding = resp.encoding if resp.encoding else 'utf-8'
            content_decoded = resp.content.decode(encoding, errors='replace')
        except:
            # 备用方案：GBK (常见于老旧中文站)
            try:
                content_decoded = resp.content.decode('gbk', errors='replace')
            except:
                # 最后的挣扎：忽略错误强制解码
                content_decoded = resp.content.decode('utf-8', errors='ignore')

        # 解析 XML
        root = ET.fromstring(content_decoded)
        channel = root.find('channel')
        items = channel.findall('item')[:source_config['max_items']]

        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # 进度条
            if i % 5 == 0: print(f"   -> {category} ({i+1}/{source_config['max_items']}): {title[:8]}...")
            
            ai_text = get_ai_summary(title, category)
            # 清洗数据
            ai_text = ai_text.replace("'", "").replace('"', '').replace("\n", "")
            if len(ai_text) > 40: ai_text = ai_text[:39] + "..."

            results.append({
                "title": title,
                "link": link,
                "category": category,
                "emoji": source_config['emoji'],
                "aiReason": ai_text
            })
            
            # 稍微快一点，0.5秒间隔
            time.sleep(0.5)
            
        return results

    except Exception as e:
        print(f"❌ 解析错误 ({category}): {e}")
        return []

def update_html(news_list):
    if not news_list: return
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        js_data = ""
        for i, item in enumerate(news_list):
            js_data += "                {\n"
            js_data += f"                    id: {i}, platform: '{item['category']}', title: '{item['title']}', link: '{item['link']}', price: 'News', sales: '刚刚', score: {100-i}, emoji: '{item['emoji']}',\n"
            js_data += f"                    aiReason: '{item['aiReason']}'\n"
            js_data += "                },\n"

        pattern = r"(// DATA_START\n)(.*?)(// DATA_END)"
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, f"\\1{js_data}                \\3", content, flags=re.DOTALL)
            with open("index.html", "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"🎉 成功更新 {len(news_list)} 条情报！")
    except Exception as e:
        print(f"❌ HTML 写入失败: {e}")

if __name__ == "__main__":
    all_news = []
    for source in SOURCES:
        data = fetch_rss_data(source)
        all_news.extend(data)
        time.sleep(1)
    update_html(all_news)
