#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转文字 - 使用 Kimi (Moonshot) API
通过文件上传 API 实现语音转录
"""
import sys
import os
import requests
import json

def transcribe_with_kimi_file(audio_path, api_key=None):
    """使用 Kimi 文件上传 + 多模态转录"""
    
    api_key = api_key or os.environ.get("MOONSHOT_API_KEY")
    
    if not api_key:
        # 尝试从 OpenClaw 配置读取
        try:
            config_path = os.path.expanduser("~/.openclaw/openclaw.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Moonshot API Key 通常存储在 keychain，这里尝试读取配置文件中的备用 key
        except:
            pass
        return {"success": False, "error": "未设置 MOONSHOT_API_KEY"}
    
    # Step 1: 上传文件到 Kimi
    upload_url = "https://api.moonshot.cn/v1/files"
    
    with open(audio_path, "rb") as f:
        files = {"file": f}
        data = {"purpose": "file-extract"}  # 用于文件内容提取
        headers = {"Authorization": f"Bearer {api_key}"}
        
        print("正在上传文件到 Kimi...")
        upload_resp = requests.post(upload_url, headers=headers, files=files, data=data, timeout=60)
    
    if upload_resp.status_code != 200:
        return {
            "success": False,
            "error": f"文件上传失败: {upload_resp.status_code}",
            "details": upload_resp.text
        }
    
    upload_result = upload_resp.json()
    file_id = upload_result.get("id")
    
    if not file_id:
        return {"success": False, "error": "无法获取文件 ID", "details": upload_result}
    
    print(f"文件上传成功，ID: {file_id}")
    
    # Step 2: 获取文件内容
    content_url = f"https://api.moonshot.cn/v1/files/{file_id}/content"
    content_resp = requests.get(content_url, headers=headers, timeout=30)
    
    if content_resp.status_code != 200:
        return {
            "success": False,
            "error": f"获取文件内容失败: {content_resp.status_code}",
            "details": content_resp.text
        }
    
    # Step 3: 使用多模态模型转录
    chat_url = "https://api.moonshot.cn/v1/chat/completions"
    
    chat_data = {
        "model": "kimi-k2.5",
        "messages": [
            {
                "role": "system",
                "content": "你是语音转录助手，请将用户提供的音频内容准确转录为文字。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "file",
                        "file_url": {
                            "url": f"https://api.moonshot.cn/v1/files/{file_id}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "请将这段语音转录为文字，只输出转录内容，不要添加任何解释。"
                    }
                ]
            }
        ]
    }
    
    print("正在进行语音识别...")
    chat_resp = requests.post(chat_url, headers={**headers, "Content-Type": "application/json"}, 
                              json=chat_data, timeout=120)
    
    if chat_resp.status_code == 200:
        result = chat_resp.json()
        if "choices" in result and len(result["choices"]) > 0:
            text = result["choices"][0]["message"]["content"]
            return {"success": True, "text": text}
        else:
            return {"success": False, "error": "响应格式异常", "details": result}
    else:
        return {
            "success": False,
            "error": f"转录请求失败: {chat_resp.status_code}",
            "details": chat_resp.text
        }

def main():
    if len(sys.argv) < 2:
        print("用法: py transcribe_kimi_file.py <音频文件路径>")
        print("\n环境变量:")
        print("  MOONSHOT_API_KEY - Kimi API Key")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        sys.exit(1)
    
    # 获取 API Key
    api_key = os.environ.get("MOONSHOT_API_KEY")
    
    if not api_key:
        print("[!] 未设置 MOONSHOT_API_KEY 环境变量")
        print("请设置: $env:MOONSHOT_API_KEY='your_api_key'")
        print("\n获取 API Key: https://platform.moonshot.cn")
        sys.exit(1)
    
    print(f"[音频] {audio_path}")
    print("-" * 50)
    
    result = transcribe_with_kimi_file(audio_path, api_key)
    
    if result.get("success"):
        print("\n[成功] 转录完成！")
        print("=" * 50)
        print(result["text"])
        print("=" * 50)
    else:
        print(f"\n[错误] {result.get('error', '未知错误')}")
        if "details" in result:
            print(f"详情: {result['details'][:500]}")

if __name__ == "__main__":
    main()
