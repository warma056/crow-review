# 模块用途：设置页面，用于填写和保存 DeepSeek API Key

import tkinter as tk
from tkinter import messagebox
import os
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.config import load_config, save_config, get_api_key

COLOR_BG     = '#FFFFFF'
COLOR_TEXT   = '#111111'
COLOR_SUBTLE = '#666666'
COLOR_BORDER = '#DDDDDD'
COLOR_INPUT  = '#F5F5F5'
COLOR_BTN_BG = '#111111'
COLOR_BTN_FG = '#FFFFFF'
COLOR_OK     = '#2D7A2D'
COLOR_ERR    = '#B00020'
FONT_TITLE   = ('Microsoft YaHei', 16, 'bold')
FONT_BODY    = ('Microsoft YaHei', 13)
FONT_SMALL   = ('Microsoft YaHei', 11)


class SettingsPage(tk.Frame):
    """设置页面"""

    def __init__(self, master):
        super().__init__(master, bg=COLOR_BG)
        self._build_ui()

    def _build_ui(self):
        # ── 标题 ──
        tk.Label(self, text='设置', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT
                 ).pack(anchor='w', padx=32, pady=(24, 0))

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── API Key 区块 ──
        section = tk.Frame(self, bg=COLOR_BG)
        section.pack(fill='x', padx=32, pady=(24, 0))

        tk.Label(section, text='DeepSeek API Key',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')

        tk.Label(section,
                 text='在 platform.deepseek.com → API Keys 页面获取，充值后即可使用',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w', pady=(4, 8))

        # 输入框（密码样式，显示圆点）
        key_row = tk.Frame(section, bg=COLOR_BG)
        key_row.pack(fill='x')

        self.key_var = tk.StringVar(value=get_api_key())
        self.key_entry = tk.Entry(key_row, textvariable=self.key_var,
                                  font=FONT_BODY, bg=COLOR_INPUT,
                                  fg=COLOR_TEXT, relief='flat',
                                  highlightbackground=COLOR_BORDER,
                                  highlightthickness=1,
                                  show='●')
        self.key_entry.pack(side='left', fill='x', expand=True, ipady=7)

        # 显示/隐藏切换按钮
        self.show_var = tk.BooleanVar(value=False)
        tk.Button(key_row, text='显示',
                  font=FONT_SMALL,
                  bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2',
                  padx=10, pady=7,
                  highlightbackground=COLOR_BORDER,
                  highlightthickness=1,
                  command=self._toggle_show
                  ).pack(side='left', padx=(8, 0))

        # ── 连接测试状态 ──
        self.status_label = tk.Label(section, text='',
                                     font=FONT_SMALL, bg=COLOR_BG)
        self.status_label.pack(anchor='w', pady=(10, 0))

        # ── 按钮区 ──
        btn_row = tk.Frame(section, bg=COLOR_BG)
        btn_row.pack(anchor='w', pady=(16, 0))

        tk.Button(btn_row, text='保存',
                  font=FONT_BODY,
                  bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2',
                  padx=20, pady=8,
                  activebackground='#333333',
                  command=self._on_save
                  ).pack(side='left')

        tk.Button(btn_row, text='测试连接',
                  font=FONT_BODY,
                  bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2',
                  padx=16, pady=8,
                  highlightbackground=COLOR_BORDER,
                  highlightthickness=1,
                  command=self._on_test
                  ).pack(side='left', padx=(12, 0))

        # ── 说明文字 ──
        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(32, 0))

        info = tk.Frame(self, bg=COLOR_BG)
        info.pack(fill='x', padx=32, pady=(16, 0))

        tk.Label(info, text='关于费用',
                 font=('Microsoft YaHei', 13, 'bold'),
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')

        tips = [
            '• 个人学习使用量极小，10 元余额可使用数月',
            '• 每次提取关键词约消耗 0.001 元',
            '• 智能判题每题约消耗 0.0005 元',
            '• 充值地址：platform.deepseek.com → 充值',
        ]
        for tip in tips:
            tk.Label(info, text=tip, font=FONT_SMALL,
                     bg=COLOR_BG, fg=COLOR_SUBTLE,
                     justify='left').pack(anchor='w', pady=2)

    def _toggle_show(self):
        """切换 API Key 显示/隐藏"""
        if self.key_entry.cget('show') == '●':
            self.key_entry.config(show='')
        else:
            self.key_entry.config(show='●')

    def _on_save(self):
        """保存 API Key"""
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning('内容为空', '请填写 API Key')
            return
        config = load_config()
        config['api_key'] = key
        if save_config(config):
            self.status_label.config(text='✓ 已保存', fg=COLOR_OK)
        else:
            messagebox.showerror('保存失败', '写入配置文件失败，请检查文件权限')

    def _on_test(self):
        """在后台线程测试 API 连接，避免界面卡顿"""
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning('请先填写', '请先填写 API Key 再测试')
            return

        self.status_label.config(text='正在测试连接...', fg=COLOR_SUBTLE)
        self.update()

        def do_test():
            try:
                from src.core.ai_client import test_connection
                test_connection(key)
                self.after(0, lambda: self.status_label.config(
                    text='✓ 连接成功！API Key 有效',
                    fg=COLOR_OK))
            except Exception as e:
                self.after(0, lambda: self.status_label.config(
                    text=f'✗ {e}', fg=COLOR_ERR))

        threading.Thread(target=do_test, daemon=True).start()
