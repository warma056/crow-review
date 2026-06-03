# 模块用途：资料列表页面，展示所有已保存资料，支持进入练习或删除

import tkinter as tk
from tkinter import messagebox
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_all_materials, delete_material, get_due_reminders

# 颜色常量
COLOR_HOVER   = '#F5F5F5'


class MaterialListPage(tk.Frame):
    """资料列表页面"""

    def __init__(self, master, on_import=None, on_select=None, on_section=None):
        """
        on_import  : 点击「导入新资料」时的回调
        on_select  : 点击某条资料「开始练习」时的回调，传入 material_id
        on_section : 点击「今日待复习」里某个小节时的回调，传入 material_id
        """
        super().__init__(master, bg=COLOR_BG)
        self.on_import  = on_import
        self.on_select  = on_select
        self.on_section = on_section
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # ── 标题 + 导入按钮 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))

        tk.Label(top, text='我的资料', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        tk.Button(top, text='＋ 导入新资料',
                  font=FONT_BODY,
                  bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2',
                  padx=16, pady=6,
                  activebackground='#333333',
                  command=self._on_import
                  ).pack(side='right')

        # ── 分割线 ──
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(14, 0))

        # ── 今日待复习提示栏 ──
        self._due_frame = tk.Frame(self, bg=COLOR_BG)
        self._due_frame.pack(fill='x', padx=32, pady=(0, 0))

        # ── 列表滚动区域 ──
        container = tk.Frame(self, bg=COLOR_BG)
        container.pack(fill='both', expand=True, padx=32, pady=16)

        canvas = tk.Canvas(container, bg=COLOR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient='vertical',
                                 command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg=COLOR_BG)

        self.list_frame.bind('<Configure>',
                             lambda e: canvas.configure(
                                 scrollregion=canvas.bbox('all')))

        canvas.create_window((0, 0), window=self.list_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        # 鼠标滚轮支持
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(
                            int(-1 * (e.delta / 120)), 'units'))

        self._canvas = canvas

    def refresh(self):
        """刷新列表，从数据库重新读取"""
        # 渲染今日待复习
        for w in self._due_frame.winfo_children():
            w.destroy()
        due = get_due_reminders()
        if due:
            banner = tk.Frame(self._due_frame, bg='#FFF5F5',
                              highlightbackground='#FFCCCC',
                              highlightthickness=1)
            banner.pack(fill='x', pady=(12, 0))
            header = tk.Frame(banner, bg='#FFF5F5')
            header.pack(fill='x', padx=14, pady=(10, 4))
            tk.Label(header,
                     text=f'🔴 今日待复习  共 {len(due)} 个小节',
                     font=('Microsoft YaHei', 12, 'bold'),
                     bg='#FFF5F5', fg=COLOR_ERR).pack(side='left')
            for item in due:
                row = tk.Frame(banner, bg='#FFF5F5')
                row.pack(fill='x', padx=14, pady=(0, 6))
                tk.Label(row,
                         text=f'· {item["material_name"]} › {item["section_title"]}',
                         font=('Microsoft YaHei', 11),
                         bg='#FFF5F5', fg=COLOR_TEXT).pack(side='left')
                tk.Button(row, text='去复习 →',
                          font=('Microsoft YaHei', 11),
                          bg='#FFF5F5', fg=COLOR_ERR,
                          relief='flat', cursor='hand2',
                          command=lambda mid=item['material_id']: self._on_section(mid)
                          ).pack(side='left', padx=(12, 0))

        # 渲染资料列表
        for w in self.list_frame.winfo_children():
            w.destroy()

        materials = get_all_materials()

        if not materials:
            tk.Label(self.list_frame,
                     text='还没有资料，点击右上角「导入新资料」开始吧',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE
                     ).pack(pady=60)
            return

        for mat in materials:
            self._build_item(mat)

    def _build_item(self, mat: dict):
        """构建单条资料卡片"""
        card = tk.Frame(self.list_frame, bg=COLOR_BG,
                        highlightbackground=COLOR_BORDER,
                        highlightthickness=1)
        card.pack(fill='x', pady=(0, 10))

        inner = tk.Frame(card, bg=COLOR_BG)
        inner.pack(fill='x', padx=16, pady=12)

        # 左侧：名称 + 时间
        left = tk.Frame(inner, bg=COLOR_BG)
        left.pack(side='left', fill='x', expand=True)

        tk.Label(left, text=mat['name'], font=FONT_BODY,
                 bg=COLOR_BG, fg=COLOR_TEXT,
                 anchor='w').pack(anchor='w')

        tk.Label(left, text=f"导入时间：{mat['created_at']}",
                 font=FONT_SMALL, bg=COLOR_BG,
                 fg=COLOR_SUBTLE, anchor='w').pack(anchor='w', pady=(2, 0))

        # 右侧：按钮
        right = tk.Frame(inner, bg=COLOR_BG)
        right.pack(side='right')

        tk.Button(right, text='开始练习',
                  font=FONT_SMALL,
                  bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2',
                  padx=14, pady=5,
                  activebackground='#333333',
                  command=lambda mid=mat['id']: self._on_select(mid)
                  ).pack(side='left', padx=(0, 8))

        tk.Button(right, text='删除',
                  font=FONT_SMALL,
                  bg=COLOR_BG, fg=COLOR_ERR,
                  relief='flat', cursor='hand2',
                  padx=10, pady=5,
                  highlightbackground=COLOR_ERR,
                  highlightthickness=1,
                  command=lambda mid=mat['id'], name=mat['name']:
                      self._on_delete(mid, name)
                  ).pack(side='left')

    def _on_section(self, material_id: int):
        if self.on_section:
            self.on_section(material_id)

    def _on_import(self):
        if self.on_import:
            self.on_import()

    def _on_select(self, material_id: int):
        if self.on_select:
            self.on_select(material_id)

    def _on_delete(self, material_id: int, name: str):
        """删除前二次确认"""
        ok = messagebox.askyesno(
            '确认删除',
            f'确定要删除「{name}」吗？\n相关练习记录也会一并删除，且无法恢复。'
        )
        if ok:
            try:
                delete_material(material_id)
                self.refresh()
            except Exception as e:
                messagebox.showerror('删除失败', f'删除时出现错误：\n{e}')
