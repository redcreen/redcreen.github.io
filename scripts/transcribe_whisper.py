#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转文字 - OpenAI Whisper API
最稳定可靠的云端方案
"""
import sys
import os
import requests
import tempfile
import subprocess
from pathlib import Path

def convert_audio(input_path, output_format="mp3"):
    """使用 ffmpeg 转换音频格式"""
    with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp:
        output_path = tmp.name
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', input_path, '-ar', '16000', '-ac', '1', '-y', output_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return output_path
    except Exception as e:
        print(f"ffmpeg 转换失败: {e}")
    
    return input_path

def transcribe_openai(audio_path, api_key=None):
    """使用 OpenAI Whisper API 转录"""
    
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        return {
            "success": False, 
            "error": "未设置 OPENAI_API_KEY",
            "hint": "请访问 https://platform.openai.com/api-keys 获取 API Key"
        }
    
    url = "https://api.openai.com/v1/audio/transcriptions"
    
    # 转换格式（OpenAI 支持 mp3, mp4, mpeg, mpga, m4a, wav, webm）
    converted_path = convert_audio(audio_path, "mp3")
    
    try:
        with open(converted_path, "rb") as f:
            files = {"file": f}
            data = {"model": "whisper-1", "language": "zh", "response_format": "text"}
            headers = {"Authorization": f"Bearer {api_key}"}
            
            print("正在上传并转录...")
            response = requests.post(url, headers=headers, files=files, data=data, timeout=120)
        
        if response.status_code == 200:
            return {"success": True, "text": response.text}
        else:
            return {
                "success": False,
                "error": f"API 错误: {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        return {"success": False, "error": f"请求异常: {str(e)}"}
    finally:
        # 清理临时文件
        if converted_path != audio_path and os.path.exists(converted_path):
            try:
                os.unlink(converted_path)
            except:
                pass

def main():
    if len(sys.argv) < 2:
        print("用法: py transcribe_whisper.py <音频文件路径>")
        print("")
        print("环境变量:")
        print("  OPENAI_API_KEY - OpenAI API Key")
        print("")
        print("获取 API Key:")
        print("  https://platform.openai.com/api-keys")
        print("")
        print("示例:")
        print("  py transcribe_whisper.py voice.ogg")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        sys.exit(1)
    
    # 获取 API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("[!] 未设置 OPENAI_API_KEY 环境变量")
        print("")
        print("请设置环境变量:")
        print("  $env:OPENAI_API_KEY='sk-...'")
        print("")
        print("或者获取新的 API Key:")
        print("  https://platform.openai.com/api-keys")
        sys.exit(1)
    
    print(f"[音频] {audio_path}")
    print("-" * 50)
    
    result = transcribe_openai(audio_path, api_key)
    
    if result.get("success"):
        print("\n[成功] 转录完成！")
        print("=" * 50)
        print(result["text"])
        print("=" * 50)
    else:
        print(f"\n[错误] {result.get('error', '未知错误')}")
        if "hint" in result:
            print(f"提示: {result['hint']}")
        if "details" in result:
            print(f"详情: {result['details'][:500]}")

if __name__ == "__main__":
    main()
