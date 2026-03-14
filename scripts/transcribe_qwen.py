#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用通义千问 API 进行语音转文字
通过 DashScope 平台
"""
import sys
import os
import base64
import requests
import json
from pathlib import Path

def get_api_key_from_openclaw():
    """尝试从 OpenClaw 配置中获取 API Key"""
    try:
        # 读取 OpenClaw 配置文件
        config_path = os.path.expanduser("~/.openclaw/openclaw.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 检查是否有 qwen 配置
        if "auth" in config and "profiles" in config["auth"]:
            if "qwen" in config["auth"]["profiles"]:
                # API Key 可能在环境变量或 keychain 中
                pass
        
        return None
    except Exception as e:
        print(f"读取配置失败: {e}")
        return None

def transcribe_with_qwen_audio(audio_path, api_key=None):
    """使用通义千问音频模型进行语音转文字"""
    
    if not api_key:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
    
    if not api_key:
        return {"error": "请设置 DASHSCOPE_API_KEY 环境变量或在代码中传入 api_key"}
    
    # 读取音频文件
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    
    # 获取文件大小
    file_size = len(audio_bytes)
    print(f"音频文件大小: {file_size / 1024:.1f} KB")
    
    # DashScope 文件上传接口
    upload_url = "https://dashscope.aliyuncs.com/api/v1/files"
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    # 上传文件
    files = {
        'file': (os.path.basename(audio_path), audio_bytes, 'audio/ogg')
    }
    
    try:
        print("正在上传音频文件...")
        upload_response = requests.post(upload_url, headers=headers, files=files, timeout=60)
        
        if upload_response.status_code != 200:
            return {
                "error": f"文件上传失败: {upload_response.status_code}",
                "details": upload_response.text
            }
        
        upload_result = upload_response.json()
        print(f"上传结果: {upload_result}")
        
        # 解析响应获取 file_id
        file_id = None
        if "data" in upload_result and "uploaded_files" in upload_result["data"]:
            uploaded_files = upload_result["data"]["uploaded_files"]
            if len(uploaded_files) > 0 and "file_id" in uploaded_files[0]:
                file_id = uploaded_files[0]["file_id"]
        
        if not file_id:
            return {
                "error": "上传成功但未获取到 file_id",
                "details": upload_result
            }
        print(f"文件 ID: {file_id}")
        
        # 使用文件进行语音识别
        chat_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        
        data = {
            "model": "qwen-audio-turbo",
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": [{"text": "You are a helpful assistant."}]
                    },
                    {
                        "role": "user",
                        "content": [
                            {"file": file_id},
                            {"text": "请将这段语音转录为文字"}
                        ]
                    }
                ]
            }
        }
        
        print("正在进行语音识别...")
        chat_response = requests.post(chat_url, headers={**headers, "Content-Type": "application/json"}, 
                                       json=data, timeout=120)
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            if "output" in result and "choices" in result["output"]:
                content = result["output"]["choices"][0]["message"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    text = content[0].get("text", "")
                else:
                    text = str(content)
                return {"success": True, "text": text}
            else:
                return {"success": False, "error": "响应格式异常", "details": result}
        else:
            return {
                "success": False,
                "error": f"识别请求失败: {chat_response.status_code}",
                "details": chat_response.text
            }
            
    except Exception as e:
        return {"success": False, "error": f"请求异常: {str(e)}"}

def main():
    if len(sys.argv) < 2:
        print("用法: python transcribe_qwen.py <音频文件路径>")
        print("示例: python transcribe_qwen.py voice.ogg")
        print("\n环境变量:")
        print("  DASHSCOPE_API_KEY - 通义千问 API Key")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        sys.exit(1)
    
    # 检查 API key
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        print("[!] 未设置 DASHSCOPE_API_KEY 环境变量")
        print("请设置: $env:DASHSCOPE_API_KEY='your_api_key'")
        print("\n获取 API Key:")
        print("1. 访问 https://dashscope.aliyun.com")
        print("2. 注册/登录阿里云账号")
        print("3. 创建 API Key")
        sys.exit(1)
    
    print(f"[音频] 正在转录: {audio_path}")
    print("-" * 50)
    
    result = transcribe_with_qwen_audio(audio_path, api_key)
    
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
