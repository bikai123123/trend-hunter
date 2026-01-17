import json
import requests
import re
import time
from urllib.parse import quote

# --- 配置区 ---
HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# Pollinations AI (免 Key，免费，无限制接口)
# 原理：直接通过 URL 传参获取 AI 响应
POLLINATIONS_URL = "https://text.pollinations.ai/{}"

def get_ai_insight(title):
    """调用 Pollinations AI 生成中文短评"""
    try:
        # 1. 构造 Prompt
        # 要求：翻译成中文，并用一句话（30字内）犀利点评
        prompt = f"Translate the following Hacker News title to Chinese and explain why it is interesting in 1 sentence (max 30 words, professional tone): '{title}'"
        
        # 2. URL 编码 (处理空格和特殊字符)
        safe_prompt = quote(prompt)
        target_url = POLLINATIONS_URL.format(safe_prompt)
        
        # 3. 发送 GET 请求 (Pollinations 极其简单，直接 GET 即可)
        # 增加 model=openai 参数试图获取更高质量回答，也可以不加
        response = requests.get(target_url + "?model=openai", timeout=15)
        
        if response.status_code == 200:
            return response.text.strip()
        else:
            return f"热度: High (AI 接口 {response.status_code})"
            
    except Exception as e:
        print(f"⚠️ AI 请求失败: {e}")
        return "AI 连接超时"

def fetch_hn_data():
    print("🚀 启动 (Pollinations 无限制版)...")
    
    try:
        # 恢复到抓取 8 条！因为没有配额限制了！
        top_ids = requests.get(HN_TOP_URL, timeout=10).json()[:8]
        
        products = []
        for i, item_id in enumerate(top_ids):
            item = requests.get(HN_ITEM_URL.format(item_id), timeout=5).json()
            title = item.get('title', 'No Title').replace("'", "\\'")
            score = item.get('score', 0)
            
            print(f"[{i+1}/8] 分析: {title[:20]}...")
            
            # 调用 AI
            ai_reason = get_ai_insight(title)
            
            # 清洗数据 (防止 AI 返回 Markdown 格式或引号破坏 JS)
            ai_reason = ai_reason.replace("'", "").replace('"', '').replace("\n", "")
            # 如果 AI 返回太长，强制截断
            if len(ai_reason) > 50: ai_reason = ai_reason[:49] + "..."

            # Emoji 逻辑
            emoji = "📰"
            if "show hn" in title.lower(): emoji = "🚀"
            elif "ai" in title.lower(): emoji = "🤖"
            elif "google" in title.lower(): emoji = "🔍"

            products.append({
                "id": item_id, "platform": "HackerNews", "title": title,
                "price": "Free", "sales": f"{score} 🔥", "score": score,
                "emoji": emoji, "aiReason": ai_reason
            })
            
            # 虽然无限制，但还是礼貌性停顿 1 秒，防止网络堵塞
            time.sleep(1)
            
        return products
    except Exception as e:
        print(f"❌ 错误: {e}")
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
            print("🎉 更新成功！")
    except: pass

if __name__ == "__main__":
    data = fetch_hn_data()
    update_html(data)
