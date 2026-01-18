import yt_dlp


def extract_video_info(url: str) -> str:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ),
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        title = (info or {}).get("title") or ""
        description = (info or {}).get("description") or ""
        uploader = (info or {}).get("uploader") or ""
        webpage_url = (info or {}).get("webpage_url") or url
        return (
            "【标题】\n"
            f"{title}\n\n"
            "【作者】\n"
            f"{uploader}\n\n"
            "【文案】\n"
            f"{description}\n\n"
            "【链接】\n"
            f"{webpage_url}"
        )
    except Exception as exc:
        return f"❌ 提取失败: {exc}"
