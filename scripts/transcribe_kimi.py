#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Kimi (Moonshot) 多模态能力进行语音转文字
通过读取音频文件并以 base64 形式传给模型
"""
import sys
import os
import base64
import requests

def transcribe_with_kimi(audio_path, api_key=None):
    """使用 Kimi 多模态模型转录音频"""
    
    api_key = api_key or os.environ.get("MOONSHOT_API_KEY")
    if not api_key:
        # 尝试从配置文件读取
        try:
            import json
            config_path = os.path.expanduser("~/.openclaw/openclaw.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
            # 这里需要实现从 keychain 获取的逻辑
        except:
            pass
        return {"success": False, "error": "未设置 MOONSHOT_API_KEY"}
    
    # 读取音频文件
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    file_size = len(audio_bytes)
    print(f"音频文件大小: {file_size / 1024:.1f} KB")
    
    # Kimi API 接口
    url = "https://api.moonshot.cn/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 构建多模态请求
    data = {
        "model": "kimi-k2.5",
        "messages": [
            {
                "role": "system",
                "content": "你是音频转录助手，请将用户提供的音频内容转录为文字。"
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "file_url",
                        "file_url": {
                            "url": f"data:audio/ogg;base64,{audio_base64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "请将这段语音转录为文字，只输出转录内容。"
                    }
                ]
            }
        ]
    }
    
    try:
        print("正在请求 Kimi API...")
        response = requests.post(url, headers=headers, json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                text = result["choices"][0]["message"]["content"]
                return {"success": True, "text": text}
            else:
                return {"success": False, "error": "响应格式异常", "details": result}
        else:
            return {
                "success": False,
                "error": f"API 错误: {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        return {"success": False, "error": f"请求异常: {str(e)}"}

def main():
    if len(sys.argv) < 2:
        print("用法: py transcribe_kimi.py <音频文件路径>")
        print("\n环境变量:")
        print("  MOONSHOT_API_KEY - Kimi API Key")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        sys.exit(1)
    
    # 从环境变量或配置文件获取 API Key
    api_key = os.environ.get("MOONSHOT_API_KEY")
    
    if not api_key:
        print("[!] 未设置 MOONSHOT_API_KEY 环境变量")
        print("正在尝试从 OpenClaw 配置读取...")
        
        # 尝试读取 OpenClaw 配置
        try:
            import json
            config_path = os.path.expanduser("~/.openclaw/openclaw.json")
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # 检查 moonshot 配置
            if "auth" in config and "profiles" in config["auth"]:
                if "moonshot:default" in config["auth"]["profiles"]:
                    print("找到 moonshot 配置，但 API Key 存储在 keychain 中")
                    print("请设置环境变量: $env:MOONSHOT_API_KEY='your_api_key'")
        except Exception as e:
            print(f"读取配置失败: {e}")
        
        sys.exit(1)
    
    print(f"[音频] {audio_path}")
    print("-" * 50)
    
    result = transcribe_with_kimi(audio_path, api_key)
    
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
