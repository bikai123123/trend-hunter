import json
import requests
import re
import time

# --- 目标：Hacker News (硅谷最火的科技热榜) ---
# 这是一个官方公开 API，极其稳定，绝不会被封
TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

def fetch_hn_data():
    print("🚀 正在连接 Hacker News 接口...")
    try:
        # 1. 获取前 10 个热帖 ID
        resp = requests.get(TOP_STORIES_URL, timeout=10)
        top_ids = resp.json()[:10]
        
        products = []
        # 2. 遍历 ID 获取详细信息
        for i, item_id in enumerate(top_ids):
            item_resp = requests.get(ITEM_URL.format(item_id), timeout=5)
            item = item_resp.json()
            
            # 清洗数据
            title = item.get('title', 'No Title').replace("'", "\\'") # 转义单引号
            score = item.get('score', 0)
            url = item.get('url', '#')
            
            # 简单的 Emoji 映射
            emoji = "📰"
            if "Show HN" in title: emoji = "🚀" # 产品发布
            elif "Ask HN" in title: emoji = "💬"
            elif "AI" in title or "GPT" in title: emoji = "🤖"
            elif "Launch" in title: emoji = "🔥"
            
            # 模拟 AI 点评
            ai_reason = f"Hacker News 热榜第 {i+1} 名！当前热度 {score} points。全球极客正在讨论此话题。"

            products.append({
                "id": item_id,
                "platform": "HackerNews",
                "title": title,
                "price": "Free", # HN 主要是资讯/开源项目
                "sales": f"{score} 🔥",
                "score": score, 
                "emoji": emoji,
                "aiReason": ai_reason
            })
            print(f"   - 获取成功: {title[:20]}...")
            time.sleep(0.1) # 礼貌请求，避免并发过快
            
        print(f"✅ 成功获取 {len(products)} 条真实科技情报")
        return products
        
    except Exception as e:
        print(f"❌ 接口请求失败: {e}")
        return [] # 这里如果失败，就让它空着，不写入模拟数据了，方便排查

def update_html(new_data):
    if not new_data:
        print("⚠️ 没有新数据，跳过更新")
        return

    print("📝 正在注入 HTML ...")
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        js_data_str = ""
        for p in new_data:
            js_data_str += "                {\n"
            js_data_str += f"                    id: {p['id']}, platform: '{p['platform']}', title: '{p['title']}', price: '{p['price']}', sales: '{p['sales']}', score: {p['score']}, emoji: '{p['emoji']}',\n"
            js_data_str += f"                    aiReason: '{p['aiReason']}'\n"
            js_data_str += "                },\n"

        # 核心替换逻辑
        pattern = r"(// DATA_START\n)(.*?)(// DATA_END)"
        if not re.search(pattern, content, re.DOTALL):
            print("❌ 致命错误：在 index.html 里找不到 // DATA_START 标记！请检查文件。")
            return

        new_content = re.sub(pattern, f"\\1{js_data_str}                \\3", content, flags=re.DOTALL)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("🎉 index.html 修改完成！准备提交...")
        
    except Exception as e:
        print(f"❌ 文件操作失败: {e}")

if __name__ == "__main__":
    data = fetch_hn_data()
    update_html(data)
