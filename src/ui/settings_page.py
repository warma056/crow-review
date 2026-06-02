# 模块用途：设置页面，用于配置 API 后端和 Key

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

        # ── AI 后端选择 ──
        provider_section = tk.Frame(self, bg=COLOR_BG)
        provider_section.pack(fill='x', padx=32, pady=(24, 0))

        tk.Label(provider_section, text='AI 后端',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')
        tk.Label(provider_section,
                 text='DeepSeek：云端 API，需要 Key 和网络；Ollama：本地大模型，无需联网',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w', pady=(4, 10))

        btn_row = tk.Frame(provider_section, bg=COLOR_BG)
        btn_row.pack(anchor='w')

        config = load_config()
        self.provider_var = tk.StringVar(value=config.get('api_provider', 'deepseek'))

        self.btn_deepseek = tk.Button(
            btn_row, text='DeepSeek',
            font=FONT_SMALL, relief='flat', cursor='hand2',
            padx=16, pady=6,
            command=lambda: self._switch_provider('deepseek')
        )
        self.btn_deepseek.pack(side='left')

        self.btn_ollama = tk.Button(
            btn_row, text='Ollama（本地）',
            font=FONT_SMALL, relief='flat', cursor='hand2',
            padx=16, pady=6,
            command=lambda: self._switch_provider('ollama')
        )
        self.btn_ollama.pack(side='left', padx=(8, 0))

        # ── DeepSeek 区块（不 pack，由 _refresh_provider_ui 控制）──
        self.deepseek_frame = tk.Frame(self, bg=COLOR_BG)

        tk.Label(self.deepseek_frame, text='DeepSeek API Key',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')
        tk.Label(self.deepseek_frame,
                 text='在 platform.deepseek.com → API Keys 页面获取，充值后即可使用',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w', pady=(4, 8))

        key_row = tk.Frame(self.deepseek_frame, bg=COLOR_BG)
        key_row.pack(fill='x')

        self.key_var = tk.StringVar(value=get_api_key())
        self.key_entry = tk.Entry(key_row, textvariable=self.key_var,
                                  font=FONT_BODY, bg=COLOR_INPUT,
                                  fg=COLOR_TEXT, relief='flat',
                                  highlightbackground=COLOR_BORDER,
                                  highlightthickness=1,
                                  show='●')
        self.key_entry.pack(side='left', fill='x', expand=True, ipady=7)

        tk.Button(key_row, text='显示',
                  font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=10, pady=7,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._toggle_show
                  ).pack(side='left', padx=(8, 0))

        ds_btn_row = tk.Frame(self.deepseek_frame, bg=COLOR_BG)
        ds_btn_row.pack(anchor='w', pady=(12, 0))

        tk.Button(ds_btn_row, text='保存',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=20, pady=8,
                  activebackground='#333333',
                  command=self._on_save_deepseek
                  ).pack(side='left')

        tk.Button(ds_btn_row, text='测试连接',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=8,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_test
                  ).pack(side='left', padx=(12, 0))

        # ── Ollama 区块（不 pack，由 _refresh_provider_ui 控制）──
        self.ollama_frame = tk.Frame(self, bg=COLOR_BG)

        tk.Label(self.ollama_frame, text='Ollama 地址',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')
        tk.Label(self.ollama_frame,
                 text='Ollama 默认运行在本机 11434 端口，保持默认即可',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w', pady=(4, 8))

        self.ollama_url_var = tk.StringVar(
            value=config.get('ollama_base_url', 'http://localhost:11434'))
        tk.Entry(self.ollama_frame, textvariable=self.ollama_url_var,
                 font=FONT_BODY, bg=COLOR_INPUT, fg=COLOR_TEXT,
                 relief='flat', highlightbackground=COLOR_BORDER,
                 highlightthickness=1
                 ).pack(fill='x', ipady=7)

        tk.Label(self.ollama_frame, text='模型名称',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT
                 ).pack(anchor='w', pady=(16, 0))
        tk.Label(self.ollama_frame,
                 text='填写已通过 ollama pull 下载的模型名，如 qwen2.5:7b、llama3:8b',
                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(anchor='w', pady=(4, 8))

        self.ollama_model_var = tk.StringVar(
            value=config.get('ollama_model', 'qwen2.5:7b'))
        tk.Entry(self.ollama_frame, textvariable=self.ollama_model_var,
                 font=FONT_BODY, bg=COLOR_INPUT, fg=COLOR_TEXT,
                 relief='flat', highlightbackground=COLOR_BORDER,
                 highlightthickness=1
                 ).pack(fill='x', ipady=7)

        ol_btn_row = tk.Frame(self.ollama_frame, bg=COLOR_BG)
        ol_btn_row.pack(anchor='w', pady=(12, 0))

        tk.Button(ol_btn_row, text='保存',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=20, pady=8,
                  activebackground='#333333',
                  command=self._on_save_ollama
                  ).pack(side='left')

        tk.Button(ol_btn_row, text='测试连接',
                  font=FONT_BODY, bg=COLOR_BG, fg=COLOR_TEXT,
                  relief='flat', cursor='hand2', padx=16, pady=8,
                  highlightbackground=COLOR_BORDER, highlightthickness=1,
                  command=self._on_test
                  ).pack(side='left', padx=(12, 0))

        # ── 状态标签（两区块共用，由 _refresh_provider_ui 控制顺序）──
        self.status_label = tk.Label(self, text='', font=FONT_SMALL, bg=COLOR_BG)

        # ── 费用说明（由 _refresh_provider_ui 控制顺序）──
        self.info_sep   = tk.Frame(self, bg=COLOR_BORDER, height=1)
        self.info_frame = tk.Frame(self, bg=COLOR_BG)

        tk.Label(self.info_frame, text='关于费用',
                 font=('Microsoft YaHei', 13, 'bold'),
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(anchor='w')

        tips = [
            '• 个人学习使用量极小，10 元余额可使用数月',
            '• 每次提取关键词约消耗 0.001 元',
            '• 智能判题每题约消耗 0.0005 元',
            '• 充值地址：platform.deepseek.com → 充值',
            '• 使用 Ollama 本地模型无需任何费用',
        ]
        for tip in tips:
            tk.Label(self.info_frame, text=tip, font=FONT_SMALL,
                     bg=COLOR_BG, fg=COLOR_SUBTLE,
                     justify='left').pack(anchor='w', pady=2)

        # 初始化显示
        self._refresh_provider_ui()

    # ──────────────────────────────────────────
    # provider 切换
    # ──────────────────────────────────────────

    def _switch_provider(self, provider: str):
        self.provider_var.set(provider)
        self._refresh_provider_ui()

    def _refresh_provider_ui(self):
        """先全部隐藏，再按正确顺序重新 pack，避免顺序错乱"""
        provider = self.provider_var.get()

        # 按钮高亮
        if provider == 'deepseek':
            self.btn_deepseek.config(bg=COLOR_BTN_BG, fg=COLOR_BTN_FG)
            self.btn_ollama.config(bg=COLOR_BG, fg=COLOR_TEXT,
                                   highlightbackground=COLOR_BORDER,
                                   highlightthickness=1)
        else:
            self.btn_ollama.config(bg=COLOR_BTN_BG, fg=COLOR_BTN_FG)
            self.btn_deepseek.config(bg=COLOR_BG, fg=COLOR_TEXT,
                                     highlightbackground=COLOR_BORDER,
                                     highlightthickness=1)

        # 全部隐藏
        self.deepseek_frame.pack_forget()
        self.ollama_frame.pack_forget()
        self.status_label.pack_forget()
        self.info_sep.pack_forget()
        self.info_frame.pack_forget()

        # 按顺序重新 pack
        if provider == 'deepseek':
            self.deepseek_frame.pack(fill='x', padx=32, pady=(20, 0))
        else:
            self.ollama_frame.pack(fill='x', padx=32, pady=(20, 0))

        self.status_label.pack(anchor='w', padx=32, pady=(10, 0))
        self.info_sep.pack(fill='x', padx=32, pady=(28, 0))
        self.info_frame.pack(fill='x', padx=32, pady=(16, 0))

        self.status_label.config(text='')

    # ──────────────────────────────────────────
    # 保存
    # ──────────────────────────────────────────

    def _on_save_deepseek(self):
        key = self.key_var.get().strip()
        if not key:
            messagebox.showwarning('内容为空', '请填写 API Key')
            return
        config = load_config()
        config['api_provider'] = 'deepseek'
        config['api_key'] = key
        if save_config(config):
            self.status_label.config(text='✓ 已保存', fg=COLOR_OK)
        else:
            messagebox.showerror('保存失败', '写入配置文件失败，请检查文件权限')

    def _on_save_ollama(self):
        url   = self.ollama_url_var.get().strip()
        model = self.ollama_model_var.get().strip()
        if not url or not model:
            messagebox.showwarning('内容为空', '请填写 Ollama 地址和模型名称')
            return
        config = load_config()
        config['api_provider']    = 'ollama'
        config['ollama_base_url'] = url
        config['ollama_model']    = model
        if save_config(config):
            self.status_label.config(text='✓ 已保存', fg=COLOR_OK)
        else:
            messagebox.showerror('保存失败', '写入配置文件失败，请检查文件权限')

    # ──────────────────────────────────────────
    # 测试连接
    # ──────────────────────────────────────────

    def _toggle_show(self):
        if self.key_entry.cget('show') == '●':
            self.key_entry.config(show='')
        else:
            self.key_entry.config(show='●')

    def _on_test(self):
        # FIX: 测试前先保存当前界面上的设置，否则测的是旧 config 里的 provider
        provider = self.provider_var.get()
        config = load_config()
        if provider == 'ollama':
            url   = self.ollama_url_var.get().strip()
            model = self.ollama_model_var.get().strip()
            if not url or not model:
                self.status_label.config(text='✗ 请先填写 Ollama 地址和模型名称', fg=COLOR_ERR)
                return
            config['api_provider']    = 'ollama'
            config['ollama_base_url'] = url
            config['ollama_model']    = model
        else:
            key = self.key_var.get().strip()
            if not key:
                self.status_label.config(text='✗ 请先填写 API Key', fg=COLOR_ERR)
                return
            config['api_provider'] = 'deepseek'
            config['api_key']      = key
        save_config(config)

        self.status_label.config(text='正在测试连接...', fg=COLOR_SUBTLE)
        self.update()

        def do_test():
            try:
                from src.core.ai_client import test_connection
                msg = test_connection()
                self.after(0, lambda: self.status_label.config(
                    text=f'✓ {msg}', fg=COLOR_OK))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda m=err_msg: self.status_label.config(
                    text=f'✗ {m}', fg=COLOR_ERR))

        threading.Thread(target=do_test, daemon=True).start()
