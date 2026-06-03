# 模块用途：练习结果页，展示得分和每道题的对错明细

import tkinter as tk
from tkinter import ttk
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import insert_session, get_section, get_all_reward_books, unlock_chunks, get_unlocked_count



class ResultPage(tk.Frame):

    def __init__(self, master, section_id: int, results: list, mode: str,
                 on_retry=None, on_back=None, on_read_reward=None):
        """
        on_retry       : 再练一次，传入 section_id
        on_back        : 返回章节列表
        on_read_reward : 去读奖励小说，传入 book_id
        """
        super().__init__(master, bg=COLOR_BG)
        self.section_id     = section_id
        self.results        = results
        self.mode           = mode
        self.on_retry       = on_retry
        self.on_back        = on_back
        self.on_read_reward = on_read_reward

        sec = get_section(section_id)
        self._section_title   = sec['title']    if sec else ''
        self._material_id     = sec['material_id'] if sec else None

        total   = len(results)
        correct = sum(1 for r in results if r['correct'])
        self._score   = round(correct / total * 100) if total else 0
        self._correct = correct
        self._total   = total

        self._save_record()
        self._unlocked_count = self._do_unlock()  # 本次解锁了几段
        self._reward_book_id = self._get_active_book()
        self._build_ui()

    def _do_unlock(self) -> int:
        """根据得分解锁段落，返回本次解锁数量"""
        books = get_all_reward_books()
        if not books:
            return 0
        book_id = books[0]['id']   # 默认对第一本书解锁
        if self._score >= 90:
            count = 3
        elif self._score >= 60:
            count = 2
        else:
            count = 1
        return unlock_chunks(book_id, count)

    def _get_active_book(self) -> int | None:
        books = get_all_reward_books()
        return books[0]['id'] if books else None

    def _save_record(self):
        if not self._material_id:
            return
        try:
            import json
            insert_session(
                section_id  = self.section_id,
                material_id = self._material_id,
                score       = self._score,
                total       = self._total,
                correct     = self._correct,
                detail_json = json.dumps(self.results, ensure_ascii=False),
                mode        = self.mode
            )
        except Exception:
            pass

    def _build_ui(self):
        # ── 底部按钮（先 pack）──
        bottom = tk.Frame(self, bg=COLOR_BG,
                          highlightbackground=COLOR_BORDER,
                          highlightthickness=1)
        bottom.pack(fill='x', side='bottom')

        tk.Button(bottom, text='再练一次',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=9,
                  activebackground='#333333',
                  command=self._on_retry).pack(side='right', padx=24, pady=12)

        tk.Button(bottom, text='返回章节列表',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=9,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_back).pack(side='right', padx=(0, 8), pady=12)

        # 有奖励书才显示「去读奖励」按钮
        if self._reward_book_id:
            tk.Button(bottom, text='📖 去读奖励 →',
                      font=FONT_BODY, bg='#2D7A2D', fg=COLOR_BTN_FG,
                      relief='flat', cursor='hand2', padx=20, pady=9,
                      activebackground='#1f5a1f',
                      command=self._on_read_reward_click
                      ).pack(side='left', padx=24, pady=12)

        # ── 得分区 ──
        score_area = tk.Frame(self, bg=COLOR_BG)
        score_area.pack(fill='x', padx=32, pady=(28, 0))

        tk.Label(score_area, text='练习完成',
                 font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')
        tk.Label(score_area, text=self._section_title,
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w', pady=(4, 0))

        score_row = tk.Frame(score_area, bg=COLOR_BG)
        score_row.pack(anchor='w', pady=(12, 0))

        score_color = COLOR_OK if self._score >= 60 else COLOR_ERR
        tk.Label(score_row, text=f'{self._score}',
                 font=FONT_SCORE, bg=COLOR_BG, fg=score_color).pack(side='left')
        tk.Label(score_row, text='分',
                 font=FONT_BODY, bg=COLOR_BG, fg=score_color
                 ).pack(side='left', anchor='s', pady=(0, 8))
        tk.Label(score_row,
                 text=f'  答对 {self._correct} / {self._total} 题  ·  '
                      f'{"严格模式" if self.mode == "strict" else "智能模式"}',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(side='left', anchor='s', pady=(0, 8))

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(16, 0))

        # 解锁提示
        if self._reward_book_id and self._unlocked_count > 0:
            unlocked_total = get_unlocked_count(self._reward_book_id)
            tip = tk.Frame(self, bg='#F0FAF0',
                           highlightbackground='#B8DEB8',
                           highlightthickness=1)
            tip.pack(fill='x', padx=32, pady=(10, 0))
            tk.Label(tip,
                     text=f'🎉 本次解锁了 {self._unlocked_count} 段奖励内容！'
                          f'  累计已解锁 {unlocked_total} 段，点左下角「去读奖励」继续阅读',
                     font=FONT_SMALL, bg='#F0FAF0', fg='#2D7A2D',
                     justify='left').pack(anchor='w', padx=12, pady=8)

        tk.Label(self, text='答题明细',
                 font=FONT_BODY_B, bg=COLOR_BG, fg=COLOR_TEXT
                 ).pack(anchor='w', padx=32, pady=(14, 0))

        # ── 明细列表 ──
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=(8, 16))

        canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient='vertical', command=canvas.yview)
        list_frame = tk.Frame(canvas, bg=COLOR_BG)
        list_frame.bind('<Configure>',
                        lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=list_frame, anchor='nw')
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(
                            int(-1 * e.delta / 120), 'units'))

        for r in self.results:
            self._build_row(list_frame, r)

    def _build_row(self, parent, r: dict):
        kw      = r['keyword']
        answer  = r['answer'] or '（未填写）'
        correct = r['correct']
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
                 font=FONT_BODY_B, bg=row_bg, fg=COLOR_TEXT).pack(side='left', padx=(8, 0))
        if not correct:
            tk.Label(inner, text=f'你填的：{answer}',
                     font=FONT_BODY, bg=row_bg, fg=COLOR_ERR
                     ).pack(side='left', padx=(20, 0))

    def _on_read_reward_click(self):
        if self.on_read_reward and self._reward_book_id:
            self.on_read_reward(self._reward_book_id)

    def _on_retry(self):
        if self.on_retry:
            self.on_retry(self.section_id)

    def _on_back(self):
        if self.on_back:
            self.on_back()
