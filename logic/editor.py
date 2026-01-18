import time
import gradio as gr
from openai import OpenAI


def real_deepseek_rewrite(raw_text: str, style: str, api_key: str):
    thought_log = ""
    output_text = ""
    yield (
        gr.update(visible=True, open=True),
        gr.update(value="", visible=True),
        "",
    )

    steps = [
        "正在读取原始文案...",
        "正在构建 Prompt...",
        f"加载「{style}」风格模板...",
        "正在连接 DeepSeek V3...",
    ]
    for step in steps:
        thought_log += f"> 🤖 {step}\n\n"
        time.sleep(0.5)
        yield (
            gr.update(visible=True, open=True),
            gr.update(value=thought_log, visible=True),
            output_text,
        )

    if not api_key:
        thought_log += "> ❌ 未配置 DeepSeek API Key，请填写后重试。"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            "",
        )
        return

    style_prompts = {
        "口播风": "你是一个金牌短视频编剧，请把以下内容改写为口语化、快节奏的口播文案。",
        "种草风": "你是一个小红书博主，请用Emoji丰富、真诚推荐的语气改写。",
        "悬疑风": "你是一个悬疑故事作者，请营造悬念感与反转感改写内容。",
        "新闻风": "你是新闻编辑，请用简洁、客观、信息密度高的方式改写。",
    }
    system_prompt = style_prompts.get(
        style,
        "请把以下内容改写为更适合短视频传播的文案。",
    )

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        thought_log += "> 🤖 正在生成内容..."
        yield (
            gr.update(visible=True, open=True),
            gr.update(value=thought_log, visible=True),
            output_text,
        )

        stream = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text},
            ],
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if not delta:
                continue
            output_text += delta
            yield (
                gr.update(visible=True, open=True),
                gr.update(value=thought_log, visible=True),
                output_text,
            )

        thought_log += "\n\n> ✅ 思考完成，内容已生成。"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            output_text,
        )
    except Exception as exc:
        thought_log += f"> ❌ 请求失败：{exc}"
        yield (
            gr.update(visible=True, open=False),
            gr.update(value=thought_log, visible=True),
            output_text,
        )
