# 模块用途：章节列表页，展示资料的所有小节，点击进入练习或校对

import tkinter as tk
from tkinter import messagebox
import json
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_material, get_sections_by_material, get_section



class SectionListPage(tk.Frame):

    def __init__(self, master, material_id: int,
                 on_practice=None, on_review=None,
                 on_reanalyze=None, on_back=None, on_cover=None, on_quiz=None):
        super().__init__(master, bg=COLOR_BG)
        self.material_id  = material_id
        self.on_practice  = on_practice
        self.on_review    = on_review
        self.on_reanalyze = on_reanalyze
        self.on_back      = on_back
        self.on_cover     = on_cover
        self.on_quiz      = on_quiz
        self._mat         = get_material(material_id) or {}
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # ── 顶部 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))

        tk.Label(top, text=self._mat.get('name', ''),
                 font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        # 右侧按钮先 pack
        tk.Button(top, text='← 返回',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=12, pady=6,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_back).pack(side='right', padx=(8, 0))

        tk.Button(top, text='重新分析',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=12, pady=6,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_reanalyze).pack(side='right')

        tk.Button(top, text='综合测验 ✎',
                  font=FONT_SMALL, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=12, pady=6,
                  activebackground='#333333',
                  command=self._on_quiz).pack(side='right', padx=(0, 8))

        tk.Label(self, text='选择一个小节开始练习',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=32, pady=(4, 0))

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── 提示栏 ──
        hint = tk.Frame(self, bg='#FFFDF0',
                        highlightbackground='#E8D870', highlightthickness=1)
        hint.pack(fill='x', padx=32, pady=(10, 0))
        tk.Label(hint,
                 text='💡 软件只在答案部分挖空。如发现问答识别有误，可点「校对标注」手动修正。',
                 font=FONT_SMALL, bg='#FFFDF0', fg=COLOR_WARN,
                 justify='left').pack(anchor='w', padx=12, pady=8)

        # ── 滚动列表 ──
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
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor='nw')

        # 关键：列表宽度跟随 canvas 宽度变化
        self._canvas.bind('<Configure>', self._on_canvas_resize)
        self._list_frame.bind('<Configure>',
                              lambda e: self._canvas.configure(
                                  scrollregion=self._canvas.bbox('all')))
        self._canvas.bind_all('<MouseWheel>',
                              lambda e: self._canvas.yview_scroll(
                                  int(-1 * e.delta / 120), 'units'))

    def _on_canvas_resize(self, event):
        """让内部 frame 始终撑满 canvas 宽度"""
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def refresh(self):
        for w in self._list_frame.winfo_children():
            w.destroy()

        sections = get_sections_by_material(self.material_id)
        if not sections:
            tk.Label(self._list_frame,
                     text='暂无章节数据，请重新分析',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE
                     ).pack(pady=40)
            return

        for sec in sections:
            self._build_card(sec)

    def _build_card(self, sec: dict):
        try:
            kw_count = len(json.loads(sec.get('keywords', '[]')))
        except Exception:
            kw_count = 0
        reviewed = sec.get('reviewed', 0)

        card = tk.Frame(self._list_frame, bg=COLOR_BG,
                        highlightbackground=COLOR_BORDER,
                        highlightthickness=1)
        card.pack(fill='x', pady=(0, 8), padx=2)

        inner = tk.Frame(card, bg=COLOR_BG)
        inner.pack(fill='x', padx=16, pady=12)

        # ── 右侧按钮先 pack ──
        btn_frame = tk.Frame(inner, bg=COLOR_BG)
        btn_frame.pack(side='right')

        tk.Button(btn_frame, text='开始练习',
                  font=FONT_SMALL, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=16, pady=7,
                  activebackground='#333333',
                  command=lambda sid=sec['id']: self._on_practice(sid)
                  ).pack(side='left')

        tk.Button(btn_frame, text='遮盖模式',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=12, pady=7,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=lambda sid=sec['id']: self._on_cover(sid)
                  ).pack(side='left', padx=(8, 0))

        tk.Button(btn_frame, text='校对标注',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=12, pady=7,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=lambda sid=sec['id']: self._on_review(sid)
                  ).pack(side='left', padx=(8, 0))

        # ── 左侧文字后 pack ──
        left = tk.Frame(inner, bg=COLOR_BG)
        left.pack(side='left', fill='x', expand=True)

        tk.Label(left, text=sec['title'],
                 font=FONT_BODY_B, bg=COLOR_BG,
                 fg=COLOR_TEXT, anchor='w').pack(anchor='w')

        meta = tk.Frame(left, bg=COLOR_BG)
        meta.pack(anchor='w', pady=(4, 0))

        tk.Label(meta, text=f'关键词 {kw_count} 个',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left')

        if reviewed:
            tk.Label(meta, text='  ✓ 已校对',
                     font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_OK).pack(side='left')
        else:
            tk.Label(meta, text='  · AI 自动标注',
                     font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left')

    def _on_quiz(self):
        if self.on_quiz:
            self.on_quiz(self.material_id)

    def _on_practice(self, section_id: int):
        sec = get_section(section_id)
        if not sec:
            messagebox.showerror('错误', '找不到该小节数据')
            return
        if not sec.get('keywords'):
            messagebox.showwarning('无关键词',
                                   '该小节没有关键词，无法练习。\n'
                                   '请先点「校对标注」添加关键词，或重新分析文档。')
            return
        if self.on_practice:
            self.on_practice(section_id)

    def _on_cover(self, section_id: int):
        sec = get_section(section_id)
        if not sec:
            messagebox.showerror('错误', '找不到该小节数据')
            return
        if not sec.get('blocks'):
            messagebox.showwarning('无内容', '该小节没有内容，无法使用遮盖模式。')
            return
        if self.on_cover:
            self.on_cover(section_id)

    def _on_review(self, section_id: int):
        if self.on_review:
            self.on_review(section_id)

    def _on_reanalyze(self):
        ok = messagebox.askyesno('重新分析',
                                 '重新分析将清空现有章节数据和关键词。\n确定继续吗？')
        if ok and self.on_reanalyze:
            self.on_reanalyze(self.material_id)

    def _on_back(self):
        if self.on_back:
            self.on_back()
