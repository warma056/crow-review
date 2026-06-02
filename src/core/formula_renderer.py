# 模块用途：把文本中的 LaTeX 公式（$...$、$$...$$）渲染为 tkinter PhotoImage
# 依赖：matplotlib、Pillow
# 放置路径：src/core/formula_renderer.py

import re
import io
from PIL import Image, ImageTk

_FORMULA_RE = re.compile(r'(\$\$[\s\S]+?\$\$|\$[^\$\n]+?\$)')


def split_formula_segments(text: str) -> list:
    """
    把文本拆分成普通文字和公式交替的片段列表。
    每个元素：{'type': 'text'|'formula', 'content': str, 'display': bool}
    display=True 表示 $$...$$ （独占行块级公式），False 表示 $...$（行内）
    """
    segments = []
    last = 0
    for m in _FORMULA_RE.finditer(text):
        if m.start() > last:
            segments.append({'type': 'text', 'content': text[last:m.start()], 'display': False})
        raw = m.group(0)
        if raw.startswith('$$'):
            latex = raw[2:-2].strip()
            segments.append({'type': 'formula', 'content': latex, 'display': True})
        else:
            latex = raw[1:-1].strip()
            segments.append({'type': 'formula', 'content': latex, 'display': False})
        last = m.end()
    if last < len(text):
        segments.append({'type': 'text', 'content': text[last:], 'display': False})
    return segments


def has_formula(text: str) -> bool:
    """判断文本中是否包含 $...$ 或 $$...$$ 公式"""
    return bool(_FORMULA_RE.search(text))


def render_formula(latex: str, display: bool = False,
                   font_size: int = 14, color: str = '#111111',
                   bg_color: str = '#FFFFFF'):
    """
    把一段 LaTeX 渲染成 PhotoImage。
    display=True 时字号稍大（块级公式）。
    失败时返回 None（调用方应降级显示原始文字）。

    注意：返回的 PhotoImage 对象必须由调用方持久保存引用，
    否则会被 GC 回收导致图片变空白。
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        fs = font_size * (1.4 if display else 1.0)

        # 第一次渲染：用于测量 bbox
        fig = plt.figure(figsize=(0.1, 0.1))
        fig.patch.set_facecolor(bg_color)
        t = fig.text(0.5, 0.5, f'${latex}$',
                     fontsize=fs,
                     color=color,
                     ha='center', va='center',
                     usetex=False)
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bbox = t.get_window_extent(renderer=renderer)
        plt.close(fig)

        # 根据实际尺寸重新建图
        pad_px = 6
        dpi = 100
        w_inch = max((bbox.width  + pad_px * 2) / dpi, 0.1)
        h_inch = max((bbox.height + pad_px * 2) / dpi, 0.1)

        fig2 = plt.figure(figsize=(w_inch, h_inch), dpi=dpi)
        fig2.patch.set_facecolor(bg_color)
        fig2.text(0.5, 0.5, f'${latex}$',
                  fontsize=fs,
                  color=color,
                  ha='center', va='center',
                  usetex=False)

        buf = io.BytesIO()
        fig2.savefig(buf, format='png', dpi=dpi,
                     facecolor=bg_color,
                     bbox_inches='tight',
                     pad_inches=pad_px / dpi)
        plt.close(fig2)
        buf.seek(0)

        img = Image.open(buf)
        return ImageTk.PhotoImage(img)

    except Exception:
        return None
