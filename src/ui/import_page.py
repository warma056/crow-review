# 模块用途：资料导入页面，支持上传 Word/PDF/PPT 或直接粘贴文字

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.file_parser import parse_file
from src.core.db import insert_material

# 颜色常量
COLOR_BG     = '#FFFFFF'
COLOR_TEXT   = '#111111'
COLOR_SUBTLE = '#666666'
COLOR_BORDER = '#DDDDDD'
COLOR_INPUT  = '#F5F5F5'
COLOR_BTN_BG = '#111111'
COLOR_BTN_FG = '#FFFFFF'
COLOR_ERR    = '#B00020'
FONT_TITLE   = ('Microsoft YaHei', 16, 'bold')
FONT_BODY    = ('Microsoft YaHei', 13)
FONT_SMALL   = ('Microsoft YaHei', 11)


class ImportPage(tk.Frame):
    """资料导入页面"""

    def __init__(self, master, on_success=None):
        super().__init__(master, bg=COLOR_BG)
        self.on_success = on_success
        self._parsed_text = ''
        self._build_ui()

    def _build_ui(self):
        # ── 底部按钮（先 pack，确保始终可见）──
        btn_frame = tk.Frame(self, bg=COLOR_BG,
                             highlightbackground=COLOR_BORDER,
                             highlightthickness=1)
        btn_frame.pack(fill='x', side='bottom')

        tk.Button(btn_frame, text='确认导入',
                  font=FONT_BODY,
                  bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2',
                  padx=24, pady=9,
                  activebackground='#333333',
                  command=self._on_confirm
                  ).pack(side='right', padx=24, pady=12)

        tk.Button(btn_frame, text='取消',
                  font=FONT_BODY,
                  bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2',
                  padx=16, pady=9,
                  highlightbackground=COLOR_BORDER,
                  highlightthickness=1,
                  command=self._on_cancel
                  ).pack(side='right', padx=(0, 8), pady=12)

        # ── 标题区 ──
        title_bar = tk.Frame(self, bg=COLOR_BG)
        title_bar.pack(fill='x', padx=32, pady=(24, 0))

        tk.Label(title_bar, text='导入资料', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')
        tk.Label(title_bar,
                 text='支持 Word (.docx)、PDF、PPT (.pptx)，或直接粘贴文字',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(side='left', padx=16, pady=4)

        # ── 分割线 ──
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── 资料名称 ──
        name_frame = tk.Frame(self, bg=COLOR_BG)
        name_frame.pack(fill='x', padx=32, pady=(16, 0))

        tk.Label(name_frame, text='资料名称', font=FONT_BODY,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')

        self.name_var = tk.StringVar()
        tk.Entry(name_frame, textvariable=self.name_var,
                 font=FONT_BODY, bg=COLOR_INPUT,
                 fg=COLOR_TEXT, relief='flat',
                 highlightbackground=COLOR_BORDER,
                 highlightthickness=1
                 ).pack(fill='x', pady=(6, 0), ipady=6)

        # ── 上传文件 ──
        file_frame = tk.Frame(self, bg=COLOR_BG)
        file_frame.pack(fill='x', padx=32, pady=(16, 0))

        tk.Label(file_frame, text='方式一：上传文件',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')

        btn_row = tk.Frame(file_frame, bg=COLOR_BG)
        btn_row.pack(fill='x', pady=(8, 0))

        tk.Button(btn_row, text='选择 Word / PDF / PPT 文件',
                  font=FONT_BODY,
                  bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2',
                  padx=16, pady=7,
                  activebackground='#333333',
                  command=self._on_upload
                  ).pack(side='left')

        self.file_label = tk.Label(btn_row, text='尚未选择文件',
                                   font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE)
        self.file_label.pack(side='left', padx=14)

        # ── 分隔"或" ──
        sep = tk.Frame(self, bg=COLOR_BG)
        sep.pack(fill='x', padx=32, pady=(16, 0))
        tk.Label(sep, text='── 或 ──', font=FONT_SMALL,
                 bg=COLOR_BG, fg=COLOR_SUBTLE).pack()

        # ── 粘贴文字 ──
        paste_frame = tk.Frame(self, bg=COLOR_BG)
        paste_frame.pack(fill='both', expand=True, padx=32, pady=(4, 12))

        tk.Label(paste_frame, text='方式二：直接粘贴文字',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')

        text_container = tk.Frame(paste_frame,
                                  highlightbackground=COLOR_BORDER,
                                  highlightthickness=1, bg=COLOR_BORDER)
        text_container.pack(fill='both', expand=True, pady=(8, 0))

        self.text_area = tk.Text(text_container, font=FONT_BODY,
                                 bg=COLOR_INPUT, fg=COLOR_TEXT,
                                 relief='flat', wrap='word',
                                 padx=10, pady=8, undo=True)
        scrollbar = ttk.Scrollbar(text_container, command=self.text_area.yview)
        self.text_area.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.text_area.pack(fill='both', expand=True)

    def _on_upload(self):
        path = filedialog.askopenfilename(
            title='选择资料文件',
            filetypes=[('支持的文件', '*.docx *.pdf *.pptx'),
                       ('Word 文档', '*.docx'),
                       ('PDF 文件', '*.pdf'),
                       ('PPT 文件', '*.pptx')]
        )
        if not path:
            return
        try:
            content = parse_file(path)
            self.text_area.delete('1.0', 'end')
            self.text_area.insert('1.0', content)
            self._parsed_text = content
            if not self.name_var.get().strip():
                self.name_var.set(os.path.splitext(os.path.basename(path))[0])
            self.file_label.config(text=f'✓ {os.path.basename(path)}', fg='#2D7A2D')
        except ValueError as e:
            messagebox.showerror('读取失败', str(e))

    def _on_confirm(self):
        name = self.name_var.get().strip()
        content = self.text_area.get('1.0', 'end').strip()

        if not name:
            messagebox.showwarning('请填写名称', '请为这份资料填写一个名称')
            return
        if not content:
            messagebox.showwarning('内容为空', '请上传文件或粘贴文字内容')
            return
        if len(content) < 10:
            messagebox.showwarning('内容太短', '内容太短，无法提取有效关键词')
            return
        try:
            material_id = insert_material(name, content)
            messagebox.showinfo('导入成功', f'「{name}」已保存！')
            if self.on_success:
                self.on_success(material_id)
        except Exception as e:
            messagebox.showerror('保存失败', f'保存时出现错误：\n{e}')

    def _on_cancel(self):
        if self.on_success:
            self.on_success(None)
