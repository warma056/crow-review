# 模块用途：帮助页面，展示完整的使用说明

import tkinter as tk
from tkinter import ttk
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.ui.theme import *


# 帮助内容：(标题, 正文)
HELP_SECTIONS = [
    ('快速上手', (
        '三步开始复习：\n'
        '① 点「我的资料」→「导入新资料」，上传 Word/PDF/PPT 或直接粘贴文字\n'
        '② 等待 AI 自动分析章节结构和问答内容（通常几秒到几分钟）\n'
        '③ 在章节列表中点「开始练习」，填空作答后提交查看得分'
    )),
    ('导入资料', (
        '支持三种文件格式：Word (.docx)、PDF (.pdf)、PowerPoint (.pptx)。\n'
        '也可以直接把文字粘贴到输入框中。\n\n'
        '导入后需要给资料起一个名称，方便后续查找。\n'
        '同一份资料可以重新分析，不需要重复导入。'
    )),
    ('AI 分析', (
        'AI 会自动完成三件事：\n'
        '• 识别章节标题，把内容拆分成小节\n'
        '• 判断每个段落是「问题」「答案」还是「说明文字」\n'
        '• 从答案段落中提取关键词，用于填空练习\n\n'
        '分析结果不一定完美，可以在「校对标注」页面手动修正。'
    )),
    ('填空练习', (
        '练习页只在「答案」段落中挖空，「问题」段落完整显示作为参考。\n'
        '灰色输入框就是需要填写的空格，填入关键词后点「提交答案」。\n\n'
        '判题模式：\n'
        '• 严格模式：必须和标准答案完全一致才算对\n'
        '• 智能模式：AI 判断语义是否相近（需要联网或 Ollama）'
    )),
    ('校对标注', (
        '如果 AI 把问题错标成了答案，或者遗漏了关键词，可以在这里手动修正。\n\n'
        '操作方式：\n'
        '• 点段落上方的「问题」「答案」「说明」按钮切换段落类型\n'
        '• 在答案段落中用鼠标选中文字，点「加入关键词」\n'
        '• 右侧面板可以手动输入关键词或删除不需要的关键词\n'
        '• 修改完成后点「保存校对结果」'
    )),
    ('遮盖模式', (
        '答案段落默认用灰色遮盖，先凭记忆回忆，再点击展开对照。\n'
        '适合快速浏览式复习，不需要逐字填写。\n\n'
        '底部有「全部展开」和「全部折叠」按钮，方便批量操作。'
    )),
    ('综合测验', (
        '在章节列表页点右上角「综合测验 ✎」按钮进入。\n\n'
        '流程：选择小节（可多选）→ AI 自动出选择题和论述题 → 在线答题 → AI 批改 → 查看详细点评。\n\n'
        '选择题自动评分，论述题由 AI 根据参考答案逐条批改并给出分项得分。'
    )),
    ('错题本', (
        '每次练习中答错的关键词会自动记录到错题本。\n'
        '进入错题本可以针对这些薄弱项做专项填空练习。\n\n'
        '从顶部导航栏的「错题本」进入。'
    )),
    ('练习记录', (
        '记录所有历次练习的得分、答对数、使用模式和时间。\n'
        '可以按资料名筛选查看。\n\n'
        '系统会根据答题表现自动安排间隔重复复习提醒，\n'
        '到期的复习任务会在「我的资料」页面顶部显示红色提示。'
    )),
    ('奖励阅读', (
        '导入一本 .txt 格式的小说作为奖励，系统会把内容切成小段。\n'
        '每次完成练习后自动解锁一部分内容，得分越高解锁越多：\n'
        '• 90 分以上：解锁 3 段\n'
        '• 60 分以上：解锁 2 段\n'
        '• 60 分以下：解锁 1 段\n\n'
        '从顶部导航栏的「我的书」进入。'
    )),
    ('设置', (
        'AI 后端：\n'
        '• DeepSeek（推荐）：云端 API，速度快，需要联网和 API Key，少量费用\n'
        '• Ollama：本地大模型，免费但较慢，需要单独安装 Ollama 并下载模型\n\n'
        '界面设置：\n'
        '• 可以调整正文和标题的字体大小\n'
        '• 修改后需要重启程序才能生效'
    )),
]


class HelpPage(tk.Frame):
    """帮助页面"""

    def __init__(self, master, on_back=None):
        super().__init__(master, bg=COLOR_BG)
        self.on_back = on_back
        self._text_widgets = []
        self._build_ui()
        self.after(100, self._fix_heights)

    def _build_ui(self):
        # ── 顶部 ──
        top = tk.Frame(self, bg=COLOR_BG)
        top.pack(fill='x', padx=32, pady=(24, 0))

        tk.Label(top, text='使用帮助', font=FONT_TITLE,
                 bg=COLOR_BG, fg=COLOR_TEXT).pack(side='left')

        if self.on_back:
            tk.Button(top, text='← 返回',
                      font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_TEXT,
                      relief='flat', cursor='hand2', padx=12, pady=6,
                      highlightbackground=COLOR_BORDER, highlightthickness=1,
                      command=self.on_back).pack(side='right')

        tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))

        # ── 滚动区 ──
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill='both', expand=True, padx=32, pady=12)

        sb = tk.Scrollbar(outer, orient='vertical')
        sb.pack(side='right', fill='y')

        canvas = tk.Canvas(outer, bg=COLOR_BG, highlightthickness=0,
                           yscrollcommand=sb.set)
        canvas.pack(side='left', fill='both', expand=True)
        sb.config(command=canvas.yview)

        self._content = tk.Frame(canvas, bg=COLOR_BG)
        win = canvas.create_window((0, 0), window=self._content, anchor='nw')
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(win, width=e.width))
        self._content.bind('<Configure>',
                           lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind_all('<MouseWheel>',
                        lambda e: canvas.yview_scroll(int(-1 * e.delta / 120), 'units'))
        self._canvas = canvas

        # ── 渲染帮助内容 ──
        for i, (title, body) in enumerate(HELP_SECTIONS):
            self._render_section(title, body, i)

        # 底部留白
        tk.Frame(self._content, bg=COLOR_BG, height=32).pack()

    def _render_section(self, title: str, body: str, index: int):
        # 标题
        tk.Label(self._content, text=f'{index + 1}.  {title}',
                 font=FONT_BODY_B, bg=COLOR_BG, fg=COLOR_TEXT,
                 anchor='w').pack(fill='x', pady=(16 if index > 0 else 8, 4))

        # 正文
        frame = tk.Frame(self._content, bg=COLOR_Q_BG,
                         highlightbackground=COLOR_BORDER,
                         highlightthickness=1)
        frame.pack(fill='x', pady=(0, 4), padx=2)

        txt = tk.Text(frame, font=FONT_BODY, bg=COLOR_Q_BG, fg=COLOR_TEXT,
                      relief='flat', wrap='word',
                      padx=14, pady=10,
                      cursor='arrow', height=1)
        txt.insert('1.0', body)
        txt.config(state='disabled')
        txt.pack(fill='x')
        self._text_widgets.append(txt)

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
        self._canvas.configure(scrollregion=self._canvas.bbox('all'))
