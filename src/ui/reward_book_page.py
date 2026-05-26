# 模块用途：奖励阅读页，导入小说、查看解锁进度、阅读已解锁段落

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import (get_all_reward_books, insert_reward_book, delete_reward_book,
                         get_reward_book, get_chunk, is_chunk_unlocked, get_unlocked_count)

COLOR_BG      = '#FFFFFF'
COLOR_TEXT    = '#111111'
COLOR_SUBTLE  = '#666666'
COLOR_BORDER  = '#DDDDDD'
COLOR_BTN_BG  = '#111111'
COLOR_BTN_FG  = '#FFFFFF'
COLOR_OK      = '#2D7A2D'
COLOR_LOCK_BG = '#F5F5F5'
COLOR_LOCK_FG = '#AAAAAA'
COLOR_READ_BG = '#FAFFF8'
COLOR_READ_BD = '#B8DEB8'
FONT_TITLE    = ('Microsoft YaHei', 16, 'bold')
FONT_BODY     = ('Microsoft YaHei', 13)
FONT_BODY_B   = ('Microsoft YaHei', 13, 'bold')
FONT_SMALL    = ('Microsoft YaHei', 11)
FONT_READ     = ('Microsoft YaHei', 14)   # 阅读正文大一点

CHUNK_SIZE = 500   # 每段字数


class RewardBookPage(tk.Frame):
    """奖励阅读主页：书架 + 阅读视图二合一"""

    def __init__(self, master, book_id: int = None, on_back=None):
        super().__init__(master, bg=COLOR_BG)
        self.on_back      = on_back
        self._book_id     = book_id   # 若传入则直接进阅读视图
        self._read_mode   = False
        self._text_widgets = []
        self._build_ui()

    def _build_ui(self):
        if self._book_id:
            self._show_reader(self._book_id)
        else:
            self._show_shelf()

    # ══════════════════════════════════════════════
    # 书架视图
    # ══════════════════════════════════════════════
    def _show_shelf(self):
        for w in self.winfo_children():
            w.destroy()
        self._read_mode = False

        # ── 底部（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='+ 导入小说（.txt）',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=20, pady=9,
                  activebackground='#333333',
                  command=self._import_book).pack(side='left', padx=24, pady=12)

        tk.Button(bottom, text='← 返回',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_back).pack(side='right', padx=24, pady=12)

        # ── 顶部 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))
        tk.Label(top, text='我的奖励书架', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        tk.Label(self,
                 text='完成练习自动解锁内容 · 得分越高解锁越多',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=32, pady=(4, 0))
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── 书列表 ──
        books = get_all_reward_books()
        if not books:
            tk.Label(self,
                     text='还没有导入小说。\n练习完成后在此处导入 .txt 文件，系统会自动解锁内容。',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE,
                     justify='center').pack(pady=60)
            return

        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=12)
        sb = tk.Scrollbar(outer, orient='vertical')
        sb.pack(side='right', fill='y')
        canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0,
                           yscrollcommand=sb.set)
        canvas.pack(side='left', fill='both', expand=True)
        sb.config(command=canvas.yview)
        lf = tk.Frame(canvas, bg=COLOR_BG)
        win = canvas.create_window((0, 0), window=lf, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(win, width=e.width))
        lf.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-1 * e.delta / 120), 'units'))

        for book in books:
            self._build_book_card(lf, book)

    def _build_book_card(self, parent, book: dict):
        unlocked = get_unlocked_count(book['id'])
        total    = book['total_chunks']
        pct      = int(unlocked / total * 100) if total else 0

        card = tk.Frame(parent, bg=COLOR_BG,
                        highlightbackground=COLOR_BORDER,
                        highlightthickness=1)
        card.pack(fill='x', pady=(0, 10), padx=2)
        inner = tk.Frame(card, bg=COLOR_BG)
        inner.pack(fill='x', padx=16, pady=14)

        # 右侧按钮先 pack
        btn_f = tk.Frame(inner, bg=COLOR_BG)
        btn_f.pack(side='right')

        tk.Button(btn_f, text='阅读',
                  font=FONT_SMALL, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=16, pady=7,
                  activebackground='#333333',
                  command=lambda bid=book['id']: self._show_reader(bid)
                  ).pack(side='left')

        tk.Button(btn_f, text='删除',
                  font=FONT_SMALL, bg=COLOR_BG, fg='#B00020',
                  relief='flat', cursor='hand2', padx=12, pady=7,
                  highlightbackground='#FFCCCC', highlightthickness=1,
                  command=lambda bid=book['id']: self._delete_book(bid)
                  ).pack(side='left', padx=(8, 0))

        # 左侧信息
        left = tk.Frame(inner, bg=COLOR_BG)
        left.pack(side='left', fill='x', expand=True)
        tk.Label(left, text=book['title'],
                 font=FONT_BODY_B, bg=COLOR_BG, fg=COLOR_TEXT, anchor='w').pack(anchor='w')

        meta = tk.Frame(left, bg=COLOR_BG)
        meta.pack(anchor='w', pady=(4, 0))
        tk.Label(meta, text=f'已解锁 {unlocked} / {total} 段  ({pct}%)',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_OK if unlocked else COLOR_SUBTLE
                 ).pack(side='left')

        # 进度条
        bar_bg = tk.Frame(left, bg=COLOR_BORDER, height=4)
        bar_bg.pack(fill='x', pady=(6, 0))
        bar_bg.update_idletasks()
        if pct > 0:
            tk.Frame(bar_bg, bg=COLOR_OK, height=4,
                     width=int(bar_bg.winfo_width() * pct / 100)).place(x=0, y=0)
        # 用 after 等宽度确定后再画进度条
        def _draw_bar(bb=bar_bg, p=pct):
            bb.update_idletasks()
            w = bb.winfo_width()
            if w > 1 and p > 0:
                tk.Frame(bb, bg=COLOR_OK, height=4,
                         width=int(w * p / 100)).place(x=0, y=0)
        self.after(150, _draw_bar)

    def _import_book(self):
        path = filedialog.askopenfilename(
            title='选择小说文件',
            filetypes=[('文本文件', '*.txt'), ('所有文件', '*.*')]
        )
        if not path:
            return
        try:
            with open(path, encoding='utf-8', errors='replace') as f:
                text = f.read()
        except Exception as e:
            messagebox.showerror('读取失败', f'无法读取文件：{e}')
            return

        text = text.strip()
        if not text:
            messagebox.showwarning('文件为空', '该文件没有内容')
            return

        # 按 CHUNK_SIZE 切段
        chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        title  = os.path.splitext(os.path.basename(path))[0]

        insert_reward_book(title, chunks, CHUNK_SIZE)
        messagebox.showinfo('导入成功',
                            f'《{title}》已导入，共 {len(chunks)} 段。\n'
                            f'完成练习后自动解锁内容。')
        self._show_shelf()

    def _delete_book(self, book_id: int):
        book = get_reward_book(book_id)
        if not book:
            return
        ok = messagebox.askyesno('删除确认',
                                 f'确定删除《{book["title"]}》？\n所有解锁进度也会一并清除。')
        if ok:
            delete_reward_book(book_id)
            self._show_shelf()

    # ══════════════════════════════════════════════
    # 阅读视图
    # ══════════════════════════════════════════════
    def _show_reader(self, book_id: int):
        for w in self.winfo_children():
            w.destroy()
        self._text_widgets.clear()
        self._read_mode = True

        book = get_reward_book(book_id)
        if not book:
            self._show_shelf()
            return

        total    = book['total_chunks']
        unlocked = get_unlocked_count(book_id)

        # ── 底部（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='← 书架',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=20, pady=9,
                  activebackground='#333333',
                  command=self._show_shelf).pack(side='right', padx=24, pady=12)

        tk.Label(bottom,
                 text=f'已解锁 {unlocked} / {total} 段  ·  完成练习可继续解锁',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(side='left', padx=24, pady=12)

        # ── 顶部 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))
        tk.Label(top, text=f'《{book["title"]}》',
                 font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── 正文滚动区 ──
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=12)
        sb = tk.Scrollbar(outer, orient='vertical')
        sb.pack(side='right', fill='y')
        self._canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0,
                                 yscrollcommand=sb.set)
        self._canvas.pack(side='left', fill='both', expand=True)
        sb.config(command=self._canvas.yview)
        self._text_frame = tk.Frame(self._canvas, bg=COLOR_BG)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._text_frame, anchor='nw')
        self._canvas.bind('<Configure>',
                          lambda e: (self._canvas.itemconfig(self._canvas_win, width=e.width),
                                     self.after(50, self._fix_heights)))
        self._text_frame.bind('<Configure>',
                              lambda e: self._canvas.configure(
                                  scrollregion=self._canvas.bbox('all')))
        self._canvas.bind_all('<MouseWheel>',
                              lambda e: self._canvas.yview_scroll(
                                  int(-1 * e.delta / 120), 'units'))

        # 渲染所有段落
        for i in range(total):
            self._render_chunk(book_id, i)

        self.after(100, self._fix_heights)

    def _render_chunk(self, book_id: int, idx: int):
        if is_chunk_unlocked(book_id, idx):
            content = get_chunk(book_id, idx)
            frame = tk.Frame(self._text_frame, bg=COLOR_READ_BG,
                             highlightbackground=COLOR_READ_BD,
                             highlightthickness=1)
            frame.pack(fill='x', pady=(0, 8))
            txt = tk.Text(frame, font=FONT_READ,
                          bg=COLOR_READ_BG, fg=COLOR_TEXT,
                          relief='flat', wrap='word',
                          padx=14, pady=10,
                          cursor='arrow', height=1)
            txt.insert('1.0', content or '')
            txt.config(state='disabled')
            txt.pack(fill='x')
            self._text_widgets.append(txt)
        else:
            frame = tk.Frame(self._text_frame, bg=COLOR_LOCK_BG,
                             highlightbackground=COLOR_BORDER,
                             highlightthickness=1)
            frame.pack(fill='x', pady=(0, 8))
            tk.Label(frame,
                     text=f'🔒  第 {idx + 1} 段  ·  完成更多练习后解锁',
                     font=FONT_SMALL, bg=COLOR_LOCK_BG, fg=COLOR_LOCK_FG,
                     pady=10).pack(fill='x')

    def _fix_heights(self):
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
        try:
            self._canvas.configure(scrollregion=self._canvas.bbox('all'))
        except Exception:
            pass

    def _on_back(self):
        if self.on_back:
            self.on_back()
