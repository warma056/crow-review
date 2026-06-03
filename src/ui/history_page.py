# 模块用途：练习记录页，展示所有历史练习记录，按资料和时间分组

import tkinter as tk
from tkinter import messagebox
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_all_sessions, get_all_materials



class HistoryPage(tk.Frame):

    def __init__(self, master):
        super().__init__(master, bg=COLOR_BG)
        self._filter_var = tk.StringVar(value='全部')
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # ── 顶部 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))

        tk.Label(top, text='练习记录',
                 font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        # 刷新按钮
        tk.Button(top, text='刷新',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=12, pady=6,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self.refresh).pack(side='right')

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(14, 0))
        tk.Label(self, text='💡 点击资料名可筛选记录，到期复习任务会在「我的资料」页面提醒',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=32, pady=(4, 0))


        # ── 筛选栏 ──
        self._filter_frame = tk.Frame(self, bg=COLOR_BG)
        self._filter_frame.pack(fill='x', padx=32, pady=(10, 0))

        # ── 列表区 ──
        wrapper = tk.Frame(self, bg=COLOR_BG)
        wrapper.pack(fill='both', expand=True, padx=32, pady=12)

        scrollbar = tk.Scrollbar(wrapper, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self._canvas = tk.Canvas(wrapper, bg=COLOR_BG,
                                 highlightthickness=0,
                                 yscrollcommand=scrollbar.set)
        self._canvas.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self._canvas.yview)

        self._list_frame = tk.Frame(self._canvas, bg=COLOR_BG)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor='nw')

        self._canvas.bind('<Configure>',
                          lambda e: self._canvas.itemconfig(
                              self._canvas_win, width=e.width))
        self._list_frame.bind('<Configure>',
                              lambda e: self._canvas.configure(
                                  scrollregion=self._canvas.bbox('all')))
        self._canvas.bind_all('<MouseWheel>',
                              lambda e: self._canvas.yview_scroll(
                                  int(-1 * e.delta / 120), 'units'))

    def refresh(self):
        """刷新筛选栏和列表"""
        sessions  = get_all_sessions()
        materials = get_all_materials()

        # 更新筛选按钮
        for w in self._filter_frame.winfo_children():
            w.destroy()

        tk.Label(self._filter_frame, text='筛选：',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left')

        mat_names = ['全部'] + [m['name'] for m in materials]
        for name in mat_names:
            is_sel = (self._filter_var.get() == name)
            btn = tk.Button(self._filter_frame, text=name,
                            font=FONT_SMALL,
                            bg=COLOR_BTN_BG if is_sel else COLOR_BG,
                            fg=COLOR_BTN_FG if is_sel else COLOR_TEXT,
                            relief='flat', cursor='hand2',
                            padx=10, pady=4,
                            highlightbackground=COLOR_BORDER,
                            highlightthickness=1,
                            command=lambda n=name: self._on_filter(n))
            btn.pack(side='left', padx=(0, 6))

        # 过滤数据
        if self._filter_var.get() != '全部':
            sessions = [s for s in sessions
                        if s.get('material_name') == self._filter_var.get()]

        # 更新列表
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not sessions:
            tk.Label(self._list_frame,
                     text='还没有练习记录',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE
                     ).pack(pady=60)
            return

        # 统计数据
        avg_score = sum(s['score'] for s in sessions) / len(sessions)
        stat_bar = tk.Frame(self._list_frame, bg='#F8F8F8',
                            highlightbackground=COLOR_BORDER,
                            highlightthickness=1)
        stat_bar.pack(fill='x', pady=(0, 12))

        tk.Label(stat_bar,
                 text=f'共 {len(sessions)} 次练习  ·  平均得分 {avg_score:.0f} 分',
                 font=FONT_SMALL, bg='#F8F8F8', fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=16, pady=8)

        for s in sessions:
            self._build_row(s)

    def _build_row(self, s: dict):
        score   = s['score']
        correct = s['correct']
        total   = s['total']
        is_ok   = score >= 60
        row_bg  = COLOR_OK_BG if is_ok else COLOR_ERR_BG

        card = tk.Frame(self._list_frame, bg=row_bg,
                        highlightbackground=COLOR_BORDER,
                        highlightthickness=1)
        card.pack(fill='x', pady=(0, 6))

        inner = tk.Frame(card, bg=row_bg)
        inner.pack(fill='x', padx=16, pady=10)

        # 右侧得分（先 pack）
        score_label = tk.Label(inner,
                               text=f'{score:.0f}分',
                               font=FONT_BODY_B, bg=row_bg,
                               fg=COLOR_OK if is_ok else COLOR_ERR)
        score_label.pack(side='right')

        # 左侧信息
        left = tk.Frame(inner, bg=row_bg)
        left.pack(side='left', fill='x', expand=True)

        # 资料名 + 小节
        tk.Label(left,
                 text=f'{s.get("material_name", "")}  ›  {s.get("section_title", "")}',
                 font=FONT_BODY_B, bg=row_bg, fg=COLOR_TEXT,
                 anchor='w').pack(anchor='w')

        # 时间 + 答对数 + 模式
        mode_text = '严格模式' if s['mode'] == 'strict' else '智能模式'
        tk.Label(left,
                 text=f'{s["created_at"]}  ·  答对 {correct}/{total} 题  ·  {mode_text}',
                 font=FONT_SMALL, bg=row_bg, fg=COLOR_SUBTLE,
                 anchor='w').pack(anchor='w', pady=(3, 0))

    def _on_filter(self, name: str):
        self._filter_var.set(name)
        self.refresh()
