# 模块用途：全局 UI 主题常量
# 所有页面从这里统一导入颜色和字体，不再各自定义
# 字体大小从 config.json 的 ui.font_size_base / ui.font_size_title 读取

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.config import load_config

# ── 读取配置 ──
_config = load_config()
_ui = _config.get('ui', {})
_FONT_SIZE_BASE  = _ui.get('font_size_base', 13)
_FONT_SIZE_TITLE = _ui.get('font_size_title', 16)

# ── 颜色 ──
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
COLOR_WARN    = '#996600'
COLOR_WARN_BG = '#FFFDF0'
COLOR_Q_BG    = '#F5F5F5'
COLOR_INPUT   = '#F5F5F5'

# ── 字体 ──
FONT_FAMILY = 'Microsoft YaHei'
FONT_TITLE  = (FONT_FAMILY, _FONT_SIZE_TITLE, 'bold')
FONT_BODY   = (FONT_FAMILY, _FONT_SIZE_BASE)
FONT_BODY_B = (FONT_FAMILY, _FONT_SIZE_BASE, 'bold')
FONT_SMALL  = (FONT_FAMILY, max(_FONT_SIZE_BASE - 2, 9))
FONT_SCORE  = (FONT_FAMILY, _FONT_SIZE_TITLE * 2, 'bold')
