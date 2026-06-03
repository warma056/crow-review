# 模块用途：人工校对页
# 功能：切换段落类型（问题/答案/说明）+ 在答案原文中选词加入关键词

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_section, update_section_blocks_keywords

COLOR_A_BG    = '#F0FAF0'
COLOR_T_BG    = '#F5F5F5'
COLOR_Q_LABEL = '#1a56db'
COLOR_A_LABEL = '#2D7A2D'
COLOR_T_LABEL = '#666666'
COLOR_SEL     = '#FFE066'   # 选中词高亮色

TYPE_LABELS = {'question': '问题', 'answer': '答案', 'text': '说明'}
TYPE_COLORS = {
    'question': (COLOR_Q_BG, COLOR_Q_LABEL),
    'answer':   (COLOR_A_BG, COLOR_A_LABEL),
    'text':     (COLOR_T_BG, COLOR_T_LABEL),
}


class ReviewPage(tk.Frame):

    def __init__(self, master, section_id: int, on_done=None, on_back=None):
        super().__init__(master, bg=COLOR_BG)
        self.section_id = section_id
        self.on_done    = on_done
        self.on_back    = on_back

        sec = get_section(section_id)
        if not sec:
            tk.Label(self, text='找不到小节数据', font=FONT_BODY,
                     bg=COLOR_BG, fg='#B00020').pack(pady=40)
            return

        self._title    = sec['title']
        self._blocks   = [dict(b) for b in sec['blocks']]
        self._keywords = list(sec['keywords'])
        self._build_ui()

    def _build_ui(self):
        # ── 底部按钮（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='保存校对结果',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=9,
                  activebackground='#333333',
                  command=self._on_save).pack(side='right', padx=24, pady=12)

        tk.Button(bottom, text='← 返回',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_back).pack(side='left', padx=24, pady=12)

        # ── 标题 ──
        tk.Label(self, text=f'校对标注：{self._title}',
                 font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT
                 ).pack(anchor='w', padx=32, pady=(20, 0))

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(10, 0))

        # ── 说明 ──
        tk.Label(self,
                 text='① 点击右侧按钮切换段落类型　② 在「答案」段落中用鼠标选中文字，点「加入关键词」',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE,
                 justify='left').pack(anchor='w', padx=32, pady=(8, 0))

        # ── 主体布局 ──
        main = tk.Frame(self, bg=COLOR_BG)
        main.pack(fill='both', expand=True, padx=32, pady=(10, 0))

        # 左侧段落列表
        left = tk.Frame(main, bg=COLOR_BG)
        left.pack(side='left', fill='both', expand=True)

        tk.Label(left, text='段落标注',
                 font=FONT_BODY_B, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')

        wrapper = tk.Frame(left, bg=COLOR_BG)
        wrapper.pack(fill='both', expand=True, pady=(6, 0))

        sb = ttk.Scrollbar(wrapper, orient='vertical')
        sb.pack(side='right', fill='y')

        self._canvas = tk.Canvas(wrapper, bg=COLOR_BG,
                                 highlightthickness=0,
                                 yscrollcommand=sb.set)
        self._canvas.pack(side='left', fill='both', expand=True)
        sb.config(command=self._canvas.yview)

        self._blocks_frame = tk.Frame(self._canvas, bg=COLOR_BG)
        self._canvas_win = self._canvas.create_window(
            (0, 0), window=self._blocks_frame, anchor='nw')

        self._canvas.bind('<Configure>',
                          lambda e: self._canvas.itemconfig(
                              self._canvas_win, width=e.width))
        self._blocks_frame.bind('<Configure>',
                                lambda e: self._canvas.configure(
                                    scrollregion=self._canvas.bbox('all')))
        self._canvas.bind_all('<MouseWheel>',
                              lambda e: self._canvas.yview_scroll(
                                  int(-1 * e.delta / 120), 'units'))

        # 右侧关键词面板
        tk.Frame(main, bg=COLOR_BORDER, width=1).pack(side='left', fill='y', padx=10)
        right = tk.Frame(main, bg=COLOR_BG, width=200)
        right.pack(side='left', fill='y')
        right.pack_propagate(False)
        self._build_keyword_panel(right)

        self._render_blocks()

    # ──────────────────────────────────────────────
    # 段落渲染
    # ──────────────────────────────────────────────
    def _render_blocks(self):
        for w in self._blocks_frame.winfo_children():
            w.destroy()
        for i, block in enumerate(self._blocks):
            self._build_block_card(i, block)
        self.after(80, self._fix_heights)

    def _build_block_card(self, idx: int, block: dict):
        btype     = block.get('type', 'text')
        bg, _     = TYPE_COLORS.get(btype, (COLOR_T_BG, COLOR_T_LABEL))
        content   = block.get('content', '')
        is_answer = (btype == 'answer')

        card = tk.Frame(self._blocks_frame, bg=bg,
                        highlightbackground=COLOR_BORDER,
                        highlightthickness=1)
        card.pack(fill='x', pady=(0, 6), padx=2)

        # ── 顶栏：类型切换按钮（先 pack）──
        top_bar = tk.Frame(card, bg=bg)
        top_bar.pack(fill='x', padx=8, pady=(6, 0))

        for t in ['question', 'answer', 'text']:
            lbl      = TYPE_LABELS[t]
            tbg, tfg = TYPE_COLORS[t]
            is_sel   = (btype == t)
            tk.Button(top_bar, text=lbl,
                      font=FONT_SMALL,
                      bg=tbg if is_sel else COLOR_BG,
                      fg=tfg if is_sel else COLOR_SUBTLE,
                      relief='groove' if is_sel else 'flat',
                      cursor='hand2', padx=8, pady=2,
                      command=lambda i=idx, nt=t: self._set_type(i, nt)
                      ).pack(side='left', padx=2)

        # ── 答案块：可选文字的 Text 组件 ──
        if is_answer:
            hint = tk.Frame(card, bg=bg)
            hint.pack(fill='x', padx=8, pady=(4, 0))
            tk.Label(hint,
                     text='选中文字后点 →',
                     font=FONT_SMALL, bg=bg, fg=COLOR_A_LABEL).pack(side='left')
            tk.Button(hint, text='加入关键词',
                      font=FONT_SMALL,
                      bg=COLOR_A_LABEL, fg='#FFFFFF',
                      relief='flat', cursor='hand2',
                      padx=8, pady=2,
                      command=lambda i=idx: self._add_selected(i)
                      ).pack(side='left', padx=(4, 0))

            txt = tk.Text(card, font=FONT_BODY, bg=bg, fg=COLOR_TEXT,
                          relief='flat', wrap='word',
                          padx=8, pady=6,
                          cursor='xterm',
                          height=1)
            txt.insert('1.0', content)
            txt.config(state='normal')   # 答案块允许选中文字
            txt.pack(fill='x', padx=4, pady=(4, 8))
            txt.tag_config('sel', background=COLOR_SEL)
            # 存引用，供 _add_selected 读取选中内容
            card._answer_text = txt
            card._block_idx   = idx
        else:
            # 非答案块：只读展示
            txt = tk.Text(card, font=FONT_BODY, bg=bg, fg=COLOR_TEXT,
                          relief='flat', wrap='word',
                          padx=8, pady=6,
                          cursor='arrow',
                          height=1)
            txt.insert('1.0', content)
            txt.config(state='disabled')
            txt.pack(fill='x', padx=4, pady=(4, 8))

        txt._is_answer = is_answer
        self._all_texts = getattr(self, '_all_texts', [])
        self._all_texts.append(txt)

    def _fix_heights(self):
        """渲染完成后统一调整 Text 高度"""
        self._all_texts = getattr(self, '_all_texts', [])
        for txt in self._all_texts:
            try:
                txt.update_idletasks()
                lines = txt.count('1.0', 'end', 'displaylines')
                if lines and lines[0]:
                    txt.config(height=max(lines[0], 1))
            except Exception:
                pass
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _set_type(self, idx: int, new_type: str):
        if idx < len(self._blocks):
            self._blocks[idx]['type'] = new_type
            self._all_texts = []
            self._render_blocks()

    def _add_selected(self, idx: int):
        """从对应答案块的 Text 中读取选中文字，加入关键词"""
        # 找到对应卡片的 Text 组件
        cards = [w for w in self._blocks_frame.winfo_children()]
        if idx >= len(cards):
            return
        card = cards[idx]
        txt  = getattr(card, '_answer_text', None)
        if not txt:
            return
        try:
            selected = txt.get('sel.first', 'sel.last').strip()
        except tk.TclError:
            messagebox.showinfo('未选中文字', '请先在答案原文中用鼠标选中要挖空的词')
            return
        if not selected:
            messagebox.showinfo('未选中文字', '请先在答案原文中用鼠标选中要挖空的词')
            return
        if selected in self._keywords:
            messagebox.showinfo('已存在', f'「{selected}」已在关键词列表中')
            return
        self._keywords.append(selected)
        self._render_keywords()

    # ──────────────────────────────────────────────
    # 关键词面板
    # ──────────────────────────────────────────────
    def _build_keyword_panel(self, parent):
        tk.Label(parent, text='关键词',
                 font=FONT_BODY_B, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')
        tk.Label(parent, text='仅「答案」段落挖空',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', pady=(2, 8))

        self._kw_frame = tk.Frame(parent, bg=COLOR_BG)
        self._kw_frame.pack(fill='x')
        self._render_keywords()

        tk.Frame(parent, bg=COLOR_BORDER, height=1).pack(fill='x', pady=(12, 8))
        tk.Label(parent, text='手动输入添加',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w')

        add_row = tk.Frame(parent, bg=COLOR_BG)
        add_row.pack(fill='x', pady=(4, 0))

        self._add_var = tk.StringVar()
        entry = tk.Entry(add_row, textvariable=self._add_var,
                         font=FONT_SMALL, bg='#F5F5F5', fg=COLOR_TEXT,
                         relief='flat', highlightbackground=COLOR_BORDER,
                         highlightthickness=1)
        entry.pack(side='left', fill='x', expand=True, ipady=5)
        entry.bind('<Return>', lambda e: self._add_keyword())

        tk.Button(add_row, text='＋',
                  font=FONT_SMALL, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=8, pady=5,
                  command=self._add_keyword).pack(side='left', padx=(4, 0))

    def _render_keywords(self):
        for w in self._kw_frame.winfo_children():
            w.destroy()
        if not self._keywords:
            tk.Label(self._kw_frame, text='暂无关键词',
                     font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w')
            return
        for kw in self._keywords:
            row = tk.Frame(self._kw_frame, bg=COLOR_BG)
            row.pack(fill='x', pady=2)
            tk.Label(row, text=kw, font=FONT_SMALL,
                     bg='#F0F0F0', fg=COLOR_TEXT,
                     padx=8, pady=3).pack(side='left')
            tk.Button(row, text='✕',
                      font=FONT_SMALL, bg=COLOR_BG, fg='#B00020',
                      relief='flat', cursor='hand2',
                      command=lambda k=kw: self._remove_keyword(k)
                      ).pack(side='left', padx=(4, 0))

    def _add_keyword(self):
        kw = self._add_var.get().strip()
        if not kw:
            return
        if kw in self._keywords:
            messagebox.showinfo('已存在', f'「{kw}」已在列表中')
            return
        self._keywords.append(kw)
        self._add_var.set('')
        self._render_keywords()

    def _remove_keyword(self, kw: str):
        if kw in self._keywords:
            self._keywords.remove(kw)
            self._render_keywords()

    def _on_save(self):
        if not self._keywords:
            ok = messagebox.askyesno('关键词为空',
                                     '当前没有关键词，保存后将无法练习。确定保存吗？')
            if not ok:
                return
        update_section_blocks_keywords(self.section_id, self._blocks, self._keywords)
        messagebox.showinfo('已保存', '校对结果已保存')
        if self.on_done:
            self.on_done(self.section_id)

    def _on_back(self):
        if self.on_back:
            self.on_back()
