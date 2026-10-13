import os

import requests
from dotenv import load_dotenv

# 从项目根目录的 .env 加载环境变量（.env 不入库，见 .gitignore）
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

API_KEY = os.getenv("ZHIPUAI_API_KEY")
if not API_KEY:
    raise RuntimeError("请先在项目根目录的 .env 文件中设置 ZHIPUAI_API_KEY（参考 .env.example）")
BASE_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def get_model_response(prompt, model="glm-4-flash", temperature=0.0):
    """向智谱大模型发送请求并返回回复内容"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }
    response = requests.post(BASE_URL, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": "你好"}],
        "temperature": 0.7,
    }
    response = requests.post(BASE_URL, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    result = response.json()

    choice = result["choices"][0]
    print("id:", result["id"])
    print("created:", result["created"])
    print("model:", result["model"])
    print("object:", result["object"])
    print("request_id:", result["request_id"])
    print("finish_reason:", choice["finish_reason"])
    print("index:", choice["index"])
    print("role:", choice["message"]["role"])
    print("content:", choice["message"]["content"])
    print("prompt_tokens:", result["usage"]["prompt_tokens"])
    print("completion_tokens:", result["usage"]["completion_tokens"])
    print("total_tokens:", result["usage"]["total_tokens"])
