# AI 填空复习工具

一个帮助学生高效复习的桌面应用。上传学习资料（Word/PDF/PPT），AI 自动识别章节和问答结构，只在答案部分挖空，填空练习帮你记住关键知识点。

## 功能一览

**核心流程**：导入资料 → AI 分析 → 填空练习 → 查看得分

- 📝 **填空练习**：AI 自动从答案中提取关键词挖空，问题完整显示作为参考
- ✏️ **综合测验**：AI 自动出选择题和论述题，答完由 AI 批改并给出详细点评
- 👁️ **遮盖模式**：答案折叠遮盖，凭记忆回忆后点击展开对照
- 🔍 **校对标注**：AI 识别不准时，可手动切换段落类型、选词加入关键词
- 📊 **练习记录**：历次得分一目了然，间隔重复提醒复习
- ❌ **错题本**：答错的关键词自动汇总，针对薄弱项专项练习
- 📖 **奖励阅读**：导入小说作为奖励，练习得分越高解锁越多章节
- ⚙️ **双 AI 后端**：支持 DeepSeek 云端（推荐）和 Ollama 本地大模型

## 安装使用

### 环境要求
- Python 3.10+
- Windows 10/11

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/warma056/crow-review.git
cd crow-review

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

### 配置 AI 后端

**方式一：DeepSeek 云端（推荐）**
1. 前往 [platform.deepseek.com](https://platform.deepseek.com) 注册并充值（10 元可用数月）
2. 在 API Keys 页面创建 Key
3. 打开程序 → 设置 → 填入 API Key → 保存

**方式二：Ollama 本地**
1. 下载安装 [Ollama](https://ollama.com)
2. 命令行执行 `ollama pull qwen2.5:7b`（或更小的 `qwen2.5:1.5b`）
3. 打开程序 → 设置 → 切换到 Ollama → 保存

### 打包为 exe

```bash
pyinstaller --onefile --windowed --name "AI填空复习工具" main.py
```

## 使用流程

1. 打开程序，点「我的资料」→「导入新资料」
2. 上传 Word/PDF/PPT 文件，或直接粘贴文字
3. 等待 AI 分析（DeepSeek 几秒，Ollama 几分钟）
4. 在章节列表中选择小节，点「开始练习」
5. 在灰色输入框中填写关键词，提交查看得分

## 技术栈

- Python 3.12 + tkinter（原生 GUI）
- DeepSeek API / Ollama（AI 后端）
- SQLite（本地数据存储）
- python-docx / pdfplumber / python-pptx（文件解析）

## 项目结构

```
├── main.py              # 程序入口
├── src/
│   ├── core/            # 核心逻辑（AI、数据库、配置、文件解析）
│   └── ui/              # 界面页面（13 个页面 + 主题模块）
├── docs/                # 设计文档
└── requirements.txt     # Python 依赖
```

## 许可证

MIT License
