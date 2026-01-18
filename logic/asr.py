# -*- coding: utf-8 -*-
"""
Whisper ASR 模块 - 从视频中提取口播文案
"""
import os
import tempfile
import subprocess
import requests


def download_video(url: str, save_path: str) -> bool:
    """
    下载视频文件
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.douyin.com/",
    }
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"[ASR] 视频下载失败: {e}")
        return False


def extract_audio(video_path: str, audio_path: str) -> bool:
    """
    使用 ffmpeg 从视频中提取音频
    """
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",  # 不要视频
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", "16000",  # 16kHz 采样率 (Whisper 推荐)
            "-ac", "1",  # 单声道
            audio_path
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120
        )
        return result.returncode == 0 and os.path.exists(audio_path)
    except Exception as e:
        print(f"[ASR] 音频提取失败: {e}")
        return False


def transcribe_audio(audio_path: str, model_name: str = "base") -> str:
    """
    使用 Whisper 将音频转为文字
    
    Args:
        audio_path: 音频文件路径
        model_name: Whisper 模型 (tiny/base/small/medium/large)
    
    Returns:
        转录的文字
    """
    try:
        import whisper
        import torch
        
        # 自动选择设备
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[ASR] 使用设备: {device}")
        
        # 加载模型
        print(f"[ASR] 加载 Whisper {model_name} 模型...")
        model = whisper.load_model(model_name, device=device)
        
        # 转录
        print(f"[ASR] 开始转录...")
        result = model.transcribe(
            audio_path,
            language="zh",  # 指定中文
            verbose=False
        )
        
        return result.get("text", "").strip()
    
    except ImportError:
        return "❌ 错误: 未安装 openai-whisper，请运行: pip install openai-whisper"
    except Exception as e:
        return f"❌ 转录失败: {e}"


def extract_speech_text(video_url: str, model_name: str = "base") -> str:
    """
    完整流程：从视频 URL 提取口播文案
    
    Args:
        video_url: 视频下载链接
        model_name: Whisper 模型名称
    
    Returns:
        口播文案文字
    """
    if not video_url:
        return "❌ 错误: 视频 URL 为空"
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="asr_")
    video_path = os.path.join(temp_dir, "video.mp4")
    audio_path = os.path.join(temp_dir, "audio.wav")
    
    try:
        # 1. 下载视频
        print(f"[ASR] 正在下载视频...")
        if not download_video(video_url, video_path):
            return "❌ 视频下载失败，请检查链接是否有效"
        
        # 2. 提取音频
        print(f"[ASR] 正在提取音频...")
        if not extract_audio(video_path, audio_path):
            return "❌ 音频提取失败，请确保已安装 ffmpeg"
        
        # 3. Whisper 转录
        text = transcribe_audio(audio_path, model_name)
        
        return text
    
    finally:
        # 4. 清理临时文件
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            os.rmdir(temp_dir)
        except Exception:
            pass


# 生成器版本，用于流式输出进度
def extract_speech_text_stream(video_url: str, model_name: str = "base"):
    """
    流式版本：边处理边输出进度
    
    Yields:
        (progress_text, final_result)
    """
    if not video_url:
        yield ("❌ 错误: 视频 URL 为空", None)
        return
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="asr_")
    video_path = os.path.join(temp_dir, "video.mp4")
    audio_path = os.path.join(temp_dir, "audio.wav")
    
    try:
        # 1. 下载视频
        yield ("📥 正在下载视频...", None)
        if not download_video(video_url, video_path):
            yield ("❌ 视频下载失败，请检查链接是否有效", None)
            return
        
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
        yield (f"✅ 视频下载完成 ({file_size:.1f} MB)", None)
        
        # 2. 提取音频
        yield ("🎵 正在提取音频...", None)
        if not extract_audio(video_path, audio_path):
            yield ("❌ 音频提取失败，请确保已安装 ffmpeg", None)
            return
        yield ("✅ 音频提取完成", None)
        
        # 3. Whisper 转录
        yield ("🎤 Whisper 正在识别语音... (首次运行需下载模型，请耐心等待)", None)
        text = transcribe_audio(audio_path, model_name)
        
        if text.startswith("❌"):
            yield (text, None)
        else:
            yield ("✅ 语音识别完成！", text)
    
    finally:
        # 4. 清理临时文件
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
            if os.path.exists(audio_path):
                os.remove(audio_path)
            os.rmdir(temp_dir)
        except Exception:
            pass
