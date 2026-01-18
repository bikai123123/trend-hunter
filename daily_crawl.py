import json
import requests
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

# --- 📡 v3.0 高容量情报源 ---
SOURCES = [
    {
        "category": "科技",
        "name": "IT之家",
        "url": "https://www.ithome.com/rss/",
        "emoji": "⚡",
        "max_items": 20  # 扩容至 20 条
    },
    {
        "category": "财经",
        "name": "新浪财经",
        "url": "http://rss.sina.com.cn/roll/finance/hot_roll.xml",
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
    """AI 极速总结模式"""
    try:
        if category == "财经":
            prompt = f"As a financial analyst, summarize market impact in 1 sentence (Chinese). Title: '{title}'"
        elif category == "时事":
            prompt = f"Summarize event objectively in 1 sentence (Chinese). Title: '{title}'"
        else:
            prompt = f"Explain tech innovation in 1 sentence (Chinese). Title: '{title}'"
        
        target_url = POLLINATIONS_URL.format(quote(prompt))
        # 缩短超时时间，保证大量抓取时的整体速度
        response = requests.get(target_url + "?model=openai", timeout=10)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "点击查看详情"
    except:
        return "点击阅读原文"

def fetch_rss_data(source_config):
    """RSS 抓取引擎"""
    category = source_config['category']
    print(f"📡 连接 [{category}] {source_config['name']} (目标: 20条)...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(source_config['url'], headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        
        if resp.status_code != 200:
            print(f"❌ 连接失败: {resp.status_code}")
            return []

        root = ET.fromstring(resp.text)
        channel = root.find('channel')
        items = channel.findall('item')[:source_config['max_items']]

        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            # 关键：抓取原文链接
            link = item.find('link').text
            
            # 进度条打印，避免日志太长
            if i % 5 == 0: print(f"   -> 正在处理第 {i+1} 条...")
            
            ai_text = get_ai_summary(title, category)
            ai_text = ai_text.replace("'", "").replace('"', '').replace("\n", "")
            if len(ai_text) > 50: ai_text = ai_text[:49] + "..."

            results.append({
                "title": title,
                "link": link,  # 新增字段
                "category": category,
                "emoji": source_config['emoji'],
                "aiReason": ai_text
            })
            
            # 稍微加快速度：1秒间隔 (60条约耗时1分钟)
            time.sleep(1)
            
        return results

    except Exception as e:
        print(f"❌ 解析错误: {e}")
        return []

def update_html(news_list):
    if not news_list: return
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        js_data = ""
        for i, item in enumerate(news_list):
            js_data += "                {\n"
            # 写入 link 字段
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
        all_news.extend(fetch_rss_data(source))
        time.sleep(2)
    update_html(all_news)
