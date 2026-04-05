import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
api_url = "https://api.deepseek.com/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 测试 R1 模型
payload = {
    "model": "deepseek-reasoner",
    "messages": [
        {"role": "user", "content": "什么是人工智能？"}
    ],
    "temperature": 0.7,
    "max_tokens": 2000,
    "stream": True
}

print("测试 DeepSeek R1 模型...")
print(f"API URL: {api_url}")
print(f"模型: {payload['model']}")
print("-" * 50)

try:
    with httpx.Client() as client:
        with client.stream("POST", api_url, headers=headers, json=payload, timeout=60.0) as response:
            response.raise_for_status()
            
            has_reasoning = False
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        print(f"收到数据: {json.dumps(chunk, indent=2, ensure_ascii=False)[:500]}")
                        
                        delta = chunk["choices"][0].get("delta", {})
                        if "reasoning_content" in delta:
                            has_reasoning = True
                            print(f"\n✓ 发现 reasoning_content: {delta['reasoning_content'][:100]}...")
                        if "content" in delta:
                            print(f"\n✓ 发现 content: {delta['content'][:100]}...")
                    except Exception as e:
                        print(f"解析错误: {e}")
            
            if not has_reasoning:
                print("\n✗ 未收到 reasoning_content")
                print("可能原因：")
                print("1. API 密钥没有 R1 模型访问权限")
                print("2. 需要使用不同的 API 端点")
                print("3. R1 模型返回格式不同")
                
except Exception as e:
    print(f"请求失败: {e}")