#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 DashScope OpenAI 兼容接口进行语音转文字
直接上传 base64 编码的音频
"""
import sys
import os
import base64
import requests
import json

def transcribe_with_qwen_openai(audio_path, api_key=None):
    """使用通义千问 OpenAI 兼容接口进行语音转文字"""
    
    if not api_key:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
    
    if not api_key:
        return {"error": "请设置 DASHSCOPE_API_KEY 环境变量"}
    
    # 读取音频文件并转为 base64
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    file_size = len(audio_bytes)
    print(f"音频文件大小: {file_size / 1024:.1f} KB")
    
    # DashScope OpenAI 兼容接口
    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建请求 - 使用 qwen-audio-turbo 模型
    data = {
        "model": "qwen-audio-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that transcribes audio to text."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": f"data:audio/ogg;base64,{audio_base64}",
                            "format": "ogg"
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
    
    try:
        print("正在识别语音...")
        response = requests.post(url, headers=headers, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return {"success": True, "text": content}
            else:
                return {"success": False, "error": "响应格式异常", "details": result}
        else:
            return {
                "success": False,
                "error": f"请求失败: {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        return {"success": False, "error": f"请求异常: {str(e)}"}

def main():
    if len(sys.argv) < 2:
        print("用法: py transcribe_qwen_openai.py <音频文件路径>")
        print("示例: py transcribe_qwen_openai.py voice.ogg")
        print("\n环境变量:")
        print("  DASHSCOPE_API_KEY - 通义千问 API Key")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        sys.exit(1)
    
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("[!] 未设置 DASHSCOPE_API_KEY 环境变量")
        print("请设置: $env:DASHSCOPE_API_KEY='your_api_key'")
        sys.exit(1)
    
    print(f"[音频] 正在转录: {audio_path}")
    print("-" * 50)
    
    result = transcribe_with_qwen_openai(audio_path, api_key)
    
    if result.get("success"):
        print("\n[成功] 转录完成！")
        print("=" * 50)
        print(result["text"])
        print("=" * 50)
    else:
        print(f"\n[错误] {result.get('error', '未知错误')}")
        if "details" in result:
            print(f"详情: {result['details']}")

if __name__ == "__main__":
    main()
