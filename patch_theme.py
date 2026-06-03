"""
一键补丁：让所有 UI 页面从 theme.py 统一导入主题常量。
运行方式：在项目根目录（D:\crow review\）执行  python patch_theme.py

做了什么：
1. 在每个 src/ui/*.py 和 main.py 中，删除与 theme.py 重复的 COLOR_/FONT_ 定义
2. 添加 from src.ui.theme import * 导入语句
3. 不动页面特有的常量（如 COLOR_BLANK、COLOR_COVER 等）
"""

import os
import re

# theme.py 中已定义的共享常量名
THEME_CONSTANTS = {
    'COLOR_BG', 'COLOR_TEXT', 'COLOR_SUBTLE', 'COLOR_BORDER',
    'COLOR_BTN_BG', 'COLOR_BTN_FG',
    'COLOR_OK', 'COLOR_ERR', 'COLOR_OK_BG', 'COLOR_ERR_BG',
    'COLOR_WARN', 'COLOR_WARN_BG', 'COLOR_Q_BG', 'COLOR_INPUT',
    'FONT_FAMILY', 'FONT_TITLE', 'FONT_BODY', 'FONT_BODY_B',
    'FONT_SMALL', 'FONT_SCORE',
}

IMPORT_LINE = 'from src.ui.theme import *'

# 需要处理的文件
UI_DIR = os.path.join('src', 'ui')
FILES_TO_PATCH = []

# src/ui/ 下所有 .py（排除 theme.py 本身）
if os.path.isdir(UI_DIR):
    for f in os.listdir(UI_DIR):
        if f.endswith('.py') and f != 'theme.py' and f != '__init__.py':
            FILES_TO_PATCH.append(os.path.join(UI_DIR, f))

# main.py
if os.path.isfile('main.py'):
    FILES_TO_PATCH.append('main.py')


def patch_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    removed = []
    import_added = False
    # 正则：匹配 CONSTANT_NAME = 'xxx' 或 CONSTANT_NAME = (xxx) 形式的赋值
    const_re = re.compile(r'^(\w+)\s*=\s*')

    for line in lines:
        stripped = line.strip()

        # 跳过已有的 theme import（避免重复添加）
        if 'from src.ui.theme import' in stripped:
            continue

        m = const_re.match(stripped)
        if m:
            name = m.group(1)
            if name in THEME_CONSTANTS:
                removed.append(name)
                continue  # 删除这行

        # 找到合适位置插入 import（在最后一个 import/from 之后）
        if not import_added and stripped and not stripped.startswith('#') \
                and not stripped.startswith('import ') \
                and not stripped.startswith('from ') \
                and not stripped == '':
            # 到了第一行非 import/非注释/非空行，在这之前插入
            new_lines.append(IMPORT_LINE + '\n')
            new_lines.append('\n')
            import_added = True

        new_lines.append(line)

    # 如果文件全是 import 行（极端情况），追加到末尾
    if not import_added:
        new_lines.append('\n' + IMPORT_LINE + '\n')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    return removed


def main():
    if not os.path.isdir(UI_DIR):
        print(f'错误：找不到 {UI_DIR} 目录，请在项目根目录下运行此脚本')
        return

    print(f'即将处理 {len(FILES_TO_PATCH)} 个文件...\n')

    for fp in sorted(FILES_TO_PATCH):
        removed = patch_file(fp)
        status = f'删除 {len(removed)} 个重复常量' if removed else '无重复常量'
        print(f'  ✓ {fp}  —  {status}')

    print(f'\n完成！所有页面现在从 theme.py 统一读取主题。')
    print(f'请运行 python main.py 验证程序是否正常启动。')


if __name__ == '__main__':
    main()
