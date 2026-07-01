# 模块用途：资料列表页面，展示所有已保存资料，支持进入练习、移动文件夹或删除

import tkinter as tk
from tkinter import messagebox
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import (get_all_materials, delete_material, get_due_reminders,
                         set_material_folder, get_all_folders)

# 颜色常量
COLOR_HOVER   = '#F5F5F5'

UNFILED = '未分类'   # 没有归入文件夹的资料归到这里


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
        self._folder_filter = '全部'   # 当前选中的文件夹筛选
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

        # ── 文件夹筛选栏 ──
        self._filter_frame = tk.Frame(self, bg=COLOR_BG)
        self._filter_frame.pack(fill='x', padx=32, pady=(10, 0))

        # ── 列表滚动区域 ──
        container = tk.Frame(self, bg=COLOR_BG)
        container.pack(fill='both', expand=True, padx=32, pady=16)

        canvas = tk.Canvas(container, bg=COLOR_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient='vertical',
                                 command=canvas.yview)
        self.list_frame = tk.Frame(canvas, bg=COLOR_BG)

        self._list_win = canvas.create_window((0, 0), window=self.list_frame, anchor='nw')
        self.list_frame.bind('<Configure>',
                             lambda e: canvas.configure(
                                 scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',
                    lambda e: canvas.itemconfig(self._list_win, width=e.width))
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
        self._render_due()
        self._render_filter_bar()
        self._render_list()

    # ──────────────────────────────────────────────
    # 今日待复习
    # ──────────────────────────────────────────────
    def _render_due(self):
        for w in self._due_frame.winfo_children():
            w.destroy()
        due = get_due_reminders()
        if not due:
            return
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

    # ──────────────────────────────────────────────
    # 文件夹筛选栏
    # ──────────────────────────────────────────────
    def _render_filter_bar(self):
        for w in self._filter_frame.winfo_children():
            w.destroy()

        folders = get_all_folders()
        tabs = ['全部', UNFILED] + folders

        # 当前筛选的文件夹如果已不存在了（比如里面的资料都被移走），回退到「全部」
        if self._folder_filter not in tabs:
            self._folder_filter = '全部'

        tk.Label(self._filter_frame, text='文件夹：',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left')

        for name in tabs:
            is_sel = (self._folder_filter == name)
            tk.Button(self._filter_frame, text=name,
                      font=FONT_SMALL,
                      bg=COLOR_BTN_BG if is_sel else COLOR_BG,
                      fg=COLOR_BTN_FG if is_sel else COLOR_TEXT,
                      relief='flat', cursor='hand2',
                      padx=10, pady=4,
                      highlightbackground=COLOR_BORDER,
                      highlightthickness=1,
                      command=lambda n=name: self._on_folder_filter(n)
                      ).pack(side='left', padx=(0, 6))

    def _on_folder_filter(self, name: str):
        self._folder_filter = name
        self.refresh()

    # ──────────────────────────────────────────────
    # 资料列表
    # ──────────────────────────────────────────────
    def _render_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        all_materials = get_all_materials()

        if not all_materials:
            tk.Label(self.list_frame,
                     text='还没有资料，点击右上角「导入新资料」开始吧',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE
                     ).pack(pady=60)
            return

        # 按当前文件夹筛选
        f = self._folder_filter
        if f == '全部':
            materials = all_materials
        elif f == UNFILED:
            materials = [m for m in all_materials if not (m.get('folder') or '')]
        else:
            materials = [m for m in all_materials if (m.get('folder') or '') == f]

        if not materials:
            tk.Label(self.list_frame,
                     text=f'「{f}」里还没有资料',
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

        # 右侧：按钮（先 pack，避免被长名称挤掉）
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

        tk.Button(right, text='移动',
                  font=FONT_SMALL,
                  bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2',
                  padx=10, pady=5,
                  highlightbackground=COLOR_BORDER,
                  highlightthickness=1,
                  command=lambda m=mat: self._open_move_dialog(m)
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

        # 左侧：名称 + 时间 + 所属文件夹
        left = tk.Frame(inner, bg=COLOR_BG)
        left.pack(side='left', fill='x', expand=True)

        tk.Label(left, text=mat['name'], font=FONT_BODY,
                 bg=COLOR_BG, fg=COLOR_TEXT,
                 anchor='w').pack(anchor='w')

        meta = tk.Frame(left, bg=COLOR_BG)
        meta.pack(anchor='w', pady=(2, 0))
        tk.Label(meta, text=f"导入时间：{mat['created_at']}",
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left')

        folder = mat.get('folder') or ''
        if folder:
            tk.Label(meta, text=f'　📁 {folder}',
                     font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left')

    # ──────────────────────────────────────────────
    # 移动到文件夹（弹窗）
    # ──────────────────────────────────────────────
    def _open_move_dialog(self, mat: dict):
        current = mat.get('folder') or ''

        dlg = tk.Toplevel(self)
        dlg.title('移动到文件夹')
        dlg.configure(bg=COLOR_BG)
        dlg.resizable(False, False)
        dlg.transient(self.winfo_toplevel())

        pad = tk.Frame(dlg, bg=COLOR_BG)
        pad.pack(fill='both', expand=True, padx=20, pady=18)

        tk.Label(pad, text=f'把「{mat["name"]}」移动到：',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                 wraplength=360, justify='left').pack(anchor='w')

        cur_text = current if current else UNFILED
        tk.Label(pad, text=f'当前：{cur_text}',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', pady=(4, 12))

        def move_to(folder: str):
            set_material_folder(mat['id'], folder)
            dlg.destroy()
            self.refresh()

        # ── 已有文件夹（含「未分类」）──
        tk.Label(pad, text='选择已有文件夹：',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w')

        chips = tk.Frame(pad, bg=COLOR_BG)
        chips.pack(fill='x', pady=(4, 12))

        existing = [UNFILED] + get_all_folders()
        for name in existing:
            target = '' if name == UNFILED else name
            is_cur = (target == current)
            tk.Button(chips, text=name,
                      font=FONT_SMALL,
                      bg=COLOR_BTN_BG if is_cur else COLOR_BG,
                      fg=COLOR_BTN_FG if is_cur else COLOR_TEXT,
                      relief='flat', cursor='hand2',
                      padx=10, pady=4,
                      highlightbackground=COLOR_BORDER,
                      highlightthickness=1,
                      command=lambda t=target: move_to(t)
                      ).pack(side='left', padx=(0, 6), pady=2)

        # ── 新建文件夹 ──
        tk.Label(pad, text='或新建文件夹：',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w')

        new_row = tk.Frame(pad, bg=COLOR_BG)
        new_row.pack(fill='x', pady=(4, 0))

        name_var = tk.StringVar()
        entry = tk.Entry(new_row, textvariable=name_var,
                         font=FONT_BODY, bg='#F5F5F5', fg=COLOR_TEXT,
                         relief='flat', highlightbackground=COLOR_BORDER,
                         highlightthickness=1)
        entry.pack(side='left', fill='x', expand=True, ipady=4)

        def create_and_move():
            name = name_var.get().strip()
            if not name:
                messagebox.showinfo('提示', '请输入文件夹名称', parent=dlg)
                return
            if name in ('全部', UNFILED):
                messagebox.showinfo('提示', f'「{name}」是保留名称，请换一个', parent=dlg)
                return
            move_to(name)

        tk.Button(new_row, text='创建并移入',
                  font=FONT_SMALL, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=12, pady=5,
                  command=create_and_move).pack(side='left', padx=(6, 0))
        entry.bind('<Return>', lambda e: create_and_move())

        # ── 取消 ──
        tk.Button(pad, text='取消',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE,
                  relief='flat', cursor='hand2', padx=12, pady=5,
                  command=dlg.destroy).pack(anchor='e', pady=(16, 0))

        # 居中到主窗口
        dlg.update_idletasks()
        parent = self.winfo_toplevel()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        dw, dh = dlg.winfo_reqwidth(), dlg.winfo_reqheight()
        x = px + max((pw - dw) // 2, 0)
        y = py + max((ph - dh) // 2, 0)
        dlg.geometry(f'+{x}+{y}')

        entry.focus_set()
        dlg.grab_set()

    # ──────────────────────────────────────────────
    # 其它回调
    # ──────────────────────────────────────────────
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
