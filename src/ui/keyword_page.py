# 模块用途：关键词确认页面，展示 AI 推荐关键词，支持手动增删，确认后进入练习

import tkinter as tk
from tkinter import messagebox
import json
import threading
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_material, update_keywords
from src.core.ai_client import extract_keywords
from src.core.config import get_api_key

COLOR_BG     = '#FFFFFF'
COLOR_TEXT   = '#111111'
COLOR_SUBTLE = '#666666'
COLOR_BORDER = '#DDDDDD'
COLOR_INPUT  = '#F5F5F5'
COLOR_BTN_BG = '#111111'
COLOR_BTN_FG = '#FFFFFF'
COLOR_ERR    = '#B00020'
COLOR_TAG_BG = '#F0F0F0'
FONT_TITLE   = ('Microsoft YaHei', 16, 'bold')
FONT_BODY    = ('Microsoft YaHei', 13)
FONT_SMALL   = ('Microsoft YaHei', 11)
FONT_TAG     = ('Microsoft YaHei', 12)


class KeywordPage(tk.Frame):
    """关键词确认页面"""

    def __init__(self, master, material_id: int, on_start=None, on_back=None):
        """
        material_id : 当前资料的数据库 id
        on_start    : 确认关键词后进入练习的回调，传入 material_id
        on_back     : 返回资料列表的回调
        """
        super().__init__(master, bg=COLOR_BG)
        self.material_id = material_id
        self.on_start    = on_start
        self.on_back     = on_back
        self._keywords   = []   # 当前关键词列表

        self._build_ui()
        self._load_and_extract()

    # ──────────────────────────────────────────────
    # 构建界面
    # ──────────────────────────────────────────────
    def _build_ui(self):
        # ── 底部按钮（先 pack 确保始终可见）──
        btn_frame = tk.Frame(self, bg=COLOR_BG,
                             highlightbackground=COLOR_BORDER,
                             highlightthickness=1)
        btn_frame.pack(fill='x', side='bottom')

        self.start_btn = tk.Button(btn_frame, text='开始练习 →',
                                   font=FONT_BODY,
                                   bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                                   relief='flat', cursor='hand2',
                                   padx=24, pady=9,
                                   activebackground='#333333',
                                   state='disabled',
                                   command=self._on_start)
        self.start_btn.pack(side='right', padx=24, pady=12)

        tk.Button(btn_frame, text='← 返回',
                  font=FONT_BODY,
                  bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2',
                  padx=16, pady=9,
                  highlightbackground=COLOR_BORDER,
                  highlightthickness=1,
                  command=self._on_back
                  ).pack(side='left', padx=24, pady=12)

        # ── 标题 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))

        self.mat = get_material(self.material_id) or {}
        name = self.mat.get('name', '未知资料')

        tk.Label(top, text='确认关键词', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')
        tk.Label(top, text=f'资料：{name}',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(side='left', padx=16)

        # ── 重新提取按钮 ──
        self.re_btn = tk.Button(top, text='重新提取',
                                font=FONT_SMALL,
                                bg=COLOR_BG, fg=COLOR_TEXT,
                                relief='flat', cursor='hand2',
                                padx=12, pady=5,
                                highlightbackground=COLOR_BORDER,
                                highlightthickness=1,
                                state='disabled',
                                command=self._do_extract)
        self.re_btn.pack(side='right')

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── 状态提示 ──
        self.status_label = tk.Label(self, text='正在调用 AI 提取关键词，请稍候...',
                                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE)
        self.status_label.pack(pady=(16, 0))

        # ── 关键词标签区（可滚动）──
        tag_outer = tk.Frame(self, bg=COLOR_BG)
        tag_outer.pack(fill='both', expand=True, padx=32, pady=(8, 0))

        self.tag_canvas = tk.Canvas(tag_outer, bg=COLOR_BG, highlightthickness=0)
        tag_sb = tk.Scrollbar(tag_outer, orient='vertical',
                              command=self.tag_canvas.yview)
        self.tag_frame = tk.Frame(self.tag_canvas, bg=COLOR_BG)
        self.tag_frame.bind('<Configure>',
                            lambda e: self.tag_canvas.configure(
                                scrollregion=self.tag_canvas.bbox('all')))
        self.tag_canvas.create_window((0, 0), window=self.tag_frame, anchor='nw')
        self.tag_canvas.configure(yscrollcommand=tag_sb.set)
        tag_sb.pack(side='right', fill='y')
        self.tag_canvas.pack(side='left', fill='both', expand=True)
        self.tag_canvas.bind_all('<MouseWheel>',
                                 lambda e: self.tag_canvas.yview_scroll(
                                     int(-1 * e.delta / 120), 'units'))

        # ── 手动添加关键词 ──
        add_frame = tk.Frame(self, bg=COLOR_BG)
        add_frame.pack(fill='x', padx=32, pady=(12, 8))

        tk.Label(add_frame, text='手动添加：',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        self.add_var = tk.StringVar()
        add_entry = tk.Entry(add_frame, textvariable=self.add_var,
                             font=FONT_BODY, bg=COLOR_INPUT,
                             fg=COLOR_TEXT, relief='flat',
                             highlightbackground=COLOR_BORDER,
                             highlightthickness=1, width=16)
        add_entry.pack(side='left', ipady=5, padx=(0, 8))
        add_entry.bind('<Return>', lambda e: self._add_keyword())

        tk.Button(add_frame, text='添加',
                  font=FONT_BODY,
                  bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2',
                  padx=12, pady=5,
                  activebackground='#333333',
                  command=self._add_keyword
                  ).pack(side='left')

        tk.Label(add_frame,
                 text='点击关键词标签可删除',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(side='right')

    # ──────────────────────────────────────────────
    # 数据加载与 AI 提取
    # ──────────────────────────────────────────────
    def _load_and_extract(self):
        """如果资料已有关键词则直接展示，否则调用 AI 提取"""
        existing = self.mat.get('keywords', '[]')
        try:
            kws = json.loads(existing)
        except Exception:
            kws = []

        if kws:
            self._keywords = kws
            self._render_tags()
            self.status_label.config(text=f'已加载 {len(kws)} 个关键词，可手动调整后开始练习')
            self.start_btn.config(state='normal')
            self.re_btn.config(state='normal')
        else:
            self._do_extract()

    def _do_extract(self):
        """在后台线程调用 AI 提取关键词"""
        if not get_api_key():
            messagebox.showwarning('未设置 API Key',
                                   '请先前往「设置」页面填写 DeepSeek API Key')
            return

        self.status_label.config(text='正在调用 AI 提取关键词，请稍候...',
                                 fg=COLOR_SUBTLE)
        self.start_btn.config(state='disabled')
        self.re_btn.config(state='disabled')

        content = self.mat.get('content', '')

        def do():
            try:
                kws = extract_keywords(content)
                self.after(0, lambda: self._on_extract_done(kws))
            except Exception as e:
                self.after(0, lambda: self._on_extract_error(str(e)))

        threading.Thread(target=do, daemon=True).start()

    def _on_extract_done(self, keywords: list):
        self._keywords = keywords
        self._save_keywords()
        self._render_tags()
        self.status_label.config(
            text=f'AI 提取完成，共 {len(keywords)} 个关键词。点击标签可删除，也可手动添加。',
            fg=COLOR_TEXT)
        self.start_btn.config(state='normal')
        self.re_btn.config(state='normal')

    def _on_extract_error(self, msg: str):
        self.status_label.config(text=f'提取失败：{msg}', fg=COLOR_ERR)
        self.re_btn.config(state='normal')
        messagebox.showerror('提取失败', msg)

    # ──────────────────────────────────────────────
    # 关键词标签渲染
    # ──────────────────────────────────────────────
    def _render_tags(self):
        """重新渲染所有关键词标签"""
        for w in self.tag_frame.winfo_children():
            w.destroy()

        if not self._keywords:
            tk.Label(self.tag_frame, text='暂无关键词',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE
                     ).pack(pady=20)
            return

        # 流式布局：按行排列标签
        row_frame = None
        row_width  = 0
        max_width  = 700  # 每行最大宽度（近似值）

        for kw in self._keywords:
            tag_w = len(kw) * 15 + 32  # 估算标签宽度
            if row_frame is None or row_width + tag_w > max_width:
                row_frame = tk.Frame(self.tag_frame, bg=COLOR_BG)
                row_frame.pack(anchor='w', pady=4)
                row_width = 0

            tag = tk.Button(row_frame, text=f'{kw}  ✕',
                            font=FONT_TAG,
                            bg=COLOR_TAG_BG, fg=COLOR_TEXT,
                            relief='flat', cursor='hand2',
                            padx=10, pady=5,
                            highlightbackground=COLOR_BORDER,
                            highlightthickness=1,
                            activebackground='#FFE0E0',
                            command=lambda k=kw: self._remove_keyword(k))
            tag.pack(side='left', padx=(0, 6))
            row_width += tag_w + 6

    def _add_keyword(self):
        kw = self.add_var.get().strip()
        if not kw:
            return
        if kw in self._keywords:
            messagebox.showinfo('已存在', f'「{kw}」已在列表中')
            return
        self._keywords.append(kw)
        self.add_var.set('')
        self._save_keywords()
        self._render_tags()

    def _remove_keyword(self, kw: str):
        if kw in self._keywords:
            self._keywords.remove(kw)
            self._save_keywords()
            self._render_tags()
        if not self._keywords:
            self.start_btn.config(state='disabled')

    def _save_keywords(self):
        """将当前关键词列表保存到数据库"""
        update_keywords(self.material_id, json.dumps(self._keywords, ensure_ascii=False))

    # ──────────────────────────────────────────────
    # 导航事件
    # ──────────────────────────────────────────────
    def _on_start(self):
        if not self._keywords:
            messagebox.showwarning('关键词为空', '请至少保留一个关键词才能开始练习')
            return
        if self.on_start:
            self.on_start(self.material_id, self._keywords)

    def _on_back(self):
        if self.on_back:
            self.on_back()
