AI 填空复习工具

基于 DeepSeek API 的智能学习辅助桌面应用，将学习资料自动转化为多种练习模式，提升复习效率。


功能介绍
📥 导入资料
支持导入 Word（.docx）、PDF、或直接粘贴文本，AI 自动识别章节结构、问答内容和关键词。
✍️ 填空练习
只在答案部分挖空，问题完整显示。支持严格匹配和 AI 语义判题两种模式。
🫣 遮盖模式
答案块默认折叠，凭记忆回忆后点击展开对照，适合快速过知识点。
📝 综合测验
跨多个小节自动出题，包含选择题和论述题，AI 批改并给出逐题点评。
📚 错题本
将综合测验中答错的论述题收入错题本，支持重新作答，AI 批改达标后移出。
⏰ 间隔复习提醒
为每个小节设置复习提醒日期，打开软件时自动显示今日待复习内容。
🎁 奖励阅读
导入小说作为奖励，每次练习完成自动解锁一段内容，得分越高解锁越多。

技术栈
技术用途Python 3.11主要开发语言tkinter桌面 GUI 界面DeepSeek APIAI 分析、出题、判题、批改SQLite本地数据持久化PyInstaller打包为单文件 .exe

项目结构
crow review/
├── main.py                  # 程序入口
├── requirements.txt         # 依赖列表
├── src/
│   ├── core/
│   │   ├── config.py        # 配置管理
│   │   ├── db.py            # 数据库操作
│   │   ├── ai_client.py     # DeepSeek API 封装
│   │   └── file_parser.py   # 文件解析
│   └── ui/
│       ├── material_list_page.py   # 资料列表
│       ├── import_page.py          # 导入资料
│       ├── analyze_page.py         # AI 分析进度
│       ├── section_list_page.py    # 章节列表
│       ├── review_page.py          # 人工校对
│       ├── practice_page.py        # 填空练习
│       ├── cover_page.py           # 遮盖模式
│       ├── quiz_page.py            # 综合测验
│       ├── result_page.py          # 练习结果
│       ├── wrong_book_page.py      # 错题本
│       ├── reward_book_page.py     # 奖励阅读
│       ├── history_page.py         # 练习记录
│       └── settings_page.py        # 设置

使用方法
直接运行（需要 Python 环境）
bashpip install -r requirements.txt
python main.py
打包为 exe
bashpyinstaller --onefile --windowed --name "AI填空复习工具" main.py

配置
首次运行后，在软件「设置」页填入 DeepSeek API Key。
API Key 申请地址：platform.deepseek.com

开发说明

所有耗时操作（AI 分析、判题、出题、批改）均在子线程执行，界面不会假死
数据库和配置文件存储在 exe 同级目录，数据本地持久化
UI 采用黑白主色调，字体 Microsoft YaHei
