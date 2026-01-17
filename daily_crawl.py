import json
import requests
import re
import time
import os
import google.generativeai as genai

# --- 配置区 ---
# Hacker News API
TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# 初始化 Gemini
# 从环境变量获取 Key (由 GitHub Actions 注入)
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    # 使用免费且快速的 Flash 模型
    model = genai.GenerativeModel('gemini-pro')
else:
    print("⚠️ 警告: 未找到 GEMINI_API_KEY，将使用默认文案。")
    model = None

def get_ai_insight(title):
    """调用 Gemini 生成中文短评"""
    if not model:
        return f"Hacker News 热榜话题：{title}"
    
    try:
        # Prompt 设计：要求简短、犀利、中文
        prompt = f"""
        你是一个科技趋势分析师。
        请将这个 Hacker News 的标题翻译成中文，并用一句话解释它为什么值得关注（或者它解决了什么痛点）。
        标题: "{title}"
        要求: 
        1. 中文回答。
        2. 语气专业且略带极客感。
        3. 不要超过 30 个字。
        4. 不要包含“这个标题”、“这篇文章”等废话，直接说重点。
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ AI 分析失败: {e}")
        return "AI 暂时掉线，建议直接阅读原文。"

def fetch_hn_data():
    print("🚀 正在连接 Hacker News 并召唤 Gemini...")
    try:
        # 1. 获取前 8 个热帖 (AI 需要时间，先跑 8 个试试)
        resp = requests.get(TOP_STORIES_URL, timeout=10)
        top_ids = resp.json()[:8]
        
        products = []
        for i, item_id in enumerate(top_ids):
            item_resp = requests.get(ITEM_URL.format(item_id), timeout=5)
            item = item_resp.json()
            
            # 基础数据清洗
            raw_title = item.get('title', 'No Title')
            clean_title = raw_title.replace("'", "\\'") 
            score = item.get('score', 0)
            
            print(f"[{i+1}/8] 正在分析: {raw_title[:30]}...")
            
            # --- 核心：调用 AI 生成洞察 ---
            ai_reason = get_ai_insight(raw_title)
            # 处理一下 AI 返回内容里可能的单引号，防止 JS 报错
            ai_reason = ai_reason.replace("'", "").replace("\n", "")

            # 根据标题关键词选 Emoji
            emoji = "📰"
            lower_title = raw_title.lower()
            if "show hn" in lower_title: emoji = "🚀"
            elif "ai" in lower_title or "gpt" in lower_title or "llm" in lower_title: emoji = "🤖"
            elif "google" in lower_title or "apple" in lower_title: emoji = "🍎"
            elif "linux" in lower_title or "code" in lower_title: emoji = "🐧"

            products.append({
                "id": item_id,
                "platform": "HackerNews",
                "title": clean_title, # 保留英文原标题
                "price": "Free",
                "sales": f"{score} 🔥",
                "score": score, 
                "emoji": emoji,
                "aiReason": ai_reason # 这里是 AI 生成的中文！
            })
            
            # 礼貌等待，防止触发 API 速率限制
            time.sleep(1)
            
        print(f"✅ 成功生成 {len(products)} 条 AI 智能简报")
        return products
        
    except Exception as e:
        print(f"❌ 流程失败: {e}")
        return []

def update_html(new_data):
    if not new_data:
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

        pattern = r"(// DATA_START\n)(.*?)(// DATA_END)"
        if not re.search(pattern, content, re.DOTALL):
            print("❌ 找不到锚点，请检查 index.html")
            return

        new_content = re.sub(pattern, f"\\1{js_data_str}                \\3", content, flags=re.DOTALL)
        
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(new_content)
        print("🎉 index.html 更新完成！")
        
    except Exception as e:
        print(f"❌ 文件写入错误: {e}")

if __name__ == "__main__":
    data = fetch_hn_data()
    update_html(data)

