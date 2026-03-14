#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 DashScope Paraformer 进行语音转文字
这是阿里云提供的语音识别服务
"""
import sys
import os
import json
import requests
import subprocess
import tempfile
from pathlib import Path

def convert_to_wav(input_path, output_path):
    """使用 ffmpeg 将音频转换为 WAV 格式"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', input_path, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', '-y', output_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"转换失败: {e}")
        return False

def transcribe_with_paraformer(audio_path, api_key=None):
    """使用 Paraformer 进行语音识别"""
    
    if not api_key:
        api_key = os.environ.get("DASHSCOPE_API_KEY")
    
    if not api_key:
        return {"error": "请设置 DASHSCOPE_API_KEY 环境变量"}
    
    # 读取音频文件
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    
    file_size = len(audio_bytes)
    print(f"音频文件大小: {file_size / 1024:.1f} KB")
    
    # DashScope 语音识别接口
    url = "https://dashscope.aliyuncs.com/api/v1/services/audio/asr/transcription"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 先上传文件
    upload_url = "https://dashscope.aliyuncs.com/api/v1/files"
    
    files = {
        'file': (os.path.basename(audio_path), audio_bytes, 'audio/wav')
    }
    
    try:
        print("正在上传音频文件...")
        upload_response = requests.post(upload_url, headers={"Authorization": f"Bearer {api_key}"}, files=files, timeout=60)
        
        if upload_response.status_code != 200:
            return {
                "error": f"文件上传失败: {upload_response.status_code}",
                "details": upload_response.text
            }
        
        upload_result = upload_response.json()
        print(f"上传结果: {json.dumps(upload_result, indent=2, ensure_ascii=False)[:500]}")
        
        # 解析 file_id
        file_id = None
        if "data" in upload_result and "uploaded_files" in upload_result["data"]:
            uploaded_files = upload_result["data"]["uploaded_files"]
            if len(uploaded_files) > 0:
                file_id = uploaded_files[0].get("file_id")
        
        if not file_id:
            return {"error": "无法获取 file_id", "details": upload_result}
        
        print(f"文件 ID: {file_id}")
        
        # 创建转录任务
        job_data = {
            "model": "paraformer-v2",
            "input": {
                "file_urls": [file_id]
            },
            "parameters": {
                "language_hint": "zh"
            }
        }
        
        print("正在创建转录任务...")
        job_response = requests.post(url, headers=headers, json=job_data, timeout=60)
        
        if job_response.status_code != 200:
            return {
                "error": f"创建任务失败: {job_response.status_code}",
                "details": job_response.text
            }
        
        job_result = job_response.json()
        print(f"任务创建结果: {json.dumps(job_result, indent=2, ensure_ascii=False)[:500]}")
        
        # 获取任务 ID
        task_id = None
        if "output" in job_result and "task_id" in job_result["output"]:
            task_id = job_result["output"]["task_id"]
        elif "id" in job_result:
            task_id = job_result["id"]
        
        if not task_id:
            return {"error": "无法获取任务 ID", "details": job_result}
        
        print(f"任务 ID: {task_id}")
        print("等待转录完成...")
        
        # 轮询任务状态
        import time
        for i in range(30):  # 最多等待 30 次，每次 2 秒
            time.sleep(2)
            
            status_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            status_response = requests.get(status_url, headers={"Authorization": f"Bearer {api_key}"}, timeout=30)
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                status = status_result.get("output", {}).get("task_status", "UNKNOWN")
                print(f"  状态: {status}")
                
                if status == "SUCCEEDED":
                    # 获取结果
                    results = status_result.get("output", {}).get("results", [])
                    if results and len(results) > 0:
                        text = results[0].get("transcription", {}).get("text", "")
                        return {"success": True, "text": text}
                    else:
                        return {"success": False, "error": "转录结果为空"}
                elif status in ["FAILED", "ERROR"]:
                    return {"success": False, "error": "转录失败", "details": status_result}
            else:
                print(f"  查询状态失败: {status_response.status_code}")
        
        return {"success": False, "error": "等待超时，请稍后查询任务状态", "task_id": task_id}
        
    except Exception as e:
        import traceback
        return {"success": False, "error": f"请求异常: {str(e)}", "details": traceback.format_exc()}

def main():
    if len(sys.argv) < 2:
        print("用法: py transcribe_paraformer.py <音频文件路径>")
        print("示例: py transcribe_paraformer.py voice.ogg")
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
    
    result = transcribe_with_paraformer(audio_path, api_key)
    
    if result.get("success"):
        print("\n[成功] 转录完成！")
        print("=" * 50)
        print(result["text"])
        print("=" * 50)
    else:
        print(f"\n[错误] {result.get('error', '未知错误')}")
        if "details" in result:
            print(f"详情: {result['details'][:500]}")
        if "task_id" in result:
            print(f"\n任务 ID: {result['task_id']}")
            print(f"可以稍后查询: https://dashscope.aliyuncs.com")

if __name__ == "__main__":
    main()
