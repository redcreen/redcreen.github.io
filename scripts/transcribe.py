#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转文字 - 多引擎支持
支持: OpenAI Whisper, 通义千问, 本地 Whisper
"""
import sys
import os
import json
import requests
import subprocess
import tempfile
from pathlib import Path

class AudioTranscriber:
    def __init__(self):
        self.engines = {
            "openai": self.transcribe_openai,
            "kimi": self.transcribe_kimi,
            "qwen": self.transcribe_qwen,
        }
    
    def convert_audio(self, input_path, output_format="mp3"):
        """转换音频格式"""
        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp:
            output_path = tmp.name
        
        try:
            # 尝试使用 ffmpeg
            result = subprocess.run(
                ['ffmpeg', '-i', input_path, '-ar', '16000', '-ac', '1', '-y', output_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                return output_path
        except:
            pass
        
        # 如果 ffmpeg 失败，直接返回原文件
        return input_path
    
    def transcribe_openai(self, audio_path, api_key=None):
        """使用 OpenAI Whisper API"""
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {"success": False, "error": "未设置 OPENAI_API_KEY"}
        
        url = "https://api.openai.com/v1/audio/transcriptions"
        
        with open(audio_path, "rb") as f:
            files = {"file": f}
            data = {"model": "whisper-1", "language": "zh"}
            headers = {"Authorization": f"Bearer {api_key}"}
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=120)
        
        if response.status_code == 200:
            return {"success": True, "text": response.json().get("text", "")}
        else:
            return {"success": False, "error": f"API 错误: {response.status_code}", "details": response.text}
    
    def transcribe_kimi(self, audio_path, api_key=None):
        """使用 Kimi API (Moonshot)"""
        api_key = api_key or os.environ.get("MOONSHOT_API_KEY")
        if not api_key:
            return {"success": False, "error": "未设置 MOONSHOT_API_KEY"}
        
        # Kimi 不直接支持音频，需要先用其他服务转录
        return {"success": False, "error": "Kimi 不支持直接音频转录"}
    
    def transcribe_qwen(self, audio_path, api_key=None):
        """使用通义千问 / DashScope"""
        api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            return {"success": False, "error": "未设置 DASHSCOPE_API_KEY"}
        
        # 读取音频文件
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        
        # 上传文件
        upload_url = "https://dashscope.aliyuncs.com/api/v1/files"
        files = {"file": (os.path.basename(audio_path), audio_bytes, "audio/ogg")}
        headers = {"Authorization": f"Bearer {api_key}"}
        
        upload_resp = requests.post(upload_url, headers=headers, files=files, timeout=60)
        if upload_resp.status_code != 200:
            return {"success": False, "error": f"上传失败: {upload_resp.status_code}"}
        
        upload_result = upload_resp.json()
        file_id = None
        if "data" in upload_result and "uploaded_files" in upload_result["data"]:
            files_list = upload_result["data"]["uploaded_files"]
            if files_list:
                file_id = files_list[0].get("file_id")
        
        if not file_id:
            return {"success": False, "error": "无法获取 file_id"}
        
        # 使用 qwen-audio-turbo 模型
        chat_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        data = {
            "model": "qwen-audio-turbo",
            "input": {
                "messages": [
                    {"role": "system", "content": [{"text": "You are a helpful assistant."}]},
                    {"role": "user", "content": [{"file": file_id}, {"text": "请将这段语音转录为文字"}]}
                ]
            }
        }
        
        resp = requests.post(chat_url, headers={**headers, "Content-Type": "application/json"}, 
                            json=data, timeout=120)
        
        if resp.status_code == 200:
            result = resp.json()
            if "output" in result and "choices" in result["output"]:
                content = result["output"]["choices"][0]["message"]["content"]
                if isinstance(content, list) and len(content) > 0:
                    text = content[0].get("text", "")
                else:
                    text = str(content)
                return {"success": True, "text": text}
        
        return {"success": False, "error": f"识别失败: {resp.status_code}", "details": resp.text}
    
    def transcribe(self, audio_path, engine="auto"):
        """自动选择引擎进行转录"""
        
        # 检查各引擎的 API Key 是否可用
        engines_to_try = []
        
        if os.environ.get("OPENAI_API_KEY"):
            engines_to_try.append("openai")
        if os.environ.get("DASHSCOPE_API_KEY"):
            engines_to_try.append("qwen")
        
        if not engines_to_try:
            return {
                "success": False, 
                "error": "没有可用的语音识别引擎",
                "hint": "请设置 OPENAI_API_KEY 或 DASHSCOPE_API_KEY 环境变量"
            }
        
        # 按优先级尝试
        for engine in engines_to_try:
            print(f"尝试使用 {engine} 引擎...")
            result = self.engines[engine](audio_path)
            if result.get("success"):
                result["engine"] = engine
                return result
            else:
                print(f"  {engine} 失败: {result.get('error')}")
        
        return {
            "success": False,
            "error": "所有引擎都失败了",
            "last_error": result.get("error")
        }

def main():
    if len(sys.argv) < 2:
        print("用法: py transcribe.py <音频文件路径> [引擎]")
        print("")
        print("引擎选项:")
        print("  auto   - 自动选择 (默认)")
        print("  openai - OpenAI Whisper")
        print("  qwen   - 通义千问")
        print("")
        print("环境变量:")
        print("  OPENAI_API_KEY    - OpenAI API Key")
        print("  DASHSCOPE_API_KEY - DashScope API Key")
        print("")
        print("示例:")
        print("  py transcribe.py voice.ogg")
        print("  py transcribe.py voice.ogg openai")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    engine = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        sys.exit(1)
    
    print(f"[音频] {audio_path}")
    print(f"[引擎] {engine}")
    print("-" * 50)
    
    transcriber = AudioTranscriber()
    
    if engine == "auto":
        result = transcriber.transcribe(audio_path)
    else:
        if engine not in transcriber.engines:
            print(f"错误: 未知引擎 '{engine}'")
            sys.exit(1)
        result = transcriber.engines[engine](audio_path)
        result["engine"] = engine
    
    if result.get("success"):
        print(f"\n[成功] 使用 {result.get('engine', 'unknown')} 引擎完成转录")
        print("=" * 50)
        print(result["text"])
        print("=" * 50)
    else:
        print(f"\n[错误] {result.get('error', '未知错误')}")
        if "hint" in result:
            print(f"提示: {result['hint']}")
        if "details" in result:
            print(f"详情: {result['details'][:200]}")

if __name__ == "__main__":
    main()
