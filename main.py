# 模块用途：程序入口，初始化数据库，启动主窗口

import tkinter as tk
from tkinter import messagebox
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'src'))

from core.db import init_db
from core.config import load_config
from src.ui.material_list_page import MaterialListPage
from src.ui.import_page import ImportPage
from src.ui.settings_page import SettingsPage
from src.ui.analyze_page import AnalyzePage
from src.ui.section_list_page import SectionListPage
from src.ui.review_page import ReviewPage
from src.ui.practice_page import PracticePage
from src.ui.result_page import ResultPage
from src.ui.history_page import HistoryPage
from src.ui.cover_page import CoverPage
from src.ui.reward_book_page import RewardBookPage
from src.ui.quiz_page import QuizPage
from src.ui.wrong_book_page import WrongBookPage

COLOR_BG    = '#FFFFFF'
COLOR_TEXT  = '#111111'
COLOR_SUBTLE= '#666666'
COLOR_BORDER= '#DDDDDD'
COLOR_BTN_BG= '#111111'
COLOR_BTN_FG= '#FFFFFF'
FONT_TITLE  = ('Microsoft YaHei', 16, 'bold')
FONT_BODY   = ('Microsoft YaHei', 13)
FONT_SMALL  = ('Microsoft YaHei', 11)


class MainApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('AI 填空复习工具')
        self.geometry('860x620')
        self.minsize(760, 520)
        self.configure(bg=COLOR_BG)
        self._center_window()
        self._build_topbar()
        self.content = tk.Frame(self, bg=COLOR_BG)
        self.content.pack(fill='both', expand=True)
        self._show_welcome()

    def _center_window(self):
        self.update_idletasks()
        w, h = 860, 620
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f'{w}x{h}+{x}+{y}')

    def _build_topbar(self):
        bar = tk.Frame(self, bg=COLOR_BG,
                       highlightbackground=COLOR_BORDER,
                       highlightthickness=1)
        bar.pack(fill='x', side='top')
        tk.Label(bar, text='AI 填空复习工具',
                 font=FONT_TITLE, bg=COLOR_BG,
                 fg=COLOR_TEXT).pack(side='left', padx=20, pady=12)
        for label, cmd in [('我的资料', self._on_nav_materials),
                            ('练习记录', self._on_nav_history),
                            ('错题本',   self._on_nav_wrong),
                            ('我的书',   self._on_nav_reward),
                            ('设  置',   self._on_nav_settings)]:
            tk.Button(bar, text=label, font=FONT_BODY,
                      bg=COLOR_BG, fg=COLOR_TEXT,
                      relief='flat', cursor='hand2',
                      activebackground=COLOR_BORDER,
                      command=cmd).pack(side='right', padx=12, pady=10)

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ── 欢迎页 ──
    def _show_welcome(self):
        self._clear()
        frame = tk.Frame(self.content, bg=COLOR_BG)
        frame.place(relx=0.5, rely=0.42, anchor='center')
        tk.Label(frame, text='欢迎使用 AI 填空复习工具',
                 font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_TEXT).pack(pady=(0, 12))
        tk.Label(frame,
                 text='上传学习资料，AI 自动识别章节结构，按小节填空复习。',
                 font=FONT_BODY, bg=COLOR_BG, fg=COLOR_SUBTLE).pack(pady=(0, 32))
        tk.Button(frame, text='开始 → 导入资料',
                  font=FONT_BODY, bg=COLOR_BTN_BG, fg=COLOR_BTN_FG,
                  relief='flat', cursor='hand2', padx=24, pady=10,
                  activebackground='#333333',
                  command=self._on_nav_materials).pack()
        if not load_config().get('api_key'):
            tk.Label(self.content,
                     text='⚠ 尚未设置 API Key，请先前往「设置」填写',
                     font=FONT_SMALL, bg=COLOR_BG, fg='#B00020'
                     ).place(relx=0.5, rely=0.82, anchor='center')

    # ── 资料列表 ──
    def _on_nav_materials(self):
        self._clear()
        MaterialListPage(
            self.content,
            on_import=self._show_import,
            on_select=self._show_analyze
        ).pack(fill='both', expand=True)

    # ── 导入资料 ──
    def _show_import(self):
        self._clear()
        ImportPage(
            self.content,
            on_success=self._after_import
        ).pack(fill='both', expand=True)

    def _after_import(self, material_id):
        if material_id:
            self._show_analyze(material_id)
        else:
            self._on_nav_materials()

    # ── 文档分析 ──
    def _show_analyze(self, material_id: int):
        self._clear()
        AnalyzePage(
            self.content,
            material_id=material_id,
            on_done=self._show_sections,
            on_back=self._on_nav_materials
        ).pack(fill='both', expand=True)

    # ── 章节列表 ──
    def _show_sections(self, material_id: int):
        self._clear()
        SectionListPage(
            self.content,
            material_id=material_id,
            on_practice=self._show_practice,
            on_review=self._show_review,
            on_reanalyze=self._show_analyze,
            on_back=self._on_nav_materials,
            on_cover=self._show_cover,
            on_quiz=self._show_quiz
        ).pack(fill='both', expand=True)

    # ── 人工校对 ──
    def _show_review(self, section_id: int):
        from src.core.db import get_section
        self._clear()
        sec = get_section(section_id)
        material_id = sec['material_id'] if sec else None
        ReviewPage(
            self.content,
            section_id=section_id,
            on_done=lambda sid: self._show_sections(material_id),
            on_back=lambda: self._show_sections(material_id)
        ).pack(fill='both', expand=True)

    # ── 填空练习 ──
    def _show_practice(self, section_id: int):
        from src.core.db import get_section
        self._clear()
        sec = get_section(section_id)
        material_id = sec['material_id'] if sec else None
        PracticePage(
            self.content,
            section_id=section_id,
            on_finish=self._show_result,
            on_back=lambda: self._show_sections(material_id)
        ).pack(fill='both', expand=True)

    # ── 练习结果 ──
    def _show_result(self, section_id: int, results: list, mode: str):
        from src.core.db import get_section
        self._clear()
        sec = get_section(section_id)
        material_id = sec['material_id'] if sec else None
        ResultPage(
            self.content,
            section_id=section_id,
            results=results,
            mode=mode,
            on_retry=self._show_practice,
            on_back=lambda: self._show_sections(material_id),
            on_read_reward=self._show_reward
        ).pack(fill='both', expand=True)

    # ── 遮盖模式 ──
    def _show_cover(self, section_id: int):
        from src.core.db import get_section
        self._clear()
        sec = get_section(section_id)
        material_id = sec['material_id'] if sec else None
        CoverPage(
            self.content,
            section_id=section_id,
            on_back=lambda: self._show_sections(material_id)
        ).pack(fill='both', expand=True)

    # ── 综合测验 ──
    def _show_quiz(self, material_id: int):
        self._clear()
        QuizPage(
            self.content,
            material_id=material_id,
            on_back=lambda: self._show_sections(material_id)
        ).pack(fill='both', expand=True)

    # ── 奖励阅读 ──
    def _show_reward(self, book_id: int = None):
        self._clear()
        RewardBookPage(
            self.content,
            book_id=book_id,
            on_back=self._on_nav_materials
        ).pack(fill='both', expand=True)

    def _on_nav_reward(self):
        self._show_reward()

    # ── 错题本 ──
    def _on_nav_wrong(self):
        self._clear()
        WrongBookPage(self.content,
                      on_back=self._on_nav_materials
                      ).pack(fill='both', expand=True)

    # ── 设置 ──
    def _on_nav_settings(self):
        self._clear()
        SettingsPage(self.content).pack(fill='both', expand=True)

    # ── 练习记录 ──
    def _on_nav_history(self):
        self._clear()
        HistoryPage(self.content).pack(fill='both', expand=True)


if __name__ == '__main__':
    try:
        init_db()
    except Exception as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror('启动错误', f'数据库初始化失败：\n{e}')
        sys.exit(1)
    app = MainApp()
    app.mainloop()
