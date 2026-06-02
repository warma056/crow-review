# 模块用途：填空练习页，只在「答案」段落中挖空，问题完整显示
# 支持数学公式渲染（$...$  行内公式 / $$...$$ 块级公式）

import tkinter as tk
from tkinter import ttk, messagebox
import re
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_section
from src.core.config import load_config
from src.core.formula_renderer import split_formula_segments, has_formula, render_formula

COLOR_BG     = '#FFFFFF'
COLOR_TEXT   = '#111111'
COLOR_SUBTLE = '#666666'
COLOR_BORDER = '#DDDDDD'
COLOR_BTN_BG = '#111111'
COLOR_BTN_FG = '#FFFFFF'
COLOR_BLANK  = '#E8E8E8'
COLOR_Q_BG   = '#F5F5F5'
FONT_TITLE   = ('Microsoft YaHei', 16, 'bold')
FONT_BODY    = ('Microsoft YaHei', 13)
FONT_SMALL   = ('Microsoft YaHei', 11)


class PracticePage(tk.Frame):

    def __init__(self, master, section_id: int, on_finish=None, on_back=None):
        super().__init__(master, bg=COLOR_BG)
        self.section_id   = section_id
        self.on_finish    = on_finish
        self.on_back      = on_back
        self._sec         = get_section(section_id) or {}
        self._keywords    = self._sec.get('keywords', [])
        self._blocks      = self._sec.get('blocks', [])
        self._entries     = {}
        self._mode_var    = tk.StringVar(value=load_config().get('judge_mode', 'strict'))
        self._text_widgets   = []   # 所有 Text 组件，用于事后调整高度
        self._formula_images = []   # 持久保存公式 PhotoImage，防止被 GC 回收变空白

        self._build_ui()
        # 窗口完全渲染后再调整所有 Text 高度
        self.after(100, self._fix_all_heights)

    def _build_ui(self):
        # ── 底部操作栏 ──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        mode_f = tk.Frame(bottom, bg=COLOR_BG)
        mode_f.pack(side='left', padx=24, pady=12)
        tk.Label(mode_f, text='判题模式：',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left')
        for text, val in [('严格（完全匹配）', 'strict'), ('智能（语义判断）', 'smart')]:
            tk.Radiobutton(mode_f, text=text, variable=self._mode_var,
                           value=val, font=FONT_SMALL,
                           bg=COLOR_BG, fg=COLOR_TEXT,
                           activebackground=COLOR_BG,
                           selectcolor=COLOR_BG).pack(side='left', padx=(0, 12))

        self._submit_btn = tk.Button(
            bottom, text='提交答案',
            font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
            relief='flat', cursor='hand2', padx=24, pady=9,
            activebackground='#333333', command=self._on_submit)
        self._submit_btn.pack(side='right', padx=24, pady=12)

        tk.Button(bottom, text='← 返回',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_back).pack(side='right', padx=(0, 8), pady=12)

        # ── 顶部标题 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(20, 0))
        tk.Label(top, text='填空练习', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')
        tk.Label(top,
                 text=f'{self._sec.get("title", "")}  ·  共 {len(self._keywords)} 个空格',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(side='left', padx=16)
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── 正文滚动区 ──
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=12)

        scrollbar = tk.Scrollbar(outer, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self._canvas = tk.Canvas(outer, bg=COLOR_BG,
                                 highlightthickness=0,
                                 yscrollcommand=scrollbar.set)
        self._canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self._canvas.yview)

        self._text_frame = tk.Frame(self._canvas, bg=COLOR_BG)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._text_frame, anchor='nw')

        self._canvas.bind('<Configure>', self._on_canvas_resize)
        self._text_frame.bind('<Configure>',
                              lambda e: self._canvas.configure(
                                  scrollregion=self._canvas.bbox('all')))
        self._canvas.bind_all('<MouseWheel>',
                              lambda e: self._canvas.yview_scroll(
                                  int(-1 * e.delta / 120), 'units'))

        self._render_content()

    def _on_canvas_resize(self, event):
        """canvas 宽度变化时，同步更新内部 frame 宽度并重算 Text 高度"""
        self._canvas.itemconfig(self._canvas_win, width=event.width)
        self.after(50, self._fix_all_heights)

    def _render_content(self):
        for w in self._text_frame.winfo_children():
            w.destroy()
        self._entries.clear()
        self._text_widgets.clear()
        self._formula_images.clear()

        rendered_kws = set()
        for block in self._blocks:
            btype   = block.get('type', 'text')
            content = block.get('content', '').strip()
            if not content:
                continue
            if btype == 'question':
                self._render_plain(content, bg=COLOR_Q_BG, border=True)
            elif btype == 'answer':
                self._render_answer(content, rendered_kws)
            else:
                self._render_plain(content, bg=COLOR_BG, border=False)

    # ──────────────────────────────────────────────
    # 普通段落：只读 Text，自动换行，支持公式渲染
    # ──────────────────────────────────────────────
    def _render_plain(self, content: str, bg: str, border: bool):
        frame = tk.Frame(self._text_frame, bg=bg,
                         highlightbackground=COLOR_BORDER if border else bg,
                         highlightthickness=1 if border else 0)
        frame.pack(fill='x', pady=(0, 6))

        txt = tk.Text(frame, font=FONT_BODY, bg=bg, fg=COLOR_TEXT,
                      relief='flat', wrap='word',
                      padx=10, pady=6,
                      cursor='arrow',
                      height=1)
        txt.pack(fill='x')

        if has_formula(content):
            self._insert_with_formula(txt, content, bg)
        else:
            txt.insert('1.0', content)

        txt.config(state='disabled')
        self._text_widgets.append(txt)

    # ──────────────────────────────────────────────
    # 答案段落：Text 混排嵌入 Entry，支持公式渲染
    # ──────────────────────────────────────────────
    def _render_answer(self, content: str, rendered_kws: set):
        frame = tk.Frame(self._text_frame, bg=COLOR_BG)
        frame.pack(fill='x', pady=(0, 6))

        txt = tk.Text(frame, font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                      relief='flat', wrap='word',
                      padx=6, pady=4,
                      cursor='arrow',
                      spacing1=2, spacing3=4,
                      height=1)
        txt.pack(fill='x')

        # 分割内容并插入
        pending  = [kw for kw in self._keywords if kw not in rendered_kws]
        segments = self._segment_text(content, pending)

        for seg in segments:
            if seg['type'] == 'text':
                if has_formula(seg['content']):
                    self._insert_with_formula(txt, seg['content'], COLOR_BG)
                else:
                    txt.insert('end', seg['content'])
            else:
                kw    = seg['content']
                rendered_kws.add(kw)
                width = max(len(kw) + 2, 6)
                entry = tk.Entry(txt,
                                 font=FONT_BODY,
                                 bg=COLOR_BLANK, fg=COLOR_TEXT,
                                 relief='flat',
                                 highlightbackground=COLOR_BORDER,
                                 highlightthickness=1,
                                 width=width,
                                 justify='center')
                txt.window_create('end', window=entry, padx=3, pady=3)
                self._entries[kw] = entry

        txt.config(state='disabled')
        # 嵌入的 Entry 需要单独恢复为可输入
        for entry in self._entries.values():
            entry.config(state='normal')

        self._text_widgets.append(txt)

    # ──────────────────────────────────────────────
    # 统一修正所有 Text 组件高度
    # 原理：让 Text 自己 count 换行后的实际显示行数
    # ──────────────────────────────────────────────
    def _fix_all_heights(self):
        for txt in self._text_widgets:
            try:
                txt.update_idletasks()
                lines = txt.count('1.0', 'end', 'displaylines')
                if lines and lines[0]:
                    txt.config(height=lines[0])
                else:
                    n = int(txt.index('end-1c').split('.')[0])
                    txt.config(height=max(n, 1))
            except Exception:
                pass
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    # ──────────────────────────────────────────────
    # 公式混排：把含公式的文本插入 Text 组件
    # ──────────────────────────────────────────────
    def _insert_with_formula(self, txt: tk.Text, content: str, bg: str):
        """把含公式的文本插入 Text 组件，公式渲染为图片嵌入，失败则降级显示原文。"""
        segments = split_formula_segments(content)
        for seg in segments:
            if seg['type'] == 'text':
                txt.insert('end', seg['content'])
            else:
                img = render_formula(
                    seg['content'],
                    display=seg['display'],
                    font_size=13,
                    color=COLOR_TEXT,
                    bg_color=bg
                )
                if img:
                    # 必须持久保存引用，否则被 GC 回收变空白
                    self._formula_images.append(img)
                    lbl = tk.Label(txt, image=img, bg=bg, borderwidth=0)
                    pady = 6 if seg['display'] else 2
                    txt.window_create('end', window=lbl, padx=2, pady=pady)
                else:
                    # 渲染失败，降级显示原始文字
                    raw = f'$${seg["content"]}$$' if seg['display'] else f'${seg["content"]}$'
                    txt.insert('end', raw)

    def _segment_text(self, text: str, keywords: list) -> list:
        if not keywords:
            return [{'type': 'text', 'content': text}]
        positions = []
        for kw in keywords:
            m = re.search(re.escape(kw), text)
            if m:
                positions.append((m.start(), m.end(), kw))
        if not positions:
            return [{'type': 'text', 'content': text}]
        positions.sort(key=lambda x: x[0])
        filtered, last_end = [], 0
        for start, end, kw in positions:
            if start >= last_end:
                filtered.append((start, end, kw))
                last_end = end
        segments, cursor = [], 0
        for start, end, kw in filtered:
            if cursor < start:
                segments.append({'type': 'text', 'content': text[cursor:start]})
            segments.append({'type': 'blank', 'content': kw})
            cursor = end
        if cursor < len(text):
            segments.append({'type': 'text', 'content': text[cursor:]})
        return segments

    def _on_submit(self):
        mode = self._mode_var.get()
        if mode == 'smart':
            # FIX: Ollama 不需要 API Key，只有 DeepSeek 才检查
            from src.core.config import get_api_key, load_config
            cfg = load_config()
            if cfg.get('api_provider', 'deepseek') != 'ollama' and not get_api_key():
                messagebox.showwarning('未设置 API Key',
                                       '智能模式需要调用 AI 判题，请先在「设置」中填写 DeepSeek API Key')
                return
            self._submit_smart()
        else:
            self._submit_strict()

    def _submit_strict(self):
        results = []
        for kw, entry in self._entries.items():
            ans = entry.get().strip()
            results.append({'keyword': kw, 'answer': ans, 'correct': ans == kw})
        if self.on_finish:
            self.on_finish(self.section_id, results, 'strict')

    def _submit_smart(self):
        import threading
        from src.core.ai_client import judge_answer
        answers = {kw: entry.get().strip() for kw, entry in self._entries.items()}
        self._submit_btn.config(state='disabled', text='AI 判题中...')

        def do():
            results = []
            for kw, ans in answers.items():
                try:
                    correct = judge_answer(kw, ans)
                except Exception:
                    correct = (ans == kw)
                results.append({'keyword': kw, 'answer': ans, 'correct': correct})
            self.after(0, lambda: self.on_finish(self.section_id, results, 'smart')
                       if self.on_finish else None)

        threading.Thread(target=do, daemon=True).start()

    def _on_back(self):
        if self.on_back:
            self.on_back()
