"""
Edge-TTS 文字转语音模块
使用微软 Edge 的免费高质量 AI 语音
"""
import asyncio
import os
import sys
import edge_tts

# Windows 兼容：修复 asyncio 事件循环问题
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# 输出目录
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

# 常用中文语音
VOICE_MAP = {
    "晓晓 (女声-温柔)": "zh-CN-XiaoxiaoNeural",
    "晓伊 (女声-活泼)": "zh-CN-XiaoyiNeural",
    "云扬 (男声-新闻)": "zh-CN-YunyangNeural",
    "云希 (男声-旁白)": "zh-CN-YunxiNeural",
    "云健 (男声-运动)": "zh-CN-YunjianNeural",
}

# 默认语音
DEFAULT_VOICE = "zh-CN-XiaoxiaoNeural"


async def _generate_speech_async(text: str, voice: str, output_path: str) -> str:
    """异步生成语音"""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path


def text_to_speech(text: str, voice_name: str = "晓晓 (女声-温柔)") -> str | None:
    """
    将文本转换为语音文件
    
    Args:
        text: 要转换的文本内容
        voice_name: 语音名称（中文友好名称）
    
    Returns:
        生成的音频文件路径，失败返回 None
    """
    # 输入验证
    if not text or not text.strip():
        return None
    
    # 确保输出目录存在
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    # 映射语音 ID
    voice_id = VOICE_MAP.get(voice_name, DEFAULT_VOICE)
    
    # 输出文件路径
    output_path = os.path.join(ASSETS_DIR, "generated_audio.mp3")
    
    try:
        # 运行异步任务
        asyncio.run(_generate_speech_async(text.strip(), voice_id, output_path))
        return output_path
    except Exception as e:
        print(f"[TTS Error] {e}")
        return None


def text_to_speech_stream(text: str, voice_name: str = "晓晓 (女声-温柔)"):
    """
    流式生成语音（带进度反馈）
    
    Yields:
        (progress_msg, audio_path)
    """
    if not text or not text.strip():
        yield "❌ 文本内容为空，无法生成语音", None
        return
    
    yield "🎤 正在初始化 Edge-TTS...", None
    
    # 确保输出目录存在
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    # 映射语音 ID
    voice_id = VOICE_MAP.get(voice_name, DEFAULT_VOICE)
    output_path = os.path.join(ASSETS_DIR, "generated_audio.mp3")
    
    yield f"🔊 使用语音: {voice_name} ({voice_id})", None
    yield f"📝 文本长度: {len(text.strip())} 字符", None
    yield "⏳ 正在生成语音，请稍候...", None
    
    try:
        asyncio.run(_generate_speech_async(text.strip(), voice_id, output_path))
        yield "✅ 语音生成成功！", output_path
    except Exception as e:
        yield f"❌ 语音生成失败: {e}", None


def get_available_voices() -> list[str]:
    """获取可用的语音列表"""
    return list(VOICE_MAP.keys())
