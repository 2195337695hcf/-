import requests
# API 配置（硅基流动平台）
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = "sk-tbpcgoxjnuewumfnqkjcmfvjbdyqgzyspcmlzocfotzabnqs" # 请替换为你在硅基流动控制台创建的 Key（sk- 开头）
# 构造请求
headers = {
"Authorization": f"Bearer {API_KEY}",
"Content-Type": "application/json"
}
data = {
"model": "meituan-longcat/LongCat-2.0",
"messages": [
{"role": "user", "content": "请用三句话介绍郑州航空工业管理学院"}
]
}
# 发送请求
response = requests.post(API_URL, headers=headers, json=data)
# 解析结果
result = response.json()
answer = result["choices"][0]["message"]["content"]
print(answer)
usage=result["usage"]
print(f"\n===== Token消耗统计 =====")
print(f"输入Token(prompt)：{usage['prompt_tokens']}")
print(f"输出Token(completion)：{usage['completion_tokens']}")
print(f"本次总Token：{usage['total_tokens']}")