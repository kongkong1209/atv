import re
import json
import requests


def extract_video_info(url: str) -> str:
    """
    抖音视频文案提取
    核心目标：获取视频的【文案/描述】用于后续 AI 改写
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/16.6 Mobile/15E148 Safari/604.1"
        ),
        "Accept": "application/json",
        "Referer": "https://www.douyin.com/",
    }

    try:
        # === Step 1: 提取视频 ID ===
        video_id = _extract_video_id(url, headers)
        if not video_id:
            return f"❌ 无法从链接中提取视频 ID\n原始链接: {url}"

        # === Step 2: 调用抖音详情 API ===
        # 使用移动端 API 接口
        api_url = f"https://www.iesdouyin.com/share/video/{video_id}/"
        resp = requests.get(api_url, headers=headers, timeout=15)
        
        # 从页面中提取 _ROUTER_DATA
        match = re.search(r'<script>window\._ROUTER_DATA\s*=\s*(\{.+?\})</script>', resp.text, re.DOTALL)
        if match:
            try:
                router_data = json.loads(match.group(1))
                return _parse_router_data(router_data, video_id)
            except json.JSONDecodeError:
                pass

        # 备用：从 HTML meta 标签提取
        desc_match = re.search(r'<meta name="description" content="([^"]*)"', resp.text)
        title_match = re.search(r'<meta property="og:title" content="([^"]*)"', resp.text)
        
        desc = desc_match.group(1) if desc_match else ""
        title = title_match.group(1) if title_match else ""
        
        if desc or title:
            content = desc or title
            return (
                "【文案】\n"
                f"{content}\n\n"
                "【视频ID】\n"
                f"{video_id}\n\n"
                "💡 提示：可直接复制上方文案到「文案编辑」进行 AI 改写"
            )

        # 最后兜底：使用第三方解析接口
        return _try_third_party_api(video_id, url)

    except Exception as e:
        return f"❌ 提取失败: {e}"


def _extract_video_id(url: str, headers: dict) -> str | None:
    """从各种格式的抖音链接中提取视频 ID"""
    
    # 情况1: 完整视频链接
    match = re.search(r"video/(\d{15,20})", url)
    if match:
        return match.group(1)

    # 情况2: 短链接，需要获取重定向
    if "v.douyin.com" in url or "iesdouyin.com" in url:
        try:
            # 提取短链接中的 URL
            url_match = re.search(r'(https?://v\.douyin\.com/[^\s/]+)', url)
            if url_match:
                url = url_match.group(1)
            
            resp = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
            final_url = str(resp.url)
            
            match = re.search(r"video/(\d{15,20})", final_url)
            if match:
                return match.group(1)
        except Exception:
            pass

    # 情况3: 从任意位置提取长数字 ID
    match = re.search(r"(\d{18,20})", url)
    if match:
        return match.group(1)

    return None


def _parse_router_data(data: dict, video_id: str) -> str:
    """解析 _ROUTER_DATA 数据"""
    try:
        # 遍历查找 aweme 详情
        for key, value in data.items():
            if isinstance(value, dict):
                loader_data = value.get("loaderData", {})
                for k, v in loader_data.items():
                    if isinstance(v, dict):
                        aweme = v.get("aweme", {}) or v.get("awemeDetail", {})
                        if aweme and "desc" in aweme:
                            return _format_output(aweme, video_id)
    except Exception:
        pass
    
    return f"⚠️ 数据解析失败\n\n【视频ID】\n{video_id}"


def _format_output(aweme: dict, video_id: str) -> str:
    """格式化输出"""
    desc = aweme.get("desc") or ""
    
    author = aweme.get("author", {})
    nickname = author.get("nickname") or author.get("name") or ""
    
    stats = aweme.get("statistics", {})
    likes = stats.get("digg_count", 0)
    comments = stats.get("comment_count", 0)
    
    result = "【文案】\n"
    result += f"{desc}\n\n"
    
    if nickname:
        result += f"【作者】\n{nickname}\n\n"
    
    if likes or comments:
        result += f"【数据】\n❤️ {_fmt(likes)} 点赞 | 💬 {_fmt(comments)} 评论\n\n"
    
    result += f"【视频ID】\n{video_id}\n\n"
    result += "💡 提示：可直接复制上方文案到「文案编辑」进行 AI 改写"
    
    return result


def _try_third_party_api(video_id: str, original_url: str) -> str:
    """尝试第三方解析接口（兜底方案）"""
    apis = [
        f"https://api.douyin.wtf/api?url=https://www.douyin.com/video/{video_id}",
        f"https://api.xingzhige.com/API/douyin/?url=https://www.douyin.com/video/{video_id}",
    ]
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for api_url in apis:
        try:
            resp = requests.get(api_url, headers=headers, timeout=10)
            data = resp.json()
            
            # 不同接口的数据结构不同，尝试提取
            desc = (
                data.get("desc") or 
                data.get("title") or 
                data.get("data", {}).get("desc") or
                data.get("data", {}).get("title") or
                ""
            )
            
            if desc:
                author = (
                    data.get("author") or 
                    data.get("nickname") or
                    data.get("data", {}).get("author") or
                    ""
                )
                
                result = "【文案】\n"
                result += f"{desc}\n\n"
                if author:
                    result += f"【作者】\n{author}\n\n"
                result += f"【视频ID】\n{video_id}\n\n"
                result += "💡 提示：可直接复制上方文案到「文案编辑」进行 AI 改写"
                return result
                
        except Exception:
            continue
    
    return (
        f"❌ 无法提取文案（抖音反爬限制）\n\n"
        f"【视频ID】\n{video_id}\n\n"
        f"【原始链接】\n{original_url}\n\n"
        "💡 建议：可以手动打开链接，复制视频描述到「文案编辑」"
    )


def _fmt(n) -> str:
    """格式化数字"""
    try:
        n = int(n)
        return f"{n/10000:.1f}万" if n >= 10000 else str(n)
    except:
        return str(n)
