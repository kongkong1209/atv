import glob
import json
import os
import re
import sys
import gradio as gr

from logic.utils import run_module_stream


PLATFORM_MAP = {
    "抖音": "dy",
    "小红书": "xhs",
    "B站": "bilibili",
    "快手": "ks",
}
FOLDER_NAME_MAP = {
    "dy": "douyin",
    "ks": "kuaishou",
    "xhs": "xhs",
    "bilibili": "bilibili",
}


def real_crawler_task(platform: str, keyword_or_link: str, count: int):
    # TODO: integrate MediaCrawler / We-Mp-RSS
    thought_log = ""
    platform_code = PLATFORM_MAP.get(platform, "xhs")
    crawler_path = os.path.join(os.getcwd(), "modules", "mediacrawler")
    cleanup_msg = _cleanup_old_files(crawler_path, platform_code)
    if cleanup_msg:
        thought_log += cleanup_msg
    browser_cleanup = _cleanup_browser_data(crawler_path)
    if browser_cleanup:
        thought_log += browser_cleanup
    yield (
        gr.update(visible=True, open=True),
        gr.update(value="", visible=True),
        [],
        "",
    )

    keyword = keyword_or_link.strip()
    if not keyword:
        thought_log += "> ❌ 错误：关键词不能为空，请在左侧输入内容！\n\n"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            [],
            "",
        )
        return

    if not os.path.isdir(crawler_path):
        thought_log += f"> ❌ 未找到爬虫目录: {crawler_path}\n\n"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            [],
            "",
        )
        return

    thought_log += f"> 📂 正在切换工作目录至: {crawler_path}\n\n"
    yield (
        gr.update(visible=True, open=True),
        gr.update(value=thought_log, visible=True),
        [],
        "",
    )

    cmd = [
        sys.executable,
        "main.py",
        "--platform",
        platform_code,
        "--keywords",
        keyword,
        "--type",
        "search",
        "--lt",
        "qrcode",
    ]
    thought_log += (
        f"> [DEBUG] 构造命令: python main.py --platform {platform_code} "
        f"--keywords {keyword} --type search --lt qrcode\n\n"
    )
    yield (
        gr.update(visible=True, open=True),
        gr.update(value=thought_log, visible=True),
        [],
        "",
    )

    for line in run_module_stream(cmd, cwd=crawler_path):
        thought_log += f"> 🤖 {line}\n\n"
        yield (
            gr.update(visible=True, open=True),
            gr.update(value=thought_log, visible=True),
            [],
            "",
        )

    table_data, best_content, error_msg = get_latest_data(
        crawler_path, platform_code, mode="search"
    )
    if error_msg:
        thought_log += f"> ❌ 错误：{error_msg}\n\n"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            [],
            "",
        )
        return

    thought_log += "> ✅ 数据抓取完成，正在加载结果...\n\n"
    thought_log += "> ✅ 爬虫任务结束"
    yield (
        gr.update(visible=True, open=False),
        gr.update(value=thought_log, visible=True),
        table_data,
        None,
    )


def real_crawler_link_task(platform: str, video_link: str):
    # TODO: integrate MediaCrawler / We-Mp-RSS
    thought_log = ""
    platform_code = PLATFORM_MAP.get(platform, "xhs")
    crawler_path = os.path.join(os.getcwd(), "modules", "mediacrawler")
    cleanup_msg = _cleanup_old_files(crawler_path, platform_code)
    if cleanup_msg:
        thought_log += cleanup_msg
    browser_cleanup = _cleanup_browser_data(crawler_path)
    if browser_cleanup:
        thought_log += browser_cleanup
    yield (
        gr.update(visible=True, open=True),
        gr.update(value="", visible=True),
        [],
        "",
    )

    link_text = video_link.strip()
    if not link_text:
        thought_log += "> ❌ 错误：抖音视频链接不能为空，请输入后再试！\n\n"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            [],
            "",
        )
        return

    match = re.search(r"(https?://[a-zA-Z0-9\./\-_]+)", link_text)
    clean_url = match.group(0) if match else link_text
    thought_log += f"> [DEBUG] 原始输入: {link_text}\n\n"
    thought_log += f"> [DEBUG] 清洗后链接: {clean_url}\n\n"
    yield (
        gr.update(visible=True, open=True),
        gr.update(value=thought_log, visible=True),
        [],
        "",
    )

    if not os.path.isdir(crawler_path):
        thought_log += f"> ❌ 未找到爬虫目录: {crawler_path}\n\n"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            [],
            "",
        )
        return

    thought_log += f"> 📂 正在切换工作目录至: {crawler_path}\n\n"
    yield (
        gr.update(visible=True, open=True),
        gr.update(value=thought_log, visible=True),
        [],
        "",
    )

    cmd = [
        sys.executable,
        "main.py",
        "--platform",
        platform_code,
        "--keywords",
        clean_url,
        "--type",
        "detail",
        "--lt",
        "qrcode",
    ]
    thought_log += (
        f"> [DEBUG] 构造命令: python main.py --platform {platform_code} "
        f"--keywords {clean_url} --type detail --lt qrcode\n\n"
    )
    yield (
        gr.update(visible=True, open=True),
        gr.update(value=thought_log, visible=True),
        [],
        "",
    )

    for line in run_module_stream(cmd, cwd=crawler_path):
        thought_log += f"> 🤖 {line}\n\n"
        yield (
            gr.update(visible=True, open=True),
            gr.update(value=thought_log, visible=True),
            [],
            "",
        )

    table_data, best_content, error_msg = get_latest_data(
        crawler_path, platform_code, mode="detail"
    )
    if error_msg:
        thought_log += f"> ❌ 错误：{error_msg}\n\n"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            [],
            "",
        )
        return

    thought_log += "> ✅ 数据抓取完成，正在加载结果...\n\n"
    thought_log += "> ✅ 爬虫任务结束"
    yield (
        gr.update(visible=True, open=False),
        gr.update(value=thought_log, visible=True),
        None,
        best_content,
    )


def get_latest_data(crawler_path: str, platform_code: str, mode: str):
    folder_name = FOLDER_NAME_MAP.get(platform_code, platform_code)
    if mode == "detail":
        json_pattern = os.path.join(
            crawler_path, "data", folder_name, "json", "detail_*.json"
        )
    else:
        json_pattern = os.path.join(
            crawler_path, "data", folder_name, "json", "search_contents_*.json"
        )
    files = glob.glob(json_pattern)
    if not files:
        return None, None, "未生成新数据，请检查爬虫日志。"
    latest = max(files, key=os.path.getmtime)
    try:
        with open(latest, "r", encoding="utf-8") as file:
            data = json.load(file)
            items = data if isinstance(data, list) else [data]
    except Exception:
        return None, None, "未生成新数据，请检查爬虫日志。"

    if not items:
        return None, None, "未找到有效数据，请检查爬虫日志。"

    if mode == "detail":
        last_item = items[-1]
        desc = ""
        title = ""
        if isinstance(last_item, dict):
            desc = last_item.get("desc", "") or ""
            title = last_item.get("title", "") or ""
        best_content = desc or title
        return None, best_content, None

    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        liked = parse_liked(item.get("liked_count"))
        nickname = item.get("nickname", "") or ""
        title = item.get("title", "") or ""
        desc = item.get("desc", "") or ""
        rows.append([liked, nickname, title, desc])
    rows.sort(key=lambda r: r[0], reverse=True)
    return rows, None, None


def parse_liked(value):
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace("+", "").replace(",", "")
    if "万" in text:
        number = text.replace("万", "").strip()
        try:
            return int(float(number) * 10000)
        except ValueError:
            return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def _cleanup_old_files(crawler_path: str, platform_code: str):
    folder_name = FOLDER_NAME_MAP.get(platform_code, platform_code)
    target_dir = os.path.join(crawler_path, "data", folder_name, "json")
    if not os.path.isdir(target_dir):
        return ""
    patterns = [
        os.path.join(target_dir, "search_contents_*.json"),
        os.path.join(target_dir, "search_comments_*.json"),
    ]
    removed = 0
    for pattern in patterns:
        for path in glob.glob(pattern):
            try:
                os.remove(path)
                removed += 1
            except OSError:
                continue
    if removed:
        return "> 🧹 已清理旧数据文件，准备开始新任务...\n"
    return ""


def _cleanup_browser_data(crawler_path: str):
    browser_dir = os.path.join(crawler_path, "browser_data")
    if not os.path.isdir(browser_dir):
        return ""
    removed = 0
    for root, dirs, files in os.walk(browser_dir, topdown=False):
        for name in files:
            try:
                os.remove(os.path.join(root, name))
                removed += 1
            except OSError:
                continue
        for name in dirs:
            try:
                os.rmdir(os.path.join(root, name))
            except OSError:
                continue
    try:
        os.rmdir(browser_dir)
    except OSError:
        pass
    if removed:
        return "> 🧹 已清理浏览器缓存目录，避免复读旧标签页...\n"
    return ""
