import glob
import json
import os
import re
import sys
import gradio as gr
from logic.utils import run_module_stream

# 平台代码 -> 文件夹名称的映射
FOLDER_NAME_MAP = {
    "dy": "douyin",
    "xhs": "xhs",
    "bilibili": "bilibili",
    "ks": "kuaishou",
}

PLATFORM_MAP = {
    "抖音": "dy",
    "小红书": "xhs",
    "B站": "bilibili",
    "快手": "ks",
}

def clean_old_data(crawler_path: str, platform_code: str):
    """
    清理旧数据文件，但保留浏览器缓存（登录状态）。
    """
    logs = []
    
    # 只清理结果文件 (JSON)，不删除 browser_data（保留登录状态）
    folder_name = FOLDER_NAME_MAP.get(platform_code, platform_code)
    json_dir = os.path.join(crawler_path, "data", folder_name, "json")
    
    if os.path.exists(json_dir):
        deleted_count = 0
        for file_name in os.listdir(json_dir):
            if file_name.startswith("search_contents_") or file_name.startswith("search_comments_") or file_name.startswith("detail_"):
                file_path = os.path.join(json_dir, file_name)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception:
                    pass
        if deleted_count > 0:
            logs.append(f"> 🧹 已清理 {deleted_count} 个旧数据文件 (登录状态已保留)")
    
    return "\n".join(logs) + "\n\n" if logs else ""

def real_crawler_task(platform: str, keyword_or_link: str, count: int):
    # --- 初始化 ---
    thought_log = ""
    yield (
        gr.update(visible=True, open=True),
        gr.update(value="", visible=True),
        [],
        "",
    )

    keyword = keyword_or_link.strip()
    if not keyword:
        thought_log += "> ❌ 错误：关键词不能为空！\n\n"
        yield (gr.update(open=False), gr.update(value=thought_log), [], "")
        return

    crawler_path = os.path.join(os.getcwd(), "modules", "mediacrawler")
    platform_code = PLATFORM_MAP.get(platform, "dy")

    # --- 执行清理 ---
    thought_log += clean_old_data(crawler_path, platform_code)
    yield (gr.update(), gr.update(value=thought_log), [], "")

    # --- 构造命令 ---
    # 注意：已移除 --enable_comment 参数
    cmd = [
        sys.executable,
        "main.py",
        "--platform", platform_code,
        "--keywords", keyword,
        "--type", "search",
        "--lt", "qrcode"
    ]

    thought_log += f"> [DEBUG] 构造命令: {' '.join(cmd)}\n\n"
    yield (gr.update(), gr.update(value=thought_log), [], "")

    # --- 运行爬虫 ---
    for line in run_module_stream(cmd, cwd=crawler_path):
        thought_log += f"> 🤖 {line}\n\n"
        yield (gr.update(), gr.update(value=thought_log), [], "")

    # --- 读取结果 ---
    table_data, _, error_msg = get_latest_data(crawler_path, platform_code, mode="search")
    
    if error_msg:
        thought_log += f"> ❌ {error_msg}\n"
        yield (gr.update(open=False), gr.update(value=thought_log), [], "")
    else:
        thought_log += f"> ✅ 成功抓取 {len(table_data)} 条数据\n"
        yield (gr.update(open=False), gr.update(value=thought_log), table_data, None)

def real_crawler_link_task(platform: str, video_link: str):
    """
    单链接提取模式 - 使用 MediaCrawler 的 detail 模式
    """
    # --- 初始化 ---
    thought_log = ""
    yield (
        gr.update(visible=True, open=True),
        gr.update(value="", visible=True),
        [],
        "",
    )

    link_text = video_link.strip()
    if not link_text:
        thought_log += "> ❌ 错误：链接不能为空！\n\n"
        yield (gr.update(open=False), gr.update(value=thought_log), [], "")
        return

    # 正则提取链接 (支持分享文本中混杂的链接)
    match = re.search(r'(https?://[a-zA-Z0-9\./\-_?=&]+)', link_text)
    clean_url = match.group(0) if match else link_text
    
    thought_log += f"> [DEBUG] 清洗后链接: {clean_url}\n\n"
    yield (gr.update(), gr.update(value=thought_log), [], "")

    crawler_path = os.path.join(os.getcwd(), "modules", "mediacrawler")
    platform_code = PLATFORM_MAP.get(platform, "dy")

    # --- 执行清理 ---
    thought_log += clean_old_data(crawler_path, platform_code)
    yield (gr.update(), gr.update(value=thought_log), [], "")

    # --- 构造命令 (使用 detail 模式 + specified_id) ---
    cmd = [
        sys.executable,
        "main.py",
        "--platform", platform_code,
        "--type", "detail",
        "--specified_id", clean_url,
        "--lt", "qrcode",
        "--get_comment", "false",  # 单链接模式不需要评论
    ]

    thought_log += f"> 🚀 使用 MediaCrawler detail 模式提取视频...\n\n"
    thought_log += f"> [DEBUG] 命令: {' '.join(cmd)}\n\n"
    yield (gr.update(), gr.update(value=thought_log), [], "")

    # --- 运行爬虫 ---
    for line in run_module_stream(cmd, cwd=crawler_path):
        thought_log += f"> 🤖 {line}\n\n"
        yield (gr.update(), gr.update(value=thought_log), [], "")

    # --- 读取结果 ---
    _, best_content, error_msg = get_latest_data(crawler_path, platform_code, mode="detail")
    
    if error_msg:
        thought_log += f"> ❌ {error_msg}\n"
        yield (gr.update(open=False), gr.update(value=thought_log), [], "")
    elif best_content:
        thought_log += "> ✅ 提取成功！\n"
        thought_log += "\n💡 提示：可直接复制上方文案到「文案编辑」进行 AI 改写"
        yield (gr.update(open=False), gr.update(value=thought_log), None, best_content)
    else:
        thought_log += "> ❌ 未能提取到文案内容\n"
        yield (gr.update(open=False), gr.update(value=thought_log), [], "")

def get_latest_data(crawler_path: str, platform_code: str, mode: str):
    folder_name = FOLDER_NAME_MAP.get(platform_code, platform_code)
    
    # 强制只读 search_contents_*.json 或 detail_*.json (如果存在)
    # MediaCrawler 在 detail 模式下通常还是生成 search_contents 或 detail
    # 我们优先尝试 detail_*.json，如果没有再找 search_contents_*.json
    
    base_dir = os.path.join(crawler_path, "data", folder_name, "json")
    
    # 查找策略：先找最新生成的文件
    search_patterns = [
        os.path.join(base_dir, "detail_*.json"),
        os.path.join(base_dir, "search_contents_*.json")
    ]
    
    files = []
    for p in search_patterns:
        files.extend(glob.glob(p))
        
    if not files:
        return None, None, "未生成新数据文件 (爬虫可能未成功抓取)"

    # 找最新的文件
    latest = max(files, key=os.path.getmtime)
    
    try:
        with open(latest, "r", encoding="utf-8") as file:
            data = json.load(file)
            items = data if isinstance(data, list) else [data]
    except Exception as e:
        return None, None, f"文件读取错误: {str(e)}"

    if not items:
        return None, None, "数据文件内容为空"

    # 单链接模式
    if mode == "detail":
        last_item = items[-1]
        if isinstance(last_item, dict):
            title = last_item.get("title", "") or ""
            desc = last_item.get("desc", "") or ""
            # 简单纯净的返回
            content = f"【标题】{title}\n\n【文案】{desc}"
            return None, content, None
        return None, None, "数据格式解析失败"

    # 关键词模式
    rows = []
    for item in items:
        if not isinstance(item, dict): continue
        liked_val = parse_liked(item.get("liked_count", 0))
        nickname = item.get("nickname", "")
        title = item.get("title", "")
        desc = item.get("desc", "")
        rows.append([liked_val, nickname, title, desc])

    rows.sort(key=lambda r: r[0], reverse=True)
    return rows, None, None

def parse_liked(value):
    if value is None: return 0
    if isinstance(value, (int, float)): return int(value)
    text = str(value).strip().replace("+", "").replace(",", "")
    try:
        if "万" in text or "w" in text.lower():
            num = re.findall(r"\d+\.?\d*", text)[0]
            return int(float(num) * 10000)
        return int(float(text))
    except:
        return 0