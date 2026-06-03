# 模块用途：遮盖模式页，逐块展示内容，答案块默认折叠，点击展开对照

import tkinter as tk
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_section

COLOR_COVER   = '#E8E8E8'      # 折叠时遮盖块的背景色
COLOR_ANS_BG  = '#F0FAF0'      # 展开后答案块背景（浅绿提示）
COLOR_ANS_BD  = '#B8DEB8'      # 展开后答案块边框
FONT_COVER    = ('Microsoft YaHei', 12)


class CoverPage(tk.Frame):

    def __init__(self, master, section_id: int, on_back=None):
        super().__init__(master, bg=COLOR_BG)
        self.section_id = section_id
        self.on_back    = on_back
        self._sec       = get_section(section_id) or {}
        self._blocks    = self._sec.get('blocks', [])

        # 每个答案块的折叠状态：index -> bool（True=折叠）
        self._collapsed = {}
        # 每个答案块对应的遮盖 frame 和内容 frame
        self._cover_frames   = {}
        self._content_frames = {}
        self._text_widgets   = []

        self._build_ui()
        self.after(100, self._fix_all_heights)

    def _build_ui(self):
        # ── 底部操作栏（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='全部展开',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._expand_all).pack(side='left', padx=24, pady=12)

        tk.Button(bottom, text='全部折叠',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._collapse_all).pack(side='left', padx=(0, 8), pady=12)

        tk.Button(bottom, text='← 返回',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=9,
                  activebackground='#333333',
                  command=self._on_back).pack(side='right', padx=24, pady=12)

        # ── 顶部标题 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(20, 0))

        tk.Label(top, text='遮盖模式', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        ans_count = sum(1 for b in self._blocks if b.get('type') == 'answer')
        tk.Label(top,
                 text=f'{self._sec.get("title", "")}  ·  共 {ans_count} 个答案块',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(side='left', padx=16)

        tk.Label(self,
                 text='点击灰色遮盖块展开答案，再次点击折叠',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=32, pady=(4, 0))

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
        self._canvas.itemconfig(self._canvas_win, width=event.width)
        self.after(50, self._fix_all_heights)

    def _render_content(self):
        for w in self._text_frame.winfo_children():
            w.destroy()
        self._text_widgets.clear()
        self._collapsed.clear()
        self._cover_frames.clear()
        self._content_frames.clear()

        ans_idx = 0
        for block in self._blocks:
            btype   = block.get('type', 'text')
            content = block.get('content', '').strip()
            if not content:
                continue

            if btype == 'question':
                self._render_plain(content, bg=COLOR_Q_BG, border=True)
            elif btype == 'answer':
                self._render_answer_block(content, ans_idx)
                ans_idx += 1
            else:
                self._render_plain(content, bg=COLOR_BG, border=False)

    # ── 普通段落 ──
    def _render_plain(self, content: str, bg: str, border: bool):
        frame = tk.Frame(self._text_frame, bg=bg,
                         highlightbackground=COLOR_BORDER if border else bg,
                         highlightthickness=1 if border else 0)
        frame.pack(fill='x', pady=(0, 6))

        txt = tk.Text(frame, font=FONT_BODY, bg=bg, fg=COLOR_TEXT,
                      relief='flat', wrap='word',
                      padx=10, pady=6,
                      cursor='arrow', height=1)
        txt.insert('1.0', content)
        txt.config(state='disabled')
        txt.pack(fill='x')
        self._text_widgets.append(txt)

    # ── 答案块（可折叠）──
    def _render_answer_block(self, content: str, idx: int):
        """
        外层 wrapper 包含两个子 frame：
          - cover_frame：折叠时显示的灰色遮盖条
          - content_frame：展开后显示的实际内容
        默认折叠（只显示 cover_frame）
        """
        self._collapsed[idx] = True

        wrapper = tk.Frame(self._text_frame, bg=COLOR_BG)
        wrapper.pack(fill='x', pady=(0, 6))

        # ── 遮盖条 ──
        cover_frame = tk.Frame(wrapper, bg=COLOR_COVER,
                               highlightbackground=COLOR_BORDER,
                               highlightthickness=1,
                               cursor='hand2')
        cover_frame.pack(fill='x')

        cover_inner = tk.Frame(cover_frame, bg=COLOR_COVER)
        cover_inner.pack(fill='x', padx=12, pady=10)

        tk.Label(cover_inner,
                 text='▶  答案已遮盖，点击展开',
                 font=FONT_COVER, bg=COLOR_COVER, fg=COLOR_SUBTLE,
                 cursor='hand2').pack(side='left')

        # ── 实际内容 ──
        content_frame = tk.Frame(wrapper, bg=COLOR_ANS_BG,
                                 highlightbackground=COLOR_ANS_BD,
                                 highlightthickness=1)
        # 默认不显示

        txt = tk.Text(content_frame, font=FONT_BODY,
                      bg=COLOR_ANS_BG, fg=COLOR_TEXT,
                      relief='flat', wrap='word',
                      padx=10, pady=8,
                      cursor='arrow', height=1)
        txt.insert('1.0', content)
        txt.config(state='disabled')
        txt.pack(fill='x')
        self._text_widgets.append(txt)

        self._cover_frames[idx]   = cover_frame
        self._content_frames[idx] = content_frame

        # 绑定点击事件（遮盖条上的所有控件）
        for widget in [cover_frame, cover_inner] + list(cover_inner.winfo_children()):
            widget.bind('<Button-1>', lambda e, i=idx: self._toggle(i))

    def _toggle(self, idx: int):
        """切换第 idx 个答案块的折叠状态"""
        if self._collapsed[idx]:
            # 展开
            self._cover_frames[idx].pack_forget()
            self._content_frames[idx].pack(fill='x')
            self._collapsed[idx] = False
        else:
            # 折叠
            self._content_frames[idx].pack_forget()
            self._cover_frames[idx].pack(fill='x')
            self._collapsed[idx] = True
        self.after(50, self._fix_all_heights)

    def _expand_all(self):
        for idx in list(self._collapsed.keys()):
            if self._collapsed[idx]:
                self._cover_frames[idx].pack_forget()
                self._content_frames[idx].pack(fill='x')
                self._collapsed[idx] = False
        self.after(50, self._fix_all_heights)

    def _collapse_all(self):
        for idx in list(self._collapsed.keys()):
            if not self._collapsed[idx]:
                self._content_frames[idx].pack_forget()
                self._cover_frames[idx].pack(fill='x')
                self._collapsed[idx] = True
        self.after(50, self._fix_all_heights)

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

    def _on_back(self):
        if self.on_back:
            self.on_back()
