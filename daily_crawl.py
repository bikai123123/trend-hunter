import json
import requests
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

# --- 📡 v3.1 稳定情报源 ---
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
        "name": "澎湃财经",  # 【替换】新浪 -> 澎湃 (UTF-8, 更稳定)
        "url": "https://www.thepaper.cn/rss.jsp?sectionid=25951",
        "emoji": "📈",
        "max_items": 20
    },
    {
        "category": "时事",
        "name": "中新网",
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
        
        target_url = POLLINATIONS_URL.format(quote(prompt))
        # 超时设为 10 秒，防止阻塞
        response = requests.get(target_url + "?model=openai", timeout=10)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "点击查看详情"
    except:
        return "点击阅读原文"

def fetch_rss_data(source_config):
    """RSS 抓取引擎 (增强版)"""
    category = source_config['category']
    print(f"📡 连接 [{category}] {source_config['name']}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(source_config['url'], headers=headers, timeout=15)
        
        # 【关键修复】不要强制 encoding='utf-8'，
        # 而是直接把二进制 content 喂给 ET，让它根据 XML 头自动识别编码 (GBK/UTF-8 通吃)
        
        if resp.status_code != 200:
            print(f"❌ 连接失败: {resp.status_code}")
            return []

        # 使用 resp.content (Bytes) 而不是 resp.text (String)
        root = ET.fromstring(resp.content)
        
        # 澎湃新闻的结构可能略有不同，做通用适配
        channel = root.find('channel')
        items = channel.findall('item')[:source_config['max_items']]

        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # 进度打印
            if i % 5 == 0: print(f"   -> 处理第 {i+1} 条: {title[:10]}...")
            
            ai_text = get_ai_summary(title, category)
            ai_text = ai_text.replace("'", "").replace('"', '').replace("\n", "")
            if len(ai_text) > 50: ai_text = ai_text[:49] + "..."

            results.append({
                "title": title,
                "link": link,
                "category": category,
                "emoji": source_config['emoji'],
                "aiReason": ai_text
            })
            
            # 这里的 sleep 稍微调小一点，保证 60 条能跑完
            time.sleep(0.8)
            
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
        time.sleep(2)
    update_html(all_news)
