"""
一键补丁：添加帮助页面和页内提示文字。
运行方式：在项目根目录（D:\crow review\）执行  python patch_help.py

做了什么：
1. main.py：添加帮助页面导入、导航按钮、跳转方法
2. practice_page.py：添加操作提示
3. history_page.py：添加操作提示
4. wrong_book_page.py：添加操作提示
"""

import os


def patch_main():
    """给 main.py 添加帮助页面入口"""
    path = 'main.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    changed = False

    # 1. 添加 import
    if 'HelpPage' not in content:
        content = content.replace(
            'from src.ui.wrong_book_page import WrongBookPage',
            'from src.ui.wrong_book_page import WrongBookPage\n'
            'from src.ui.help_page import HelpPage'
        )
        changed = True

    # 2. 导航栏添加「帮助」按钮（加在设置按钮后面，即列表最前面）
    if '_on_nav_help' not in content:
        content = content.replace(
            "for label, cmd in [('我的资料', self._on_nav_materials),",
            "for label, cmd in [('我的资料', self._on_nav_materials),\n"
            "                            ('帮  助',   self._on_nav_help),"
        )
        changed = True

    # 3. 添加帮助相关方法
    if 'def _on_nav_help' not in content:
        # 在 _on_nav_settings 方法后面添加
        help_methods = '''
    # ── 帮助 ──
    def _on_nav_help(self):
        self._clear()
        HelpPage(self.content,
                 on_back=self._on_nav_materials
                 ).pack(fill='both', expand=True)
'''
        content = content.replace(
            '    # ── 设置 ──\n    def _on_nav_settings(self):',
            help_methods + '    # ── 设置 ──\n    def _on_nav_settings(self):'
        )
        changed = True

    if changed:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  ✓ {path} — 添加帮助页面入口')
    else:
        print(f'  · {path} — 已有帮助入口，跳过')


def add_hint(filepath, anchor_text, hint_text):
    """在指定文本后面插入提示行"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if hint_text in content:
        print(f'  · {filepath} — 提示已存在，跳过')
        return

    if anchor_text not in content:
        print(f'  ✗ {filepath} — 找不到插入位置，跳过')
        return

    hint_block = (
        f"\n        tk.Label(self, text='{hint_text}',\n"
        f"                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE\n"
        f"                 ).pack(anchor='w', padx=32, pady=(4, 0))\n"
    )

    content = content.replace(anchor_text, anchor_text + hint_block, 1)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  ✓ {filepath} — 添加提示文字')


def patch_practice():
    """给 practice_page 添加提示"""
    fp = os.path.join('src', 'ui', 'practice_page.py')
    if not os.path.isfile(fp):
        print(f'  ✗ {fp} — 文件不存在')
        return

    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    hint = '💡 在灰色输入框中填写关键词，完成后点「提交答案」查看得分'
    if hint in content:
        print(f'  · {fp} — 提示已存在，跳过')
        return

    # 在分割线后面插入提示
    anchor = "tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))"
    if anchor not in content:
        print(f'  ✗ {fp} — 找不到插入位置')
        return

    hint_code = (
        f"\n        tk.Label(self, text='{hint}',\n"
        "                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE\n"
        "                 ).pack(anchor='w', padx=32, pady=(4, 0))\n"
    )
    content = content.replace(anchor, anchor + hint_code, 1)

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  ✓ {fp} — 添加提示文字')


def patch_history():
    """给 history_page 添加提示"""
    fp = os.path.join('src', 'ui', 'history_page.py')
    if not os.path.isfile(fp):
        print(f'  ✗ {fp} — 文件不存在')
        return

    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    hint = '💡 点击资料名可筛选记录，到期复习任务会在「我的资料」页面提醒'
    if hint in content:
        print(f'  · {fp} — 提示已存在，跳过')
        return

    anchor = "tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(14, 0))"
    if anchor not in content:
        print(f'  ✗ {fp} — 找不到插入位置')
        return

    hint_code = (
        f"\n        tk.Label(self, text='{hint}',\n"
        "                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE\n"
        "                 ).pack(anchor='w', padx=32, pady=(4, 0))\n"
    )
    content = content.replace(anchor, anchor + hint_code, 1)

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  ✓ {fp} — 添加提示文字')


def patch_wrong_book():
    """给 wrong_book_page 添加提示"""
    fp = os.path.join('src', 'ui', 'wrong_book_page.py')
    if not os.path.isfile(fp):
        print(f'  ✗ {fp} — 文件不存在')
        return

    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    hint = '💡 练习中答错的关键词会自动收集到这里，可针对薄弱项专项练习'
    if hint in content:
        print(f'  · {fp} — 提示已存在，跳过')
        return

    # wrong_book_page 需要找到合适的插入点
    # 找标题后面的分割线
    anchor = None
    for candidate in [
        "tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(12, 0))",
        "tk.Frame(self, bg=COLOR_BORDER, height=1).pack(fill='x', padx=32, pady=(14, 0))",
    ]:
        if candidate in content:
            anchor = candidate
            break

    if not anchor:
        # 尝试在标题 Label 后面插入
        if "'错题本'" in content or "'错题本'" in content:
            print(f'  ⚠ {fp} — 找不到分割线，请手动添加提示')
        else:
            print(f'  ✗ {fp} — 找不到插入位置')
        return

    hint_code = (
        f"\n        tk.Label(self, text='{hint}',\n"
        "                 font=FONT_SMALL, bg=COLOR_BG, fg=COLOR_SUBTLE\n"
        "                 ).pack(anchor='w', padx=32, pady=(4, 0))\n"
    )
    content = content.replace(anchor, anchor + hint_code, 1)

    with open(fp, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'  ✓ {fp} — 添加提示文字')


def main():
    if not os.path.isfile('main.py'):
        print('错误：找不到 main.py，请在项目根目录下运行此脚本')
        return

    print('添加帮助页面和页内提示...\n')
    patch_main()
    patch_practice()
    patch_history()
    patch_wrong_book()
    print(f'\n完成！运行 python main.py 验证。')


if __name__ == '__main__':
    main()
