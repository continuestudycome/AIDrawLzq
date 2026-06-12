"""占位图像生成：在真实 AI 绘图接入前，返回可预览的 SVG 占位图。"""

import base64
import html
import textwrap


def build_placeholder_image_data_url(
    prompt: str,
    *,
    width: int = 512,
    height: int = 512,
) -> str:
    """根据提示词生成 SVG 占位图，并以 data URL 形式返回。"""
    safe_prompt = html.escape(prompt.strip() or "（空提示词）")
    wrapped_lines = textwrap.wrap(safe_prompt, width=18) or ["（空提示词）"]
    line_elements = "\n".join(
        f'<tspan x="50%" dy="{28 if index else 0}">{line}</tspan>'
        for index, line in enumerate(wrapped_lines[:6])
    )
    extra_hint = ""
    if len(wrapped_lines) > 6:
        extra_hint = '<tspan x="50%" dy="28">…</tspan>'

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#1e1b4b"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <rect x="24" y="24" width="{width - 48}" height="{height - 48}" rx="16" fill="none" stroke="#6366f1" stroke-width="2" stroke-dasharray="8 6"/>
  <text x="50%" y="42%" text-anchor="middle" fill="#c7d2fe" font-size="20" font-family="Segoe UI, sans-serif">占位预览图</text>
  <text x="50%" y="52%" text-anchor="middle" fill="#e2e8f0" font-size="16" font-family="Segoe UI, sans-serif">
    {line_elements}
    {extra_hint}
  </text>
  <text x="50%" y="88%" text-anchor="middle" fill="#94a3b8" font-size="13" font-family="Segoe UI, sans-serif">AI 绘图服务尚未接入</text>
</svg>"""

    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
