import time
import random
import gradio as gr
from logic.crawler import real_crawler_task, real_crawler_link_task, clear_login_state
from logic.editor import real_deepseek_rewrite
from logic.tts import text_to_speech_stream, get_available_voices
from logic.video_gen import merge_video_audio_stream


def mock_postprocess(video_file, options):
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


# 自定义主题 - 使用 Soft 深色主题作为基础
custom_theme = gr.themes.Soft(
    primary_hue=gr.themes.colors.blue,
    secondary_hue=gr.themes.colors.slate,
    neutral_hue=gr.themes.colors.slate,
)

# 自定义 CSS
custom_css = """
/* 全局样式 */
.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
}

/* 标题样式 */
.main-title {
    text-align: center;
    background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.5rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
    letter-spacing: -0.02em;
}

.sub-title {
    text-align: center;
    color: #94a3b8 !important;
    font-size: 1rem !important;
    margin-bottom: 1.5rem !important;
}

/* Tab 样式增强 */
.tabs {
    border-radius: 12px !important;
    overflow: hidden;
}

button.tab-nav {
    font-weight: 500 !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
}

button.tab-nav.selected {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
}

/* 卡片效果 */
.card-section {
    background: rgba(30, 41, 59, 0.8) !important;
    backdrop-filter: blur(10px);
    border-radius: 16px !important;
    padding: 20px !important;
    border: 1px solid #334155 !important;
    margin-bottom: 16px;
}

/* Accordion 样式 */
.accordion {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid #334155 !important;
    border-radius: 12px !important;
}

/* 按钮动画 */
button.primary {
    transition: all 0.3s ease !important;
    font-weight: 600 !important;
}

button.primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(59, 130, 246, 0.3) !important;
}

/* 输入框聚焦效果 */
textarea:focus, input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2) !important;
}

/* 数据表格样式 */
.dataframe {
    border-radius: 12px !important;
    overflow: hidden;
}

/* 分割线 */
hr {
    border-color: #334155 !important;
    margin: 24px 0 !important;
}

/* 滑块样式 */
input[type="range"] {
    accent-color: #3b82f6;
}

/* 下拉框样式 */
select {
    background-color: #0f172a !important;
    border-color: #475569 !important;
}

/* 区块标题 */
.section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #334155;
}

.section-header h3 {
    margin: 0;
    color: #f1f5f9;
    font-size: 1.1rem;
}
"""


with gr.Blocks(
    title="SuperMediaFactory - 超级自媒体工厂",
    theme=custom_theme,
    css=custom_css,
) as demo:
    
    # 标题区域
    gr.HTML("""
        <div style="padding: 20px 0;">
            <h1 class="main-title">SuperMediaFactory</h1>
            <p class="sub-title">AI 驱动的一站式自媒体内容生产平台</p>
        </div>
    """)

    with gr.Tabs() as tabs:
        # ==================== Tab 1: 素材选择 ====================
        with gr.TabItem("1. 素材采集", id="tab-collect"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">🎯</span><h3>采集配置</h3></div>')
                    
                    platform = gr.Dropdown(
                        ["抖音", "小红书", "B站", "公众号"],
                        label="目标平台",
                        value="抖音",
                        info="选择要采集的内容平台",
                    )
                    
                    with gr.Tabs() as collect_tabs:
                        with gr.TabItem("关键词搜索"):
                            keyword_or_link = gr.Textbox(
                                label="搜索关键词",
                                placeholder="输入关键词，如：美食探店、穿搭分享...",
                                lines=1,
                            )
                            count = gr.Slider(
                                1, 50, value=10, step=1,
                                label="采集数量",
                                info="建议首次采集 10-20 条",
                            )
                            collect_btn = gr.Button(
                                "🔍 开始采集",
                                variant="primary",
                            )
                            
                        with gr.TabItem("单链接提取"):
                            video_link = gr.Textbox(
                                label="视频链接",
                                placeholder="粘贴抖音/小红书分享链接...",
                                lines=2,
                            )
                            with gr.Row():
                                link_btn = gr.Button(
                                    "🚀 提取内容",
                                    variant="primary",
                                )
                                clear_login_btn = gr.Button(
                                    "🔄 清除登录",
                                    variant="secondary",
                                )
                            login_status = gr.Textbox(
                                label="状态",
                                interactive=False,
                                visible=False,
                            )

                with gr.Column(scale=3):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">📊</span><h3>采集结果</h3></div>')
                    
                    collect_thought = gr.Accordion("AI 分析进度", open=True)
                    with collect_thought:
                        collect_thought_md = gr.Markdown(value="等待开始采集...")
                        
                    collect_table = gr.Dataframe(
                        label="热门内容榜单（按互动量排序）",
                        headers=["点赞", "作者", "标题", "文案"],
                        interactive=False,
                        wrap=True,
                    )
                    
                    collect_text = gr.Textbox(
                        label="提取的文案内容",
                        lines=4,
                        placeholder="采集完成后，文案将显示在这里...",
                    )

            # 绑定事件
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
            
            def on_clear_login(plat):
                msg = clear_login_state(plat)
                return gr.update(value=msg, visible=True)
            
            clear_login_btn.click(
                on_clear_login,
                inputs=[platform],
                outputs=[login_status],
            )

        # ==================== Tab 2: 文案编辑 ====================
        with gr.TabItem("2. 文案编辑", id="tab-edit"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">✏️</span><h3>文案改写</h3></div>')
                    
                    raw_copy = gr.Textbox(
                        label="原始文案",
                        lines=6,
                        placeholder="粘贴或输入需要改写的原始文案...",
                    )
                    
                    rewrite_style = gr.Dropdown(
                        ["口播风", "种草风", "悬疑风", "新闻风"],
                        label="改写风格",
                        value="口播风",
                        info="选择适合你内容的风格",
                    )
                    
                    deepseek_api_key = gr.Textbox(
                        label="DeepSeek API Key",
                        placeholder="sk-xxxxxxxx",
                        type="password",
                        info="用于 AI 改写，请妥善保管",
                    )
                    
                    rewrite_btn = gr.Button(
                        "✨ AI 智能改写",
                        variant="primary",
                    )
                    
                with gr.Column(scale=3):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">📝</span><h3>改写结果</h3></div>')
                    
                    rewrite_thought = gr.Accordion("AI 思考过程", open=True)
                    with rewrite_thought:
                        rewrite_thought_md = gr.Markdown(value="等待开始改写...")
                        
                    final_script = gr.Textbox(
                        label="最终脚本（可编辑）",
                        lines=6,
                        interactive=True,
                        placeholder="改写后的脚本将显示在这里...",
                    )
            
            rewrite_btn.click(
                real_deepseek_rewrite,
                inputs=[raw_copy, rewrite_style, deepseek_api_key],
                outputs=[rewrite_thought, rewrite_thought_md, final_script],
            )
            
            gr.HTML('<hr style="margin: 32px 0; border-color: #334155;">')
            
            # AI 配音区域
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">🎙️</span><h3>AI 配音</h3></div>')
                    
                    tts_voice = gr.Dropdown(
                        choices=get_available_voices(),
                        label="语音角色",
                        value="晓晓 (女声-温柔)",
                        info="选择配音的声音风格",
                    )
                    
                    tts_btn = gr.Button(
                        "🎤 生成配音",
                        variant="primary",
                    )
                    
                with gr.Column(scale=3):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">🔊</span><h3>配音输出</h3></div>')
                    
                    tts_thought = gr.Accordion("生成进度", open=True)
                    with tts_thought:
                        tts_thought_md = gr.Markdown(value="等待开始生成...")
                        
                    audio_output = gr.Audio(
                        label="生成的配音",
                        type="filepath",
                    )
            
            def run_tts(text, voice):
                thought_log = ""
                audio_path = None
                
                yield (
                    gr.update(visible=True, open=True),
                    gr.update(value="", visible=True),
                    None,
                )
                
                if not text or not text.strip():
                    thought_log = "> ❌ 错误：文案内容为空，请先填写或生成文案\n"
                    yield (gr.update(open=False), gr.update(value=thought_log), None)
                    return
                
                for progress, result in text_to_speech_stream(text, voice):
                    thought_log += f"> 🤖 {progress}\n\n"
                    if result:
                        audio_path = result
                    yield (gr.update(), gr.update(value=thought_log), audio_path)
                
                if audio_path:
                    thought_log += "> ✅ 配音生成完成\n"
                yield (gr.update(open=False), gr.update(value=thought_log), audio_path)
            
            tts_btn.click(
                run_tts,
                inputs=[final_script, tts_voice],
                outputs=[tts_thought, tts_thought_md, audio_output],
            )

        # ==================== Tab 3: 视频生产 ====================
        with gr.TabItem("3. 视频生产", id="tab-video"):
            gr.HTML("""
                <div style="text-align: center; padding: 16px 0; margin-bottom: 24px; 
                            background: linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(139,92,246,0.1) 100%);
                            border-radius: 12px; border: 1px solid #334155;">
                    <h2 style="margin: 0; color: #f1f5f9; font-size: 1.5rem;">🎬 视频生产流水线</h2>
                    <p style="margin: 8px 0 0; color: #94a3b8;">阶段1: 音画合成 → 阶段2: 数字人合成</p>
                </div>
            """)
            
            # 阶段1
            gr.HTML('<div class="section-header"><span style="font-size:1.2em;">📼</span><h3>阶段1：音画合成</h3></div>')
            
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    video_input = gr.Video(
                        label="📹 背景视频素材",
                        sources=["upload"],
                    )
                    
                    audio_input = gr.Audio(
                        label="🎵 配音文件",
                        type="filepath",
                    )
                    
                    merge_mode = gr.Radio(
                        choices=["循环视频 (匹配音频时长)", "截断音频 (匹配视频时长)"],
                        label="⏱️ 时长处理",
                        value="循环视频 (匹配音频时长)",
                    )
                    
                    merge_btn = gr.Button(
                        "🎬 开始合成",
                        variant="primary",
                    )
                    
                with gr.Column(scale=3):
                    merge_thought = gr.Accordion("处理进度", open=True)
                    with merge_thought:
                        merge_thought_md = gr.Markdown(value="等待开始合成...")
                        
                    video_step1_output = gr.Video(label="🎥 阶段1输出")
            
            def run_merge(video, audio, mode):
                thought_log = ""
                output_path = None
                
                yield (
                    gr.update(visible=True, open=True),
                    gr.update(value="", visible=True),
                    None,
                )
                
                video_path = video if isinstance(video, str) else (video.name if video else None)
                
                if not video_path:
                    thought_log = "> ❌ 错误：请先上传视频文件\n"
                    yield (gr.update(open=False), gr.update(value=thought_log), None)
                    return
                if not audio:
                    thought_log = "> ❌ 错误：请先上传或生成配音文件\n"
                    yield (gr.update(open=False), gr.update(value=thought_log), None)
                    return
                
                loop_video = "循环视频" in mode
                
                for progress, result in merge_video_audio_stream(video_path, audio, loop_video):
                    thought_log += f"> 🤖 {progress}\n\n"
                    if result:
                        output_path = result
                    yield (gr.update(), gr.update(value=thought_log), output_path)
                
                if output_path:
                    thought_log += "> ✅ 阶段1完成\n"
                yield (gr.update(open=False), gr.update(value=thought_log), output_path)
            
            merge_btn.click(
                run_merge,
                inputs=[video_input, audio_input, merge_mode],
                outputs=[merge_thought, merge_thought_md, video_step1_output],
            )
            
            gr.HTML('<hr style="margin: 32px 0; border-color: #334155;">')
            
            # 阶段2
            gr.HTML('<div class="section-header"><span style="font-size:1.2em;">🧑‍💻</span><h3>阶段2：数字人合成</h3></div>')
            
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    avatar_video = gr.Video(
                        label="🧑 数字人视频（绿幕/透明）",
                        sources=["upload"],
                    )
                    
                    base_video = gr.Video(
                        label="📹 底层视频",
                        sources=["upload"],
                    )
                    
                    avatar_position = gr.Radio(
                        choices=["右下角", "左下角", "右上角", "左上角", "居中"],
                        label="🎯 数字人位置",
                        value="右下角",
                    )
                    
                    avatar_scale = gr.Slider(
                        minimum=0.1, maximum=1.0, value=0.3, step=0.05,
                        label="📐 缩放比例",
                    )
                    
                    avatar_btn = gr.Button(
                        "🧑‍💻 开始合成",
                        variant="primary",
                    )
                    
                with gr.Column(scale=3):
                    avatar_thought = gr.Accordion("处理进度", open=True)
                    with avatar_thought:
                        avatar_thought_md = gr.Markdown(value="等待开始合成...")
                        
                    video_final_output = gr.Video(label="🎬 最终成品")
            
            def run_avatar_merge(avatar, base, position, scale):
                thought_log = ""
                yield (
                    gr.update(visible=True, open=True),
                    gr.update(value="", visible=True),
                    None,
                )
                
                thought_log += "> 🚧 数字人合成功能开发中...\n\n"
                thought_log += "> 📋 计划集成方案：\n"
                thought_log += ">   - SadTalker / Wav2Lip\n"
                thought_log += ">   - FFmpeg 绿幕抠像\n"
                thought_log += ">   - MuseTalk / LivePortrait\n\n"
                thought_log += f"> 📍 已选位置: {position}\n"
                thought_log += f"> 📐 缩放比例: {scale}\n\n"
                thought_log += "> ⏳ 敬请期待\n"
                
                yield (gr.update(open=False), gr.update(value=thought_log), None)
            
            avatar_btn.click(
                run_avatar_merge,
                inputs=[avatar_video, base_video, avatar_position, avatar_scale],
                outputs=[avatar_thought, avatar_thought_md, video_final_output],
            )

        # ==================== Tab 4: 后期增强 ====================
        with gr.TabItem("4. 后期增强", id="tab-post"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">🎨</span><h3>后期处理</h3></div>')
                    
                    upload_video = gr.File(
                        label="上传视频",
                        file_types=["video"],
                    )
                    
                    post_options = gr.CheckboxGroup(
                        ["去重（MD5）", "补帧", "4K 超分", "自动字幕"],
                        label="处理选项",
                        info="选择需要的后期处理功能",
                    )
                    
                    post_btn = gr.Button(
                        "⚡ 执行处理",
                        variant="primary",
                    )
                    
                with gr.Column(scale=3):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">📋</span><h3>处理日志</h3></div>')
                    
                    post_log = gr.Textbox(
                        label="执行日志",
                        lines=12,
                        interactive=False,
                        placeholder="处理日志将显示在这里...",
                    )
                    
            post_btn.click(
                mock_postprocess,
                inputs=[upload_video, post_options],
                outputs=[post_log],
            )

        # ==================== Tab 5: 矩阵分发 ====================
        with gr.TabItem("5. 矩阵分发", id="tab-publish"):
            with gr.Row(equal_height=False):
                with gr.Column(scale=2):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">🚀</span><h3>发布配置</h3></div>')
                    
                    publish_platforms = gr.CheckboxGroup(
                        ["抖音", "视频号", "小红书", "快手", "B站"],
                        label="目标平台",
                        info="选择要发布的平台",
                    )
                    
                    schedule_time = gr.Textbox(
                        label="定时发布（可选）",
                        placeholder="如：2026-01-18 20:30",
                        info="留空则立即发布",
                    )
                    
                    publish_btn = gr.Button(
                        "🚀 一键分发",
                        variant="primary",
                    )
                    
                with gr.Column(scale=3):
                    gr.HTML('<div class="section-header"><span style="font-size:1.2em;">📋</span><h3>发布日志</h3></div>')
                    
                    publish_log = gr.Textbox(
                        label="发布状态",
                        lines=12,
                        interactive=False,
                        placeholder="发布日志将显示在这里...",
                    )
                    
            publish_btn.click(
                mock_publish,
                inputs=[publish_platforms, schedule_time],
                outputs=[publish_log],
            )
    
    # 底部信息
    gr.HTML("""
        <div style="text-align: center; padding: 24px 0; margin-top: 24px; 
                    border-top: 1px solid #334155; color: #64748b; font-size: 0.875rem;">
            SuperMediaFactory v1.0 | AI 驱动的自媒体内容生产平台
        </div>
    """)


if __name__ == "__main__":
    demo.launch()
