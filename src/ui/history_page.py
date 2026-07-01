# 模块用途：练习记录页，展示所有历史练习记录，按资料和时间分组
# 点击单条记录可进入详情，查看本次每题的对错明细

import tkinter as tk
from tkinter import messagebox
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_all_sessions, get_all_materials, get_session_detail



class HistoryPage(tk.Frame):

    def __init__(self, master):
        super().__init__(master, bg=COLOR_BG)
        self._filter_var = tk.StringVar(value='全部')
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # ── 滚轮系统：鼠标移到哪个滚动区就滚哪个，避免列表/详情两区冲突 ──
        self._setup_scroll_system()

        # ── 顶部（常驻）──
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
        tk.Label(self, text='💡 点击单条记录可查看每题对错；点击资料名可筛选；到期复习任务会在「我的资料」页面提醒',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=32, pady=(4, 0))

        # ── 列表视图容器（默认显示）──
        self._list_view = tk.Frame(self, bg=COLOR_BG)
        self._list_view.pack(fill='both', expand=True)

        # ── 详情视图容器（默认隐藏）──
        self._detail_view = tk.Frame(self, bg=COLOR_BG)

        # 筛选栏
        self._filter_frame = tk.Frame(self._list_view, bg=COLOR_BG)
        self._filter_frame.pack(fill='x', padx=32, pady=(10, 0))

        # 列表区
        wrapper = tk.Frame(self._list_view, bg=COLOR_BG)
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
        self._register_scroll(self._canvas)

    # ──────────────────────────────────────────────
    # 滚轮系统（多滚动区共存，互不冲突）
    # ──────────────────────────────────────────────
    def _setup_scroll_system(self):
        self._active_canvas = None
        self.bind_all('<MouseWheel>', self._on_mousewheel)

    def _register_scroll(self, canvas):
        canvas.bind('<Enter>',
                    lambda e, c=canvas: setattr(self, '_active_canvas', c))

    def _on_mousewheel(self, event):
        c = getattr(self, '_active_canvas', None)
        if c is not None:
            try:
                c.yview_scroll(int(-1 * event.delta / 120), 'units')
            except tk.TclError:
                pass

    # ──────────────────────────────────────────────
    # 视图切换
    # ──────────────────────────────────────────────
    def _show_list_view(self):
        self._detail_view.pack_forget()
        if not self._list_view.winfo_ismapped():
            self._list_view.pack(fill='both', expand=True)

    def refresh(self):
        """刷新筛选栏和列表（并切回列表视图）"""
        self._show_list_view()

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
                        highlightthickness=1, cursor='hand2')
        card.pack(fill='x', pady=(0, 6))

        inner = tk.Frame(card, bg=row_bg)
        inner.pack(fill='x', padx=16, pady=10)

        # 右侧：得分 + 查看提示（先 pack）
        right = tk.Frame(inner, bg=row_bg)
        right.pack(side='right')
        tk.Label(right,
                 text=f'{score:.0f}分',
                 font=FONT_BODY_B, bg=row_bg,
                 fg=COLOR_OK if is_ok else COLOR_ERR).pack(side='right')
        tk.Label(right, text='查看明细 ›',
                 font=FONT_SMALL, bg=row_bg, fg=COLOR_SUBTLE
                 ).pack(side='right', padx=(0, 12))

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

        # 整张卡片（含所有子组件）可点击 → 进入详情
        self._bind_click(card, s['id'])

    def _bind_click(self, widget, session_id: int):
        """给组件及其所有子孙绑定点击事件，整行任意位置都能点开详情"""
        widget.bind('<Button-1>',
                    lambda e, sid=session_id: self._show_detail(sid))
        for child in widget.winfo_children():
            self._bind_click(child, session_id)

    def _on_filter(self, name: str):
        self._filter_var.set(name)
        self.refresh()

    # ──────────────────────────────────────────────
    # 详情视图：单次练习的每题对错
    # ──────────────────────────────────────────────
    def _show_detail(self, session_id: int):
        data = get_session_detail(session_id)
        if not data:
            messagebox.showinfo('提示', '找不到该练习记录')
            return

        self._list_view.pack_forget()
        for w in self._detail_view.winfo_children():
            w.destroy()
        self._build_detail(data)
        self._detail_view.pack(fill='both', expand=True)

    def _build_detail(self, data: dict):
        dv = self._detail_view

        # 顶部：返回 + 标题
        head = tk.Frame(dv, bg=COLOR_BG)
        head.pack(fill='x', padx=32, pady=(16, 0))
        tk.Button(head, text='← 返回记录',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=12, pady=6,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._show_list_view).pack(side='left')

        tk.Label(dv,
                 text=f'{data.get("material_name", "")}  ›  {data.get("section_title", "")}',
                 font=FONT_BODY_B, bg=COLOR_BG, fg=COLOR_TEXT
                 ).pack(anchor='w', padx=32, pady=(12, 0))

        is_ok     = data['score'] >= 60
        mode_text = '严格模式' if data['mode'] == 'strict' else '智能模式'
        info_row  = tk.Frame(dv, bg=COLOR_BG)
        info_row.pack(anchor='w', padx=32, pady=(4, 0))
        tk.Label(info_row, text=f'{data["score"]:.0f}分',
                 font=FONT_BODY_B, bg=COLOR_BG,
                 fg=COLOR_OK if is_ok else COLOR_ERR).pack(side='left')
        tk.Label(info_row,
                 text=f'  ·  答对 {data["correct"]}/{data["total"]} 题  ·  '
                      f'{mode_text}  ·  {data["created_at"]}',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left')

        tk.Frame(dv, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))
        tk.Label(dv, text='答题明细',
                 font=FONT_BODY_B, bg=COLOR_BG, fg=COLOR_TEXT
                 ).pack(anchor='w', padx=32, pady=(12, 0))

        detail = data.get('detail', [])
        if not detail:
            tk.Label(dv,
                     text='本次练习没有保存答题明细（可能是较早版本的旧记录）',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(pady=40)
            return

        # ── 明细滚动列表 ──
        outer = tk.Frame(dv, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=(8, 16))

        sb = tk.Scrollbar(outer, orient='vertical')
        sb.pack(side='right', fill='y')

        d_canvas = tk.Canvas(outer, bg=COLOR_BG,
                             highlightthickness=0,
                             yscrollcommand=sb.set)
        d_canvas.pack(side='left', fill='both', expand=True)
        sb.config(command=d_canvas.yview)

        d_frame = tk.Frame(d_canvas, bg=COLOR_BG)
        d_win = d_canvas.create_window((0, 0), window=d_frame, anchor='nw')
        d_canvas.bind('<Configure>',
                      lambda e: d_canvas.itemconfig(d_win, width=e.width))
        d_frame.bind('<Configure>',
                     lambda e: d_canvas.configure(scrollregion=d_canvas.bbox('all')))
        self._register_scroll(d_canvas)

        for r in detail:
            self._build_detail_row(d_frame, r)

    def _build_detail_row(self, parent, r: dict):
        kw      = r.get('keyword', '')
        answer  = r.get('answer', '') or '（未填写）'
        correct = r.get('correct', False)
        row_bg  = COLOR_OK_BG if correct else COLOR_ERR_BG
        row_fg  = COLOR_OK    if correct else COLOR_ERR

        card = tk.Frame(parent, bg=row_bg,
                        highlightbackground=COLOR_BORDER,
                        highlightthickness=1)
        card.pack(fill='x', pady=(0, 6))

        inner = tk.Frame(card, bg=row_bg)
        inner.pack(fill='x', padx=16, pady=10)

        tk.Label(inner, text='✓' if correct else '✗',
                 font=FONT_BODY_B, bg=row_bg, fg=row_fg, width=2).pack(side='left')
        tk.Label(inner, text=f'答案：{kw}',
                 font=FONT_BODY_B, bg=row_bg, fg=COLOR_TEXT
                 ).pack(side='left', padx=(8, 0))
        tk.Label(inner, text=f'你填的：{answer}',
                 font=FONT_BODY, bg=row_bg, fg=row_fg
                 ).pack(side='left', padx=(20, 0))
