"""
视频生成与合成模块
使用 FFmpeg 进行音视频处理
"""
import os
import subprocess
import shutil

# 输出目录
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def check_ffmpeg() -> bool:
    """检查 FFmpeg 是否可用"""
    return shutil.which("ffmpeg") is not None


def get_media_duration(file_path: str) -> float:
    """获取媒体文件时长（秒）"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 0.0


def merge_video_audio(video_path: str, audio_path: str, loop_video: bool = True, output_name: str = "final_output.mp4") -> str | None:
    """
    将视频和音频合并（替换原视频音轨）
    
    Args:
        video_path: 视频文件路径
        audio_path: 音频文件路径
        loop_video: True=循环视频匹配音频长度, False=截断音频到视频长度
        output_name: 输出文件名
    
    Returns:
        输出视频路径，失败返回 None
    """
    if not video_path or not os.path.exists(video_path):
        print(f"[Video Error] 视频文件不存在: {video_path}")
        return None
    
    if not audio_path or not os.path.exists(audio_path):
        print(f"[Video Error] 音频文件不存在: {audio_path}")
        return None
    
    if not check_ffmpeg():
        print("[Video Error] FFmpeg 未安装或不在 PATH 中")
        return None
    
    # 确保输出目录存在
    os.makedirs(ASSETS_DIR, exist_ok=True)
    output_path = os.path.join(ASSETS_DIR, output_name)
    
    if loop_video:
        # 获取音频时长
        audio_duration = get_media_duration(audio_path)
        
        # 循环视频直到匹配音频长度
        # -stream_loop -1 无限循环视频
        # -t 限制输出时长为音频长度
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",  # 无限循环视频
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "libx264",  # 需要重编码因为循环
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-t", str(audio_duration),  # 限制为音频时长
            output_path
        ]
    else:
        # 截断模式：以视频时长为准
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            return output_path
        else:
            print(f"[FFmpeg Error] {result.stderr}")
            return None
    except Exception as e:
        print(f"[Video Error] {e}")
        return None


def merge_video_audio_stream(video_path: str, audio_path: str, loop_video: bool = True):
    """
    流式合并视频和音频（带进度反馈）
    
    Args:
        video_path: 视频路径
        audio_path: 音频路径
        loop_video: True=循环视频匹配音频, False=截断音频匹配视频
    
    Yields:
        (progress_msg, output_path)
    """
    yield "🎬 检查输入文件...", None
    
    if not video_path or not os.path.exists(video_path):
        yield f"❌ 视频文件不存在: {video_path}", None
        return
    
    if not audio_path or not os.path.exists(audio_path):
        yield f"❌ 音频文件不存在: {audio_path}", None
        return
    
    yield "🔍 检查 FFmpeg...", None
    
    if not check_ffmpeg():
        yield "❌ FFmpeg 未安装！请先安装 FFmpeg 并添加到系统 PATH", None
        return
    
    yield "✅ FFmpeg 已就绪", None
    
    # 获取时长信息
    video_duration = get_media_duration(video_path)
    audio_duration = get_media_duration(audio_path)
    yield f"📊 视频时长: {video_duration:.1f}s | 音频时长: {audio_duration:.1f}s", None
    
    # 准备输出
    os.makedirs(ASSETS_DIR, exist_ok=True)
    output_path = os.path.join(ASSETS_DIR, "final_output.mp4")
    
    if loop_video and audio_duration > video_duration:
        yield f"🔄 模式: 循环视频 (输出时长 ≈ {audio_duration:.1f}s)", None
        yield "⏳ 正在循环视频并合成，可能需要一些时间...", None
        
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-t", str(audio_duration),
            output_path
        ]
    else:
        mode_desc = "截断音频" if audio_duration > video_duration else "正常合成"
        yield f"✂️ 模式: {mode_desc} (输出时长 ≈ {min(video_duration, audio_duration):.1f}s)", None
        yield "⏳ 正在合成视频...", None
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            output_duration = get_media_duration(output_path)
            yield f"✅ 合成成功！时长: {output_duration:.1f}s | 大小: {size_mb:.1f} MB", output_path
        else:
            error_msg = result.stderr[-500:] if result.stderr else "未知错误"
            yield f"❌ FFmpeg 错误: {error_msg}", None
    except Exception as e:
        yield f"❌ 执行异常: {e}", None


def add_background_music(video_path: str, music_path: str, music_volume: float = 0.3) -> str | None:
    """
    为视频添加背景音乐（混合原音轨）
    
    Args:
        video_path: 视频文件路径
        music_path: 背景音乐路径
        music_volume: 背景音乐音量 (0.0-1.0)
    
    Returns:
        输出视频路径
    """
    if not check_ffmpeg():
        return None
    
    os.makedirs(ASSETS_DIR, exist_ok=True)
    output_path = os.path.join(ASSETS_DIR, "video_with_bgm.mp4")
    
    # 使用 amix 滤镜混合音频
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", music_path,
        "-filter_complex", f"[1:a]volume={music_volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac",
        output_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            return output_path
    except Exception:
        pass
    return None
