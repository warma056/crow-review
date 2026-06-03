# 模块用途：文档分析页，导入资料后触发 AI 全文分析，显示进度，完成后跳转章节列表

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys

from src.ui.theme import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.db import (get_material, insert_section, set_material_analyzed,
                          delete_sections_by_material, get_sections_by_material)
from src.core.ai_client import analyze_material
from src.core.config import get_api_key, load_config   # FIX: 增加 load_config



class AnalyzePage(tk.Frame):
    """文档分析页面：AI 全文分析进度展示"""

    def __init__(self, master, material_id: int, on_done=None, on_back=None):
        """
        on_done : 分析完成回调，传入 material_id
        on_back : 返回资料列表回调
        """
        super().__init__(master, bg=COLOR_BG)
        self.material_id = material_id
        self.on_done     = on_done
        self.on_back     = on_back
        self._mat        = get_material(material_id) or {}
        self._build_ui()
        # 如果已分析过，询问是否重新分析
        if self._mat.get('analyzed'):
            self.after(100, self._ask_reanalyze)
        else:
            self.after(100, self._start_analyze)

    def _build_ui(self):
        # ── 标题 ──
        tk.Label(self, text='正在分析文档',
                 font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT
                 ).pack(anchor='w', padx=32, pady=(32, 0))

        tk.Label(self, text=f'资料：{self._mat.get("name", "")}',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE
                 ).pack(anchor='w', padx=32, pady=(6, 0))

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(16, 0))

        # ── 进度区 ──
        center = tk.Frame(self, bg=COLOR_BG)
        center.place(relx=0.5, rely=0.45, anchor='center')

        self.icon_label = tk.Label(center, text='⏳',
                                   font=('Microsoft YaHei', 32),
                                   bg=COLOR_BG, fg=COLOR_TEXT)
        self.icon_label.pack(pady=(0, 16))

        self.status_label = tk.Label(center,
                                     text='准备中...',
                                     font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT)
        self.status_label.pack()

        self.sub_label = tk.Label(center,
                                  text='AI 正在识别章节结构和问答内容，请稍候',
                                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE)
        self.sub_label.pack(pady=(6, 0))

        # 进度条
        style = ttk.Style()
        style.configure('BW.Horizontal.TProgressbar',
                        troughcolor=COLOR_BORDER,
                        background=COLOR_TEXT,
                        thickness=6)
        self.progress = ttk.Progressbar(center, style='BW.Horizontal.TProgressbar',
                                        orient='horizontal', length=340, mode='determinate')
        self.progress.pack(pady=(20, 0))

        self.pct_label = tk.Label(center, text='',
                                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE)
        self.pct_label.pack(pady=(6, 0))

        # ── 取消按钮 ──
        self.cancel_btn = tk.Button(self, text='取消',
                                    font=FONT_BODY,
                                    bg=COLOR_BG, fg=COLOR_TEXT,
                                    relief='flat', cursor='hand2',
                                    padx=16, pady=8,
                                    highlightbackground=COLOR_BORDER,
                                    highlightthickness=1,
                                    command=self._on_back)
        self.cancel_btn.pack(side='bottom', pady=24)

    def _ask_reanalyze(self):
        """已有分析结果，询问是直接进入还是重新分析"""
        sections = get_sections_by_material(self.material_id)
        answer = messagebox.askyesno(
            '已有分析结果',
            f'这份资料之前已分析过，共识别出 {len(sections)} 个小节。\n\n'
            '是否重新分析？（选「否」直接进入章节列表）'
        )
        if answer:
            delete_sections_by_material(self.material_id)
            self._start_analyze()
        else:
            if self.on_done:
                self.on_done(self.material_id)

    def _start_analyze(self):
        """在后台线程启动 AI 分析"""
        # FIX: Ollama 不需要 API Key，只有 DeepSeek 才检查
        config = load_config()
        if config.get('api_provider', 'deepseek') != 'ollama' and not get_api_key():
            messagebox.showwarning('未设置 API Key',
                                   '请先前往「设置」填写 DeepSeek API Key')
            if self.on_back:
                self.on_back()
            return

        self._cancelled = False
        threading.Thread(target=self._do_analyze, daemon=True).start()

    def _do_analyze(self):
        """后台线程：调用 AI 分析全文，将结果写入数据库"""
        try:
            content = self._mat.get('content', '')

            def progress_cb(current, total, message):
                if self._cancelled:
                    return
                pct = int(current / total * 100)
                self.after(0, lambda: self._update_progress(current, total, pct, message))

            sections = analyze_material(content, progress_callback=progress_cb)

            if self._cancelled:
                return

            if not sections:
                self.after(0, lambda: self._on_error('AI 未能识别出任何章节，请检查文档格式'))
                return

            # 写入数据库
            for i, sec in enumerate(sections):
                insert_section(
                    material_id  = self.material_id,
                    title        = sec.get('title', f'第{i+1}节'),
                    order_index  = i,
                    content      = '\n'.join(
                        b['content'] for b in sec.get('blocks', [])
                    ),
                    blocks       = sec.get('blocks', []),
                    keywords     = sec.get('keywords', [])
                )

            set_material_analyzed(self.material_id)
            self.after(0, lambda: self._on_done(len(sections)))

        except Exception as e:
            if not self._cancelled:
                self.after(0, lambda: self._on_error(str(e)))

    def _update_progress(self, current, total, pct, message):
        self.status_label.config(text=message)
        self.progress['value'] = pct
        self.pct_label.config(text=f'{pct}%  （{current}/{total} 段）')

    def _on_done(self, section_count: int):
        self.icon_label.config(text='✓')
        self.status_label.config(
            text=f'分析完成！共识别出 {section_count} 个小节', fg=COLOR_OK)
        self.sub_label.config(text='即将跳转到章节列表...')
        self.progress['value'] = 100
        self.pct_label.config(text='100%')
        self.cancel_btn.config(text='进入章节列表', bg=COLOR_BTN_BG,
                               fg=COLOR_BTN_FG, command=lambda: self.on_done(self.material_id))
        # 1.5 秒后自动跳转
        self.after(1500, lambda: self.on_done(self.material_id) if self.on_done else None)

    def _on_error(self, msg: str):
        self.icon_label.config(text='✗')
        self.status_label.config(text='分析失败', fg=COLOR_ERR)
        self.sub_label.config(text=msg, fg=COLOR_ERR)
        self.cancel_btn.config(text='返回', command=self._on_back)
        messagebox.showerror('分析失败', msg)

    def _on_back(self):
        self._cancelled = True
        if self.on_back:
            self.on_back()
