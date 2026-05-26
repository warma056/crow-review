# 模块用途：综合测验页，跨小节出题、答题、AI批改、详细点评

import tkinter as tk
from tkinter import messagebox
import threading
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import get_sections_by_material, get_section
from src.core.db import add_wrong_question, wrong_question_exists, delete_wrong_question
from src.core.config import get_api_key

COLOR_BG      = '#FFFFFF'
COLOR_TEXT    = '#111111'
COLOR_SUBTLE  = '#666666'
COLOR_BORDER  = '#DDDDDD'
COLOR_BTN_BG  = '#111111'
COLOR_BTN_FG  = '#FFFFFF'
COLOR_OK      = '#2D7A2D'
COLOR_ERR     = '#B00020'
COLOR_OK_BG   = '#F0FAF0'
COLOR_ERR_BG  = '#FFF0F0'
COLOR_Q_BG    = '#F5F5F5'
COLOR_WARN    = '#996600'
COLOR_WARN_BG = '#FFFDF0'
FONT_TITLE    = ('Microsoft YaHei', 16, 'bold')
FONT_BODY     = ('Microsoft YaHei', 13)
FONT_BODY_B   = ('Microsoft YaHei', 13, 'bold')
FONT_SMALL    = ('Microsoft YaHei', 11)
FONT_SCORE    = ('Microsoft YaHei', 32, 'bold')


class QuizPage(tk.Frame):
    """综合测验：选节 → 出题加载 → 答题 → 批改加载 → 结果"""

    def __init__(self, master, material_id: int, on_back=None):
        super().__init__(master, bg=COLOR_BG)
        self.material_id  = material_id
        self.on_back      = on_back
        self._questions   = []      # 当前题目列表
        self._answers     = {}      # {question_id: StringVar 或 str}
        self._choice_vars = {}      # {question_id: StringVar} 选择题
        self._essay_texts = {}      # {question_id: Text widget} 论述题
        self._results     = []      # 批改结果

        self._show_select()

    # ══════════════════════════════════════════════
    # 第一步：选择小节
    # ══════════════════════════════════════════════
    def _show_select(self):
        self._clear()

        # ── 底部（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='开始出题 →',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=9,
                  activebackground='#333333',
                  command=self._on_start).pack(side='right', padx=24, pady=12)

        tk.Button(bottom, text='← 返回',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_back).pack(side='right', padx=(0, 8), pady=12)

        # ── 顶部 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))
        tk.Label(top, text='综合测验', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        tk.Label(self, text='选择要测验的小节（可多选），AI 将自动出题',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=32, pady=(4, 0))
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # 全选按钮
        ctrl = tk.Frame(self, bg=COLOR_BG)
        ctrl.pack(anchor='w', padx=32, pady=(8, 0))
        tk.Button(ctrl, text='全选',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=10, pady=4,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._select_all).pack(side='left')
        tk.Button(ctrl, text='全不选',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=10, pady=4,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._deselect_all).pack(side='left', padx=(8, 0))

        # ── 小节列表 ──
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=8)
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

        sections = get_sections_by_material(self.material_id)
        self._check_vars = {}
        for sec in sections:
            var = tk.BooleanVar(value=True)
            self._check_vars[sec['id']] = var
            row = tk.Frame(lf, bg=COLOR_BG,
                           highlightbackground=COLOR_BORDER, highlightthickness=1)
            row.pack(fill='x', pady=(0, 6), padx=2)
            tk.Checkbutton(row, text=f"  {sec['title']}",
                           variable=var, font=FONT_BODY,
                           bg=COLOR_BG, fg=COLOR_TEXT,
                           activebackground=COLOR_BG,
                           selectcolor=COLOR_BG,
                           anchor='w').pack(fill='x', padx=8, pady=10)

    def _select_all(self):
        for var in self._check_vars.values():
            var.set(True)

    def _deselect_all(self):
        for var in self._check_vars.values():
            var.set(False)

    def _on_start(self):
        selected = [sid for sid, var in self._check_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning('未选择', '请至少选择一个小节')
            return
        if not get_api_key():
            messagebox.showwarning('未设置 API Key', '综合测验需要调用 AI，请先在设置中填写 API Key')
            return
        self._selected_ids = selected
        self._show_generating()

    # ══════════════════════════════════════════════
    # 第二步：AI 出题（加载中）
    # ══════════════════════════════════════════════
    def _show_generating(self):
        self._clear()
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.place(relx=0.5, rely=0.45, anchor='center')
        self._status_label = tk.Label(frame, text='AI 正在出题，请稍候...',
                                      font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE)
        self._status_label.pack()
        tk.Label(frame, text='根据资料量可能需要 10-30 秒',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(pady=(8, 0))

        def do():
            try:
                from src.core.ai_client import generate_quiz
                # 拼接选中小节内容
                sections_data = []
                for sid in self._selected_ids:
                    sec = get_section(sid)
                    if sec:
                        # 用 blocks 里的文本拼成纯文字
                        content = '\n'.join(
                            b['content'] for b in sec.get('blocks', [])
                            if b.get('content', '').strip()
                        )
                        sections_data.append({'title': sec['title'], 'content': content})
                result = generate_quiz(sections_data)
                self.after(0, lambda: self._on_quiz_ready(result))
            except Exception as e:
                self.after(0, lambda: self._on_generate_error(str(e)))

        threading.Thread(target=do, daemon=True).start()

    def _on_quiz_ready(self, result: dict):
        self._questions = result.get('questions', [])
        if not self._questions:
            messagebox.showerror('出题失败', 'AI 未能生成题目，请重试')
            self._show_select()
            return
        self._show_answer()

    def _on_generate_error(self, msg: str):
        messagebox.showerror('出题失败', f'AI 出题时出错：\n{msg}')
        self._show_select()

    # ══════════════════════════════════════════════
    # 第三步：答题
    # ══════════════════════════════════════════════
    def _show_answer(self):
        self._clear()
        self._choice_vars.clear()
        self._essay_texts.clear()

        # ── 底部（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='提交答案',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=9,
                  activebackground='#333333',
                  command=self._on_submit).pack(side='right', padx=24, pady=12)

        tk.Button(bottom, text='← 重新选题',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._show_select).pack(side='right', padx=(0, 8), pady=12)

        # ── 顶部 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))
        tk.Label(top, text='综合测验', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')
        n_choice = sum(1 for q in self._questions if q['type'] == 'choice')
        n_essay  = sum(1 for q in self._questions if q['type'] == 'essay')
        tk.Label(top, text=f'选择题 {n_choice} 道  ·  论述题 {n_essay} 道',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(side='left', padx=16)
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── 题目滚动区 ──
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=12)
        sb = tk.Scrollbar(outer, orient='vertical')
        sb.pack(side='right', fill='y')
        canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0,
                           yscrollcommand=sb.set)
        canvas.pack(side='left', fill='both', expand=True)
        sb.config(command=canvas.yview)
        self._ans_frame = tk.Frame(canvas, bg=COLOR_BG)
        win = canvas.create_window((0, 0), window=self._ans_frame, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(win, width=e.width))
        self._ans_frame.bind('<Configure>',
                             lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-1 * e.delta / 120), 'units'))

        for q in self._questions:
            self._render_question(q)

    def _render_question(self, q: dict):
        qid   = q['id']
        qtype = q['type']

        card = tk.Frame(self._ans_frame, bg=COLOR_Q_BG,
                        highlightbackground=COLOR_BORDER, highlightthickness=1)
        card.pack(fill='x', pady=(0, 12), padx=2)
        inner = tk.Frame(card, bg=COLOR_Q_BG)
        inner.pack(fill='x', padx=16, pady=14)

        # 题号 + 题型标签
        header = tk.Frame(inner, bg=COLOR_Q_BG)
        header.pack(fill='x', anchor='w')
        type_text = '选择题' if qtype == 'choice' else '论述题'
        type_color = COLOR_SUBTLE if qtype == 'choice' else COLOR_WARN
        tk.Label(header, text=f'第 {qid} 题',
                 font=FONT_BODY_B, bg=COLOR_Q_BG, fg=COLOR_TEXT).pack(side='left')
        tk.Label(header, text=f'  [{type_text}]',
                 font=FONT_SMALL, bg=COLOR_Q_BG, fg=type_color).pack(side='left')
        score_hint = '（10分）' if qtype == 'choice' else '（25分）'
        tk.Label(header, text=score_hint,
                 font=FONT_SMALL, bg=COLOR_Q_BG, fg=COLOR_SUBTLE).pack(side='left')

        # 题目内容
        tk.Label(inner, text=q['question'],
                 font=FONT_BODY, bg=COLOR_Q_BG, fg=COLOR_TEXT,
                 wraplength=700, justify='left', anchor='w'
                 ).pack(fill='x', pady=(8, 0))

        if qtype == 'choice':
            var = tk.StringVar(value='')
            self._choice_vars[qid] = var
            for opt in q.get('options', []):
                tk.Radiobutton(inner, text=opt, variable=var,
                               value=opt[0],   # 取 'A'/'B'/'C'/'D'
                               font=FONT_BODY, bg=COLOR_Q_BG, fg=COLOR_TEXT,
                               activebackground=COLOR_Q_BG,
                               selectcolor=COLOR_Q_BG,
                               anchor='w').pack(fill='x', pady=(4, 0))
        else:
            tk.Label(inner, text='请在下方输入你的答案：',
                     font=FONT_SMALL, bg=COLOR_Q_BG, fg=COLOR_SUBTLE
                     ).pack(anchor='w', pady=(10, 4))
            txt = tk.Text(inner, font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                          relief='flat', wrap='word',
                          highlightbackground=COLOR_BORDER, highlightthickness=1,
                          padx=8, pady=6, height=6)
            txt.pack(fill='x')
            self._essay_texts[qid] = txt

    def _on_submit(self):
        # 收集答案
        answers = {}
        for qid, var in self._choice_vars.items():
            answers[qid] = var.get()
        for qid, txt in self._essay_texts.items():
            answers[qid] = txt.get('1.0', 'end').strip()

        # 检查是否有未答的选择题
        unanswered = [qid for qid, var in self._choice_vars.items() if not var.get()]
        if unanswered:
            ok = messagebox.askyesno('有题未答',
                                     f'有 {len(unanswered)} 道选择题未作答，确定提交吗？')
            if not ok:
                return

        self._pending_answers = answers
        self._show_grading()

    # ══════════════════════════════════════════════
    # 第四步：AI 批改（加载中）
    # ══════════════════════════════════════════════
    def _show_grading(self):
        self._clear()
        frame = tk.Frame(self, bg=COLOR_BG)
        frame.place(relx=0.5, rely=0.45, anchor='center')
        tk.Label(frame, text='AI 正在批改，请稍候...',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE).pack()
        tk.Label(frame, text='论述题批改需要较长时间，请耐心等待',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(pady=(8, 0))

        def do():
            try:
                from src.core.ai_client import grade_quiz
                results = grade_quiz(self._questions, self._pending_answers)
                self.after(0, lambda: self._show_result(results))
            except Exception as e:
                self.after(0, lambda: self._on_grade_error(str(e)))

        threading.Thread(target=do, daemon=True).start()

    def _on_grade_error(self, msg: str):
        messagebox.showerror('批改失败', f'AI 批改时出错：\n{msg}')
        self._show_answer()

    # ══════════════════════════════════════════════
    # 第五步：结果展示
    # ══════════════════════════════════════════════
    def _show_result(self, results: list):
        self._results = results
        self._clear()

        total_score = sum(r['score'] for r in results)
        full_score  = sum(r['full_score'] for r in results)
        pct         = round(total_score / full_score * 100) if full_score else 0
        score_color = COLOR_OK if pct >= 60 else COLOR_ERR

        # ── 底部（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='重新测验',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=9,
                  activebackground='#333333',
                  command=self._show_select).pack(side='right', padx=24, pady=12)

        tk.Button(bottom, text='← 返回',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_back).pack(side='right', padx=(0, 8), pady=12)

        # ── 得分区 ──
        score_area = tk.Frame(self, bg=COLOR_BG)
        score_area.pack(fill='x', padx=32, pady=(28, 0))
        tk.Label(score_area, text='测验完成',
                 font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')

        score_row = tk.Frame(score_area, bg=COLOR_BG)
        score_row.pack(anchor='w', pady=(12, 0))
        tk.Label(score_row, text=f'{total_score}',
                 font=FONT_SCORE, bg=COLOR_BG, fg=score_color).pack(side='left')
        tk.Label(score_row, text=f' / {full_score} 分  （{pct}%）',
                 font=FONT_BODY, bg=COLOR_BG, fg=score_color
                 ).pack(side='left', anchor='s', pady=(0, 6))

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(16, 0))
        tk.Label(self, text='详细点评',
                 font=FONT_BODY_B, bg=COLOR_BG, fg=COLOR_TEXT
                 ).pack(anchor='w', padx=32, pady=(14, 0))

        # ── 结果滚动区 ──
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=(8, 16))
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

        for r in results:
            self._render_result_card(rf, r)

    def _render_result_card(self, parent, r: dict):
        correct = r['correct']
        row_bg  = COLOR_OK_BG if correct else COLOR_ERR_BG
        bd_col  = '#B8DEB8' if correct else '#FFCCCC'

        card = tk.Frame(parent, bg=row_bg,
                        highlightbackground=bd_col, highlightthickness=1)
        card.pack(fill='x', pady=(0, 10), padx=2)
        inner = tk.Frame(card, bg=row_bg)
        inner.pack(fill='x', padx=16, pady=14)

        # 题号 + 得分
        header = tk.Frame(inner, bg=row_bg)
        header.pack(fill='x')
        mark = '✓' if correct else '✗'
        mark_color = COLOR_OK if correct else COLOR_ERR
        tk.Label(header, text=f'{mark}  第 {r["id"]} 题',
                 font=FONT_BODY_B, bg=row_bg, fg=mark_color).pack(side='left')
        tk.Label(header, text=f'  {r["score"]} / {r["full_score"]} 分',
                 font=FONT_BODY_B, bg=row_bg, fg=COLOR_TEXT).pack(side='left', padx=(12, 0))

        # 题目
        tk.Label(inner, text=r['question'],
                 font=FONT_BODY, bg=row_bg, fg=COLOR_TEXT,
                 wraplength=700, justify='left', anchor='w'
                 ).pack(fill='x', pady=(8, 0))

        # 选择题选项显示
        if r['type'] == 'choice':
            user_ans    = r['user_answer'] or ''
            correct_ans = r['correct_answer']
            for opt in r.get('options', []):
                letter = opt[0]   # 'A'/'B'/'C'/'D'
                is_correct_opt = (letter == correct_ans)
                is_user_opt    = (letter == user_ans)

                if is_correct_opt:
                    opt_bg = COLOR_OK_BG
                    opt_fg = COLOR_OK
                    suffix = '  ← 正确答案'
                elif is_user_opt and not correct:
                    opt_bg = COLOR_ERR_BG
                    opt_fg = COLOR_ERR
                    suffix = '  ← 你的答案'
                else:
                    opt_bg = row_bg
                    opt_fg = COLOR_SUBTLE
                    suffix = ''

                opt_row = tk.Frame(inner, bg=opt_bg,
                                   highlightbackground=COLOR_OK if is_correct_opt else (COLOR_ERR if (is_user_opt and not correct) else row_bg),
                                   highlightthickness=1 if (is_correct_opt or (is_user_opt and not correct)) else 0)
                opt_row.pack(fill='x', pady=(4, 0))
                tk.Label(opt_row, text=f'  {opt}{suffix}',
                         font=FONT_SMALL, bg=opt_bg, fg=opt_fg,
                         anchor='w', pady=4).pack(fill='x', padx=8)
        else:
            # 论述题：显示学生答案
            if r['user_answer']:
                tk.Label(inner, text='你的答案：',
                         font=FONT_SMALL, bg=row_bg, fg=COLOR_SUBTLE
                         ).pack(anchor='w', pady=(8, 2))
                ans_box = tk.Text(inner, font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                                  relief='flat', wrap='word', padx=6, pady=4,
                                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                                  height=4)
                ans_box.insert('1.0', r['user_answer'])
                ans_box.config(state='disabled')
                ans_box.pack(fill='x')

            # 参考答案
            tk.Label(inner, text='参考答案：',
                     font=FONT_SMALL, bg=row_bg, fg=COLOR_SUBTLE
                     ).pack(anchor='w', pady=(8, 2))
            ref_box = tk.Text(inner, font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                              relief='flat', wrap='word', padx=6, pady=4,
                              highlightbackground=COLOR_BORDER, highlightthickness=1,
                              height=4)
            ref_box.insert('1.0', r['correct_answer'])
            ref_box.config(state='disabled')
            ref_box.pack(fill='x')

        # AI 点评
        tk.Label(inner, text=f'💬 {r["comment"]}',
                 font=FONT_SMALL, bg=row_bg, fg=COLOR_TEXT,
                 wraplength=700, justify='left', anchor='w'
                 ).pack(fill='x', pady=(10, 0))

        # 论述题：加入错题本按钮
        if r['type'] == 'essay':
            already = wrong_question_exists(r['question'])
            btn_frame = tk.Frame(inner, bg=row_bg)
            btn_frame.pack(anchor='e', pady=(10, 0))
            if already:
                tk.Label(btn_frame, text='✓ 已在错题本',
                         font=FONT_SMALL, bg=row_bg, fg=COLOR_SUBTLE).pack(side='left')
            else:
                tk.Button(btn_frame, text='+ 加入错题本',
                          font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_WARN,
                          relief='flat', cursor='hand2', padx=10, pady=4,
                          highlightbackground='#E8D870', highlightthickness=1,
                          command=lambda q=r['question'], a=r['correct_answer'],
                                         b=btn_frame: self._add_to_wrong_book(q, a, b)
                          ).pack(side='left')

    def _add_to_wrong_book(self, question: str, ref_answer: str, btn_frame: tk.Frame):
        from datetime import datetime
        label = f'综合测验 · {datetime.now().strftime("%Y-%m-%d")}'
        add_wrong_question(question, ref_answer, label)
        # 按钮变成「已加入」提示
        for w in btn_frame.winfo_children():
            w.destroy()
        tk.Label(btn_frame, text='✓ 已加入错题本',
                 font=FONT_SMALL, bg=btn_frame.cget('bg'), fg=COLOR_OK).pack(side='left')

    # ══════════════════════════════════════════════
    # 工具方法
    # ══════════════════════════════════════════════
    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _on_back(self):
        if self.on_back:
            self.on_back()
