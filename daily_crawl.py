import json
import requests
import re
import time
import os

# --- 配置区 ---
HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# Google AI Studio 基础 URL
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def get_available_model(api_key):
    """
    动态获取当前 API Key 可用的模型列表，不再瞎猜名字
    """
    url = f"{BASE_URL}/models?key={api_key}"
    try:
        print("🔍 正在查询可用模型列表...")
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ 无法获取模型列表: {resp.text}")
            return None
            
        data = resp.json()
        # 遍历所有模型，寻找支持 generateContent 的模型
        for model in data.get('models', []):
            methods = model.get('supportedGenerationMethods', [])
            name = model.get('name') # 例如 models/gemini-1.5-flash
            
            # 优先找 flash 或 pro，且必须支持生成内容
            if 'generateContent' in methods:
                if 'flash' in name or 'pro' in name:
                    print(f"✅ 锁定模型: {name}")
                    return name
        
        # 如果没找到理想的，就随便返回第一个支持生成的
        for model in data.get('models', []):
            if 'generateContent' in model.get('supportedGenerationMethods', []):
                print(f"⚠️ 降级使用模型: {model.get('name')}")
                return model.get('name')
                
        return None
    except Exception as e:
        print(f"❌ 模型发现失败: {e}")
        return None

def get_ai_insight(title, model_name, api_key):
    """发送 HTTP 请求调用 Gemini"""
    if not model_name or not api_key:
        return f"Hacker News 热榜话题：{title}"
    
    try:
        # 构造动态 URL
        target_url = f"{BASE_URL}/{model_name}:generateContent?key={api_key}"
        
        prompt_text = f"""
        Translate this Hacker News title to Chinese and explain the key point in 1 sentence (max 30 words).
        Title: "{title}"
        """
        
        payload = { "contents": [{ "parts": [{"text": prompt_text}] }] }
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(target_url, headers=headers, data=json.dumps(payload), timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            # 兼容不同的返回结构
            try:
                text = result['candidates'][0]['content']['parts'][0]['text']
                return text.strip()
            except:
                return "AI 解析结果格式异常"
        else:
            print(f"⚠️ API {response.status_code}: {response.text[:100]}...")
            return "AI 接口响应异常"
            
    except Exception as e:
        print(f"⚠️ 请求失败: {e}")
        return "AI 分析暂时不可用"

def fetch_hn_data():
    print("🚀 启动趋势猎人...")
    
    # 1. 准备 API Key 和模型
    api_key = os.environ.get("GEMINI_API_KEY")
    current_model = None
    
    if api_key:
        current_model = get_available_model(api_key)
    else:
        print("⚠️ 未找到 GEMINI_API_KEY，将跳过 AI 分析")

    try:
        # 2. 获取 Hacker News 数据
        print("📡 获取 HN 热榜 ID...")
        resp = requests.get(HN_TOP_URL, timeout=10)
        top_ids = resp.json()[:8] # 取前8个
        
        products = []
        for i, item_id in enumerate(top_ids):
            item_resp = requests.get(HN_ITEM_URL.format(item_id), timeout=5)
            item = item_resp.json()
            
            raw_title = item.get('title', 'No Title')
            clean_title = raw_title.replace("'", "\\'") 
            score = item.get('score', 0)
            
            print(f"[{i+1}/8] 处理: {raw_title[:20]}...")
            
            # --- 调用 AI (如果模型可用) ---
            if current_model:
                ai_reason = get_ai_insight(raw_title, current_model, api_key)
                ai_reason = ai_reason.replace("'", "").replace("\n", "").replace('"', '')
            else:
                ai_reason = f"Hacker News 热度: {score}"

            # Emoji 逻辑
            emoji = "📰"
            lower = raw_title.lower()
            if "show hn" in lower: emoji = "🚀"
            elif "ai" in lower or "llm" in lower: emoji = "🤖"
            elif "release" in lower: emoji = "🔥"

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
            time.sleep(1) 
            
        print(f"✅ 完成！获取 {len(products)} 条数据")
        return products
        
    except Exception as e:
        print(f"❌ 流程失败: {e}")
        return []

def update_html(new_data):
    if not new_data: return
    print("📝 更新 HTML...")
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
        print("🎉 写入成功！")
        
    except Exception as e:
        print(f"❌ 写入错误: {e}")

if __name__ == "__main__":
    data = fetch_hn_data()
    update_html(data)
