import os

import requests


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("GEMINI_MODEL")
    if not api_key or not model:
        print("請先設定 GEMINI_API_KEY 與 GEMINI_MODEL。")
        return
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": "請只回覆 OK"}]}],
        },
        timeout=(2, 6),
    )
    print(response.status_code)
    print(response.text[:500])


if __name__ == "__main__":
    main()
