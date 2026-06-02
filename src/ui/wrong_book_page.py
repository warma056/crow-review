# 模块用途：错题本页，查看论述题错题、重新作答、AI批改、达标后移出

import tkinter as tk
from tkinter import messagebox
import threading
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_all_wrong_questions, delete_wrong_question
from src.core.config import get_api_key, load_config

COLOR_BG      = '#FFFFFF'
COLOR_TEXT    = '#111111'
COLOR_SUBTLE  = '#666666'
COLOR_BORDER  = '#DDDDDD'
COLOR_BTN_BG  = '#111111'
COLOR_BTN_FG  = '#FFFFFF'
COLOR_OK      = '#2D7A2D'
COLOR_OK_BG   = '#F0FAF0'
COLOR_ERR     = '#B00020'
COLOR_ERR_BG  = '#FFF0F0'
COLOR_WARN    = '#996600'
COLOR_WARN_BG = '#FFFDF0'
FONT_TITLE    = ('Microsoft YaHei', 16, 'bold')
FONT_BODY     = ('Microsoft YaHei', 13)
FONT_BODY_B   = ('Microsoft YaHei', 13, 'bold')
FONT_SMALL    = ('Microsoft YaHei', 11)


class WrongBookPage(tk.Frame):

    def __init__(self, master, on_back=None):
        super().__init__(master, bg=COLOR_BG)
        self.on_back = on_back
        self._show_list()

    # ══════════════════════════════════════════════
    # 错题列表
    # ══════════════════════════════════════════════
    def _show_list(self):
        self._clear()

        # ── 底部（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')
        tk.Button(bottom, text='← 返回',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=9,
                  activebackground='#333333',
                  command=self._on_back).pack(side='right', padx=24, pady=12)

        # ── 顶部 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))
        tk.Label(top, text='错题本', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        questions = get_all_wrong_questions()
        tk.Label(top, text=f'共 {len(questions)} 道题',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(side='left', padx=16)

        tk.Label(self, text='论述题错题收藏 · 重新作答达标后可移出',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=32, pady=(4, 0))
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        if not questions:
            tk.Label(self,
                     text='还没有错题。\n在综合测验结果页点「+ 加入错题本」来收藏论述题。',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE,
                     justify='center').pack(pady=60)
            return

        # ── 滚动列表 ──
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

        for q in questions:
            self._build_card(lf, q)

    def _build_card(self, parent, q: dict):
        card = tk.Frame(parent, bg=COLOR_WARN_BG,
                        highlightbackground='#E8D870', highlightthickness=1)
        card.pack(fill='x', pady=(0, 10), padx=2)
        inner = tk.Frame(card, bg=COLOR_WARN_BG)
        inner.pack(fill='x', padx=16, pady=14)

        # 右侧按钮先 pack
        btn_f = tk.Frame(inner, bg=COLOR_WARN_BG)
        btn_f.pack(side='right', anchor='n')

        tk.Button(btn_f, text='重新作答',
                  font=FONT_SMALL, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=12, pady=6,
                  activebackground='#333333',
                  command=lambda wq=q: self._show_answer(wq)
                  ).pack(anchor='e')

        tk.Button(btn_f, text='移出错题本',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_ERR,
                  relief='flat', cursor='hand2', padx=10, pady=6,
                  highlightbackground='#FFCCCC', highlightthickness=1,
                  command=lambda wid=q['id']: self._remove(wid)
                  ).pack(anchor='e', pady=(6, 0))

        # 左侧内容
        left = tk.Frame(inner, bg=COLOR_WARN_BG)
        left.pack(side='left', fill='x', expand=True)

        tk.Label(left, text=q['question'],
                 font=FONT_BODY_B, bg=COLOR_WARN_BG, fg=COLOR_TEXT,
                 wraplength=550, justify='left', anchor='w').pack(anchor='w')

        tk.Label(left, text=f'来源：{q["source_label"]}',
                 font=FONT_SMALL, bg=COLOR_WARN_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', pady=(6, 0))

        # 折叠参考答案
        show_var = tk.BooleanVar(value=False)
        ref_frame = tk.Frame(left, bg=COLOR_WARN_BG)

        def toggle(sv=show_var, rf=ref_frame, qa=q):
            if sv.get():
                rf.pack(fill='x', pady=(6, 0))
                toggle_btn.config(text='▲ 收起参考答案')
            else:
                rf.pack_forget()
                toggle_btn.config(text='▼ 查看参考答案')
            sv.set(not sv.get())

        toggle_btn = tk.Button(left, text='▼ 查看参考答案',
                               font=FONT_SMALL, bg=COLOR_WARN_BG, fg=COLOR_WARN,
                               relief='flat', cursor='hand2',
                               command=toggle)
        toggle_btn.pack(anchor='w', pady=(8, 0))

        ref_txt = tk.Text(ref_frame, font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                          relief='flat', wrap='word', padx=6, pady=4,
                          highlightbackground=COLOR_BORDER, highlightthickness=1,
                          height=4)
        ref_txt.insert('1.0', q['ref_answer'])
        ref_txt.config(state='disabled')
        ref_txt.pack(fill='x')

    def _remove(self, wrong_id: int):
        ok = messagebox.askyesno('移出确认', '确定将这道题移出错题本吗？')
        if ok:
            delete_wrong_question(wrong_id)
            self._show_list()

    # ══════════════════════════════════════════════
    # 重新作答页
    # ══════════════════════════════════════════════
    def _show_answer(self, q: dict):
        self._clear()

        # ── 底部（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='提交答案',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=9,
                  activebackground='#333333',
                  command=lambda: self._submit(q, txt.get('1.0', 'end').strip())
                  ).pack(side='right', padx=24, pady=12)

        tk.Button(bottom, text='← 返回错题本',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._show_list).pack(side='right', padx=(0, 8), pady=12)

        # ── 内容 ──
        tk.Label(self, text='重新作答', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w', padx=32, pady=(24, 0))
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 8))

        inner = tk.Frame(self, bg=COLOR_BG)
        inner.pack(fill='both', expand=True, padx=32, pady=8)

        # 题目
        q_frame = tk.Frame(inner, bg=COLOR_WARN_BG,
                           highlightbackground='#E8D870', highlightthickness=1)
        q_frame.pack(fill='x')
        tk.Label(q_frame, text=q['question'],
                 font=FONT_BODY_B, bg=COLOR_WARN_BG, fg=COLOR_TEXT,
                 wraplength=700, justify='left', anchor='w',
                 padx=14, pady=12).pack(fill='x')

        tk.Label(inner, text='请在下方输入你的答案：',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', pady=(16, 4))

        txt = tk.Text(inner, font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                      relief='flat', wrap='word',
                      highlightbackground=COLOR_BORDER, highlightthickness=1,
                      padx=8, pady=6, height=10)
        txt.pack(fill='x')

        self._current_q = q

    def _submit(self, q: dict, user_answer: str):
        if not user_answer:
            messagebox.showwarning('未作答', '请先输入答案')
            return
        # FIX: Ollama 不需要 API Key
        cfg = load_config()
        if cfg.get('api_provider', 'deepseek') != 'ollama' and not get_api_key():
            messagebox.showwarning('未设置 API Key', '需要 AI 批改，请先在设置中填写 DeepSeek API Key')
            return
        self._show_grading(q, user_answer)

    # ══════════════════════════════════════════════
    # AI 批改
    # ══════════════════════════════════════════════
    def _show_grading(self, q: dict, user_answer: str):
        self._clear()
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.place(relx=0.5, rely=0.45, anchor='center')
        tk.Label(frame, text='AI 正在批改，请稍候...',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE).pack()

        def do():
            try:
                from src.core.ai_client import grade_quiz
                question_obj = {
                    'id': 1, 'type': 'essay',
                    'question': q['question'],
                    'answer': q['ref_answer']
                }
                results = grade_quiz([question_obj], {1: user_answer})
                r = results[0]
                self.after(0, lambda: self._show_result(q, user_answer, r))
            except Exception as e:
                self.after(0, lambda: self._on_error(str(e), q))

        threading.Thread(target=do, daemon=True).start()

    def _on_error(self, msg: str, q: dict):
        messagebox.showerror('批改失败', f'AI 批改出错：\n{msg}')
        self._show_answer(q)

    # ══════════════════════════════════════════════
    # 批改结果
    # ══════════════════════════════════════════════
    def _show_result(self, q: dict, user_answer: str, r: dict):
        self._clear()
        score      = r['score']
        full_score = r['full_score']
        passed     = score >= 15   # 达标线

        result_bg = COLOR_OK_BG if passed else COLOR_ERR_BG
        bd_col    = '#B8DEB8' if passed else '#FFCCCC'

        # ── 底部（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        if passed:
            tk.Button(bottom, text='移出错题本 ✓',
                      font=FONT_BODY, bg=COLOR_OK, fg=COLOR_BTN_FG,
                      relief='flat', cursor='hand2', padx=24, pady=9,
                      activebackground='#1f5a1f',
                      command=lambda: self._confirm_remove(q['id'])
                      ).pack(side='right', padx=24, pady=12)
        else:
            tk.Button(bottom, text='再试一次',
                      font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                      relief='flat', cursor='hand2', padx=24, pady=9,
                      activebackground='#333333',
                      command=lambda: self._show_answer(q)
                      ).pack(side='right', padx=24, pady=12)

        tk.Button(bottom, text='← 返回错题本',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._show_list).pack(side='right', padx=(0, 8), pady=12)

        # ── 得분 ──
        tk.Label(self, text='批改结果', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w', padx=32, pady=(24, 0))

        score_color = COLOR_OK if passed else COLOR_ERR
        score_row = tk.Frame(self, bg=COLOR_BG)
        score_row.pack(anchor='w', padx=32, pady=(12, 0))
        tk.Label(score_row, text=f'{score}',
                 font=('Microsoft YaHei', 32, 'bold'),
                 bg=COLOR_BG, fg=score_color).pack(side='left')
        tk.Label(score_row, text=f' / {full_score} 分',
                 font=FONT_BODY, bg=COLOR_BG, fg=score_color
                 ).pack(side='left', anchor='s', pady=(0, 6))

        if passed:
            tk.Label(self, text='🎉 达标！可以移出错题本了',
                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_OK
                     ).pack(anchor='w', padx=32, pady=(4, 0))
        else:
            tk.Label(self, text='还需继续加油，得 15 分以上才能移出错题本',
                     font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_ERR
                     ).pack(anchor='w', padx=32, pady=(4, 0))

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(16, 0))

        # ── 详情滚动区 ──
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=12)
        sb = tk.Scrollbar(outer, orient='vertical')
        sb.pack(side='right', fill='y')
        canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0,
                           yscrollcommand=sb.set)
        canvas.pack(side='left', fill='both', expand=True)
        sb.config(command=canvas.yview)
        rf = tk.Frame(canvas, bg=COLOR_BG)
        win = canvas.create_window((0, 0), window=rf, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(win, width=e.width))
        rf.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-1 * e.delta / 120), 'units'))

        card = tk.Frame(rf, bg=result_bg,
                        highlightbackground=bd_col, highlightthickness=1)
        card.pack(fill='x', padx=2)
        inner = tk.Frame(card, bg=result_bg)
        inner.pack(fill='x', padx=16, pady=14)

        # 题目
        tk.Label(inner, text=q['question'],
                 font=FONT_BODY_B, bg=result_bg, fg=COLOR_TEXT,
                 wraplength=680, justify='left').pack(anchor='w')

        # 你的答案
        tk.Label(inner, text='你的答案：',
                 font=FONT_SMALL, bg=result_bg, fg=COLOR_SUBTLE
                 ).pack(anchor='w', pady=(10, 2))
        ans_box = tk.Text(inner, font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                          relief='flat', wrap='word', padx=6, pady=4,
                          highlightbackground=COLOR_BORDER, highlightthickness=1,
                          height=4)
        ans_box.insert('1.0', user_answer)
        ans_box.config(state='disabled')
        ans_box.pack(fill='x')

        # 参考答案
        tk.Label(inner, text='参考答案：',
                 font=FONT_SMALL, bg=result_bg, fg=COLOR_SUBTLE
                 ).pack(anchor='w', pady=(10, 2))
        ref_box = tk.Text(inner, font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                          relief='flat', wrap='word', padx=6, pady=4,
                          highlightbackground=COLOR_BORDER, highlightthickness=1,
                          height=4)
        ref_box.insert('1.0', q['ref_answer'])
        ref_box.config(state='disabled')
        ref_box.pack(fill='x')

        # AI 点评
        tk.Label(inner, text=f'💬 {r["comment"]}',
                 font=FONT_SMALL, bg=result_bg, fg=COLOR_TEXT,
                 wraplength=680, justify='left').pack(anchor='w', pady=(10, 0))

    def _confirm_remove(self, wrong_id: int):
        delete_wrong_question(wrong_id)
        messagebox.showinfo('已移出', '这道题已从错题本中移出，继续加油！')
        self._show_list()

    # ══════════════════════════════════════════════
    # 工具方法
    # ══════════════════════════════════════════════
    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _on_back(self):
        if self.on_back:
            self.on_back()
