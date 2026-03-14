#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音转文字 - 本地 Whisper 方案
自动安装和运行 faster-whisper
"""
import sys
import os
import subprocess
import tempfile
from pathlib import Path

def check_ffmpeg():
    """检查是否安装了 ffmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def install_faster_whisper():
    """安装 faster-whisper"""
    print("正在安装 faster-whisper...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'faster-whisper'], 
                      check=True, timeout=120)
        return True
    except Exception as e:
        print(f"安装失败: {e}")
        return False

def convert_to_wav(input_path):
    """转换为 WAV 格式"""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        output_path = tmp.name
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-i', input_path, '-ar', '16000', '-ac', '1', '-c:a', 'pcm_s16le', '-y', output_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return output_path
    except Exception as e:
        print(f"转换失败: {e}")
    
    return None

def transcribe_local(audio_path, model_size="base"):
    """使用本地 faster-whisper 转录"""
    
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("faster-whisper 未安装，尝试自动安装...")
        if not install_faster_whisper():
            return {"success": False, "error": "无法安装 faster-whisper"}
        from faster_whisper import WhisperModel
    
    # 检查 ffmpeg
    if not check_ffmpeg():
        return {
            "success": False, 
            "error": "未安装 ffmpeg",
            "hint": "请安装 ffmpeg: https://ffmpeg.org/download.html"
        }
    
    # 转换音频格式
    print("正在转换音频格式...")
    wav_path = convert_to_wav(audio_path)
    if not wav_path:
        return {"success": False, "error": "音频格式转换失败"}
    
    try:
        print(f"正在加载模型 {model_size}...")
        # 使用 CPU 运行，模型会自动下载
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        
        print("正在转录...")
        segments, info = model.transcribe(wav_path, beam_size=5, language="zh")
        
        print(f"检测到语言: {info.language}, 概率: {info.language_probability:.2f}")
        
        # 合并所有片段
        texts = []
        for segment in segments:
            texts.append(segment.text)
        
        full_text = " ".join(texts).strip()
        
        return {"success": True, "text": full_text}
        
    except Exception as e:
        return {"success": False, "error": f"转录失败: {str(e)}"}
    finally:
        # 清理临时文件
        try:
            if wav_path and os.path.exists(wav_path):
                os.unlink(wav_path)
        except:
            pass

def main():
    if len(sys.argv) < 2:
        print("用法: py transcribe_local.py <音频文件路径> [模型大小]")
        print("")
        print("模型大小:")
        print("  tiny   - 最快，准确率一般 (约 39MB)")
        print("  base   - 平衡速度和准确率 (约 74MB, 默认)")
        print("  small  - 较慢，准确率较高 (约 244MB)")
        print("  medium - 慢，准确率高 (约 769MB)")
        print("  large  - 最慢，准确率最高 (约 1.5GB)")
        print("")
        print("示例:")
        print("  py transcribe_local.py voice.ogg")
        print("  py transcribe_local.py voice.ogg small")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 {audio_path}")
        sys.exit(1)
    
    print(f"[音频] {audio_path}")
    print(f"[模型] {model_size}")
    print("-" * 50)
    
    result = transcribe_local(audio_path, model_size)
    
    if result.get("success"):
        print("\n[成功] 转录完成！")
        print("=" * 50)
        print(result["text"])
        print("=" * 50)
    else:
        print(f"\n[错误] {result.get('error', '未知错误')}")
        if "hint" in result:
            print(f"提示: {result['hint']}")

if __name__ == "__main__":
    main()
