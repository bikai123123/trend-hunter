import json
import requests
import re
import random
import time

# 1. 目标 URL (Reddit)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
URL = "https://www.reddit.com/r/shutupandtakemymoney/top.json?t=week&limit=10"

def get_mock_data():
    """本地网络不通时，生成模拟数据，保证流程跑通"""
    print("⚠️ 检测到网络限制，切换至【本地模拟数据模式】...")
    mock_titles = [
        "Transparent Cyberpunk Power Bank (200W)",
        "Levitating Plant Pot - AI Monitor",
        "E-Ink Smartphone Case for iPhone 15",
        "Laser Projection Keyboard V2",
        "Smart Coffee Table with Fridge"
    ]
    products = []
    for i, title in enumerate(mock_titles):
        products.append({
            "id": i + 100,
            "platform": "LocalTest", # 标记为本地测试
            "title": title,
            "price": f"${random.randint(20, 200)}.99",
            "sales": f"{random.randint(1000, 5000)} 🔥",
            "score": 99 - i,
            "emoji": "🧪", # 测试管图标
            "aiReason": "这是本地生成的测试数据。当你部署到 GitHub 后，这里会自动变成真实的 Reddit 爆品分析。"
        })
    return products

def fetch_reddit_data():
    print("🕷️ 正在尝试爬取 Reddit 爆品数据...")
    try:
        # 设置 5 秒超时，避免卡住
        resp = requests.get(URL, headers=HEADERS, timeout=5)
        
        # 检查是否是合法的 JSON
        if resp.status_code != 200 or 'application/json' not in resp.headers.get('Content-Type', ''):
            raise Exception("非 JSON 响应 (可能是网络阻断)")
            
        data = resp.json()
        posts = data['data']['children']
        
        products = []
        for i, post in enumerate(posts):
            item = post['data']
            title = item['title'].replace("'", "\\'")[:50] + "..."
            score = item['score']
            
            emoji = "📦"
            if "light" in title.lower(): emoji = "💡"
            elif "game" in title.lower(): emoji = "🎮"
            
            product = {
                "id": i + 1,
                "platform": "Reddit",
                "title": title,
                "price": "$??",
                "sales": f"{score} ⬆️",
                "score": 95 - i,
                "emoji": emoji,
                "aiReason": f"来自 Reddit 高赞帖 ({score} upvotes)。海外极客社区热门话题。"
            }
            products.append(product)
        print(f"✅ 网络畅通！成功获取 {len(products)} 条真实数据")
        return products
        
    except Exception as e:
        print(f"❌ 爬取失败: {e}")
        # 【关键修改】失败时返回模拟数据，而不是空列表
        return get_mock_data()

def update_html(new_data):
    print("📝 正在更新 index.html ...")
    
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        js_data_str = ""
        for p in new_data:
            js_data_str += "                {\n"
            js_data_str += f"                    id: {p['id']}, platform: '{p['platform']}', title: '{p['title']}', price: '{p['price']}', sales: '{p['sales']}', score: {p['score']}, emoji: '{p['emoji']}',\n"
            js_data_str += f"                    aiReason: '{p['aiReason']}'\n"
            js_data_str += "                },\n"

        pattern = r"(// DATA_START\n)(.*?)(// DATA_END)"
        new_content = re.sub(pattern, f"\\1{js_data_str}                \\3", content, flags=re.DOTALL)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("🎉 网页更新完成！请打开 index.html 查看结果。")
        
    except Exception as e:
        print(f"❌ 文件写入错误: {e}")
        print("请检查 index.html 里是否包含 // DATA_START 和 // DATA_END 标记")

if __name__ == "__main__":
    data = fetch_reddit_data()
    if data:
        update_html(data)