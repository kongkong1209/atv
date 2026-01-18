import time
import random
import gradio as gr
from logic.crawler import real_crawler_task, real_crawler_link_task
from logic.editor import real_deepseek_rewrite


def mock_render(mode: str, avatar_image, voice_or_tts: str, broll_keywords: str):
    # TODO: integrate LuoGen / MoneyPrinterTurbo
    thought_log = ""
    yield (
        gr.update(visible=True, open=True),
        gr.update(value="", visible=True),
        None,
    )

    if mode == "数字人口播模式":
        steps = [
            "正在读取数字人素材...",
            "分析配音内容与节奏...",
            "构建口播镜头与字幕...",
            "合成视频与音轨...",
        ]
    else:
        steps = [
            "正在解析画面关键词...",
            "匹配素材库镜头...",
            "生成混剪节奏与转场...",
            "渲染合成视频...",
        ]

    for step in steps:
        thought_log += f"> 🤖 {step}\n\n"
        time.sleep(random.uniform(0.5, 1))
        yield (
            gr.update(visible=True, open=True),
            gr.update(value=thought_log, visible=True),
            None,
        )

    output_path = (
        "outputs/mock_digital_avatar.mp4"
        if mode == "数字人口播模式"
        else "outputs/mock_broll_mix.mp4"
    )
    thought_log += "> ✅ 渲染完成，视频已生成。"
    yield (
        gr.update(visible=True, open=False),
        gr.update(value=thought_log, visible=True),
        output_path,
    )


def mock_postprocess(video_file, options):
    # TODO: integrate Pixelle-Video / FFmpeg
    yield ""
    time.sleep(random.uniform(1, 3))
    opts = options or []
    name = video_file.name if video_file else "（未上传视频）"
    lines = [
        f"[INFO] 视频: {name}",
        f"[INFO] 处理选项: {', '.join(opts) if opts else '无'}",
        "[INFO] 任务已提交...",
        "[DONE] 后期处理完成（Mock）",
    ]
    yield "\n".join(lines)


def mock_publish(platforms, schedule_time):
    # TODO: integrate Matrix / Social-Auto-Upload
    yield ""
    time.sleep(random.uniform(1, 3))
    targets = platforms or []
    when = schedule_time or "立即发布"
    lines = [
        f"[INFO] 目标平台: {', '.join(targets) if targets else '未选择'}",
        f"[INFO] 发布时间: {when}",
        "[INFO] 分发任务已创建...",
        "[DONE] 发布完成（Mock）",
    ]
    yield "\n".join(lines)


with gr.Blocks(title="SuperMediaFactory") as demo:
    gr.Markdown("## SuperMediaFactory（超级自媒体工厂）")

    with gr.Tabs():
        with gr.TabItem("素材选择"):
            with gr.Row():
                with gr.Column(scale=2):
                    platform = gr.Dropdown(
                        ["抖音", "小红书", "B站", "公众号"],
                        label="平台选择",
                        value="抖音",
                    )
                    with gr.Tabs():
                        with gr.TabItem("关键词搜索"):
                            keyword_or_link = gr.Textbox(
                                label="关键词",
                                placeholder="输入关键词",
                            )
                            count = gr.Slider(1, 50, value=10, step=1, label="抓取数量")
                            collect_btn = gr.Button("开始采集")
                        with gr.TabItem("单链接提取"):
                            video_link = gr.Textbox(
                                label="抖音视频链接",
                                placeholder="请粘贴分享链接...",
                            )
                            link_btn = gr.Button("开始提取")
                with gr.Column(scale=3):
                    collect_thought = gr.Accordion("🧠 AI 深度思考中...", open=True)
                    with collect_thought:
                        collect_thought_md = gr.Markdown(value="", visible=True)
                    collect_table = gr.Dataframe(
                        label="📊 抓取结果榜单 (按点赞排序)",
                        headers=["点赞", "作者", "标题", "文案"],
                        interactive=False,
                    )
                    collect_text = gr.Textbox(
                        label="📝 最终提取文案 (可直接复制)",
                        lines=5,
                    )
            collect_btn.click(
                real_crawler_task,
                inputs=[platform, keyword_or_link, count],
                outputs=[collect_thought, collect_thought_md, collect_table, collect_text],
            )
            link_btn.click(
                real_crawler_link_task,
                inputs=[platform, video_link],
                outputs=[collect_thought, collect_thought_md, collect_table, collect_text],
            )

        with gr.TabItem("文案编辑"):
            with gr.Row():
                with gr.Column(scale=2):
                    raw_copy = gr.Textbox(
                        label="原始文案",
                        lines=12,
                        placeholder="可从素材情报局复制内容到此处",
                    )
                    rewrite_style = gr.Dropdown(
                        ["口播风", "种草风", "悬疑风", "新闻风"],
                        label="改写风格",
                        value="口播风",
                    )
                    deepseek_api_key = gr.Textbox(
                        label="DeepSeek API Key",
                        placeholder="填入你的 API Key（不建议写死在代码中）",
                        type="password",
                    )
                    rewrite_btn = gr.Button("AI 智能改写")
                with gr.Column(scale=3):
                    rewrite_thought = gr.Accordion("🧠 AI 深度思考中...", open=True)
                    with rewrite_thought:
                        rewrite_thought_md = gr.Markdown(value="", visible=True)
                    final_script = gr.Textbox(
                        label="最终分镜脚本",
                        lines=14,
                        interactive=True,
                    )
            rewrite_btn.click(
                real_deepseek_rewrite,
                inputs=[raw_copy, rewrite_style, deepseek_api_key],
                outputs=[rewrite_thought, rewrite_thought_md, final_script],
            )

        with gr.TabItem("视频生产线"):
            with gr.Row():
                mode = gr.Radio(
                    ["数字人口播模式", "画面混剪模式"],
                    label="模式选择",
                    value="数字人口播模式",
                )
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 数字人模式")
                    avatar_image = gr.Image(label="数字人图片", type="filepath")
                    voice_or_tts = gr.Textbox(
                        label="配音或 TTS 文本",
                        lines=4,
                        placeholder="输入文本或粘贴配音说明",
                    )
                with gr.Column():
                    gr.Markdown("### 混剪模式")
                    broll_keywords = gr.Textbox(
                        label="画面关键词",
                        lines=4,
                        placeholder="多个关键词用逗号分隔",
                    )
            render_btn = gr.Button("开始渲染视频")
            render_thought = gr.Accordion("🧠 AI 深度思考中...", open=True)
            with render_thought:
                render_thought_md = gr.Markdown(value="", visible=True)
            rendered_video = gr.Video(label="输出 MP4")
            render_btn.click(
                mock_render,
                inputs=[mode, avatar_image, voice_or_tts, broll_keywords],
                outputs=[render_thought, render_thought_md, rendered_video],
            )

        with gr.TabItem("后期与增强"):
            with gr.Row():
                with gr.Column(scale=2):
                    upload_video = gr.File(label="上传视频", file_types=["video"])
                    post_options = gr.CheckboxGroup(
                        ["去重（MD5）", "补帧", "4K 超分", "自动字幕"],
                        label="处理选项",
                    )
                    post_btn = gr.Button("执行后期处理")
                with gr.Column(scale=3):
                    post_log = gr.Textbox(label="处理日志", lines=10, interactive=False)
            post_btn.click(
                mock_postprocess,
                inputs=[upload_video, post_options],
                outputs=[post_log],
            )

        with gr.TabItem("矩阵分发"):
            with gr.Row():
                with gr.Column(scale=2):
                    publish_platforms = gr.CheckboxGroup(
                        ["抖音", "视频号", "小红书", "快手", "B站"],
                        label="选择平台",
                    )
                    schedule_time = gr.Textbox(
                        label="定时发布时间（可选）",
                        placeholder="例如：2026-01-18 20:30",
                    )
                    publish_btn = gr.Button("一键全网分发")
                with gr.Column(scale=3):
                    publish_log = gr.Textbox(label="发布日志", lines=10, interactive=False)
            publish_btn.click(
                mock_publish,
                inputs=[publish_platforms, schedule_time],
                outputs=[publish_log],
            )


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
