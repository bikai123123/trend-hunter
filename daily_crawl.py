import json
import requests
import re
import time
import xml.etree.ElementTree as ET
from urllib.parse import quote

# --- 📡 v2.0 情报源配置 (修正版) ---
SOURCES = [
    {
        "category": "科技",
        "name": "IT之家",
        "url": "https://www.ithome.com/rss/",
        "emoji": "⚡",
        "max_items": 5
    },
    {
        "category": "财经",
        "name": "新浪财经", # 替换了不稳定的 36氪
        "url": "http://rss.sina.com.cn/roll/finance/hot_roll.xml", # 老牌稳定源
        "emoji": "📈",
        "max_items": 5
    },
    {
        "category": "时事",
        "name": "中新网",
        "url": "http://www.chinanews.com.cn/rss/importnews.xml",
        "emoji": "🏛️",
        "max_items": 5
    }
]


# --- 🧠 AI 配置 ---
POLLINATIONS_URL = "https://text.pollinations.ai/{}"

def get_ai_summary(title, category):
    """根据新闻分类，调用 AI 生成一句话总结"""
    try:
        # 针对不同分类微调 Prompt
        if category == "财经":
            role = "financial analyst"
            focus = "identify market impact or investment signal"
        elif category == "时事":
            role = "political commentator"
            focus = "summarize the core event objectively"
        else: # 科技
            role = "tech editor"
            focus = "explain the innovation or impact"

        prompt = f"As a {role}, translate title to Chinese (if needed) and {focus} in 1 sentence (max 30 words). Title: '{title}'"
        
        target_url = POLLINATIONS_URL.format(quote(prompt))
        # 使用 openai 模型以获得更好理解力
        response = requests.get(target_url + "?model=openai", timeout=20)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            return "AI 正在分析中..."
    except:
        return "暂无 AI 点评"

def fetch_rss_data(source_config):
    """通用的 RSS 抓取函数"""
    category = source_config['category']
    print(f"📡 正在连接 [{category}] {source_config['name']} ...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(source_config['url'], headers=headers, timeout=15)
        resp.encoding = 'utf-8' # 防止中文乱码
        
        if resp.status_code != 200:
            print(f"❌ {category} 源连接失败: {resp.status_code}")
            return []

        # 解析 XML
        root = ET.fromstring(resp.text)
        channel = root.find('channel')
        items = channel.findall('item')[:source_config['max_items']] # 限制条数

        results = []
        for item in items:
            title = item.find('title').text
            # 这里的 link 留着备用，虽然我们只展示标题
            # link = item.find('link').text 
            
            print(f"   -> 抓取: {title[:15]}...")
            
            # AI 总结
            ai_text = get_ai_summary(title, category)
            # 清洗
            ai_text = ai_text.replace("'", "").replace('"', '').replace("\n", "")
            if len(ai_text) > 50: ai_text = ai_text[:49] + "..."

            results.append({
                "title": title,
                "category": category,
                "emoji": source_config['emoji'],
                "aiReason": ai_text
            })
            
            # 关键：避免请求过快被 AI 封锁，每个请求间隔 1.5 秒
            time.sleep(1.5)
            
        return results

    except Exception as e:
        print(f"❌ {category} 解析错误: {e}")
        return []

def main():
    print("🚀 启动全网情报聚合 (5x Daily)...")
    
    all_news = []
    
    # 遍历所有源
    for source in SOURCES:
        news_items = fetch_rss_data(source)
        all_news.extend(news_items)
        # 源与源之间休息 2 秒
        time.sleep(2)

    # 如果完全没数据，就不更新
    if not all_news:
        print("⚠️ 本次未获取到任何数据，跳过更新")
        return

    # 生成 HTML 数据
    update_html(all_news)

def update_html(news_list):
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        js_data = ""
        # 赋予 ID
        for i, item in enumerate(news_list):
            # 颜色逻辑：不同分类给不同热度标签颜色（通过 emoji 区分视觉）
            # 这里复用之前的结构
            js_data += "                {\n"
            js_data += f"                    id: {i}, platform: '{item['category']}', title: '{item['title']}', price: 'News', sales: '刚刚', score: {100-i}, emoji: '{item['emoji']}',\n"
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
    main()


