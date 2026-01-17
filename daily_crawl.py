import json
import requests
import re
import time
import os

# --- 配置区 ---
HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def get_available_model(api_key):
    """动态获取可用模型"""
    url = f"{BASE_URL}/models?key={api_key}"
    try:
        print("🔍 正在适配 Google AI 模型...")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200: return None
        data = resp.json()
        for model in data.get('models', []):
            if 'generateContent' in model.get('supportedGenerationMethods', []):
                if 'flash' in model.get('name') or 'pro' in model.get('name'):
                    print(f"✅ 锁定模型: {model.get('name')}")
                    return model.get('name')
        return None
    except: return None

def get_ai_insight(title, model_name, api_key):
    """调用 AI"""
    if not model_name or not api_key: return f"HN 热榜: {title}"
    try:
        target_url = f"{BASE_URL}/{model_name}:generateContent?key={api_key}"
        prompt = f"Translate to Chinese and summarize in 1 sentence (max 20 words). Title: '{title}'"
        payload = { "contents": [{ "parts": [{"text": prompt}] }] }
        headers = {'Content-Type': 'application/json'}
        
        # 发送请求
        response = requests.post(target_url, headers=headers, data=json.dumps(payload), timeout=10)
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        elif response.status_code == 429:
            print("⏳ 触发限流，AI 休息中...")
            return "🔥 极高热度话题 (AI 繁忙)"
        else:
            return "AI 暂时无法解析"
    except: return "AI 分析不可用"

def fetch_hn_data():
    print("🚀 启动...")
    api_key = os.environ.get("GEMINI_API_KEY")
    current_model = get_available_model(api_key) if api_key else None

    try:
        # 获取前 5 个 (减少数量，保证成功率)
        top_ids = requests.get(HN_TOP_URL, timeout=10).json()[:5]
        
        products = []
        for i, item_id in enumerate(top_ids):
            item = requests.get(HN_ITEM_URL.format(item_id), timeout=5).json()
            title = item.get('title', 'No Title').replace("'", "\\'")
            score = item.get('score', 0)
            
            print(f"[{i+1}/5] 分析: {title[:20]}...")
            
            if current_model:
                ai_reason = get_ai_insight(title, current_model, api_key)
                # 清洗换行符和引号
                ai_reason = ai_reason.replace("'", "").replace("\n", "").replace('"', '')
            else:
                ai_reason = f"热度: {score}"

            # Emoji
            emoji = "📰"
            if "show hn" in title.lower(): emoji = "🚀"
            elif "ai" in title.lower(): emoji = "🤖"

            products.append({
                "id": item_id, "platform": "HackerNews", "title": title,
                "price": "Free", "sales": f"{score} 🔥", "score": score,
                "emoji": emoji, "aiReason": ai_reason
            })
            
            # 【关键修改】休息 5 秒！防止 429 错误
            time.sleep(5)
            
        return products
    except Exception as e:
        print(f"❌ 失败: {e}")
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
