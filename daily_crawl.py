import json
import requests
import re
import time
import os

# --- 配置区 ---
# Hacker News API
TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# Gemini API (直接使用 HTTP 接口，绕过 SDK 版本问题)
# 使用 gemini-1.5-flash，这是目前免费版最标准的模型
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={}"

def get_ai_insight(title):
    """直接发送 HTTP 请求调用 Gemini"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return f"Hacker News 热榜话题：{title}"
    
    try:
        # 1. 构造请求 URL
        target_url = GEMINI_URL.format(api_key)
        
        # 2. 构造 Prompt
        prompt_text = f"""
        请将这个 Hacker News 科技新闻标题翻译成中文，并用一句话（30字以内）解释它的核心看点或痛点。
        标题: "{title}"
        """
        
        # 3. 构造 Payload (数据包)
        payload = {
            "contents": [{
                "parts": [{"text": prompt_text}]
            }]
        }
        
        # 4. 发送 POST 请求
        headers = {'Content-Type': 'application/json'}
        response = requests.post(target_url, headers=headers, data=json.dumps(payload), timeout=10)
        
        # 5. 解析结果
        if response.status_code == 200:
            result = response.json()
            # 提取文本内容
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text.strip()
        else:
            print(f"⚠️ API 响应错误: {response.status_code} - {response.text}")
            return "AI 接口响应异常，请直接看原文。"
            
    except Exception as e:
        print(f"⚠️ 网络请求失败: {e}")
        return "AI 分析暂时不可用。"

def fetch_hn_data():
    print("🚀 正在连接 Hacker News (HTTP 直连模式)...")
    try:
        # 获取前 8 个热帖
        resp = requests.get(TOP_STORIES_URL, timeout=10)
        top_ids = resp.json()[:8]
        
        products = []
        for i, item_id in enumerate(top_ids):
            item_resp = requests.get(ITEM_URL.format(item_id), timeout=5)
            item = item_resp.json()
            
            # 清洗数据
            raw_title = item.get('title', 'No Title')
            clean_title = raw_title.replace("'", "\\'") 
            score = item.get('score', 0)
            
            print(f"[{i+1}/8] 分析中: {raw_title[:30]}...")
            
            # --- 调用 AI ---
            ai_reason = get_ai_insight(raw_title)
            # 清洗 AI 返回的特殊字符
            ai_reason = ai_reason.replace("'", "").replace("\n", "").replace('"', '')

            # 简单的 Emoji 映射
            emoji = "📰"
            lower = raw_title.lower()
            if "show hn" in lower: emoji = "🚀"
            elif "ai" in lower or "llm" in lower: emoji = "🤖"
            elif "ask hn" in lower: emoji = "💬"

            products.append({
                "id": item_id,
                "platform": "HackerNews",
                "title": clean_title,
                "price": "Free",
                "sales": f"{score} 🔥",
                "score": score, 
                "emoji": emoji,
                "aiReason": ai_reason
            })
            time.sleep(1) # 稍微慢一点，稳定第一
            
        print(f"✅ 成功获取 {len(products)} 条数据")
        return products
        
    except Exception as e:
        print(f"❌ 流程失败: {e}")
        return []

def update_html(new_data):
    if not new_data: return

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

        pattern = r"(// DATA_START\n)(.*?)(// DATA_END)"
        if not re.search(pattern, content, re.DOTALL):
            print("❌ 找不到锚点")
            return

        new_content = re.sub(pattern, f"\\1{js_data_str}                \\3", content, flags=re.DOTALL)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("🎉 更新完成！")
        
    except Exception as e:
        print(f"❌ 写入错误: {e}")

if __name__ == "__main__":
    data = fetch_hn_data()
    update_html(data)
