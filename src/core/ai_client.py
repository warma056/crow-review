# 模块用途：封装 DeepSeek API
# 功能：1.全文分析（章节识别+问答标注+关键词提取）  2.智能判题

import json
import requests
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.config import get_api_key

API_URL = 'https://api.deepseek.com/v1/chat/completions'
MODEL   = 'deepseek-chat'
TIMEOUT = 60


def _chat(messages: list, api_key: str) -> str:
    """底层调用 DeepSeek API，返回模型回复文本"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    payload = {
        'model': MODEL,
        'messages': messages,
        'temperature': 0.1,
        'max_tokens': 4096
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        raise ConnectionError('请求超时，请检查网络后重试')
    except requests.exceptions.ConnectionError:
        raise ConnectionError('无法连接到 DeepSeek 服务，请检查网络')
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 401:
            raise ValueError('API Key 无效或已过期，请在设置中重新填写')
        elif code == 402:
            raise ValueError('账户余额不足，请前往 DeepSeek 平台充值')
        elif code == 429:
            raise ConnectionError('请求过于频繁，请稍后再试')
        else:
            raise ConnectionError(f'服务器错误（{code}），请稍后再试')
    except (KeyError, IndexError):
        raise ValueError('API 返回格式异常，请重试')


# ──────────────────────────────────────────────
# 全文分析：章节识别 + 问答标注 + 关键词提取
# ──────────────────────────────────────────────

def analyze_material(full_text: str, api_key: str = None,
                     progress_callback=None) -> list:
    """
    对全文进行一次性分析，返回小节列表。
    每个小节结构：
    {
        'title': str,         # 章节标题
        'blocks': [           # 段落块列表
            {
                'type': 'question' | 'answer' | 'text',
                'content': str
            }, ...
        ],
        'keywords': [str, ...]  # 仅从 answer 块中提取的关键词
    }

    progress_callback(current, total, message): 进度回调，可选
    """
    if api_key is None:
        api_key = get_api_key()
    if not api_key:
        raise ValueError('尚未设置 API Key，请先前往设置页填写')

    # 分段处理：将全文按 1500 字一块切分，逐块分析后合并
    chunks = _split_text(full_text, chunk_size=4000)
    total  = len(chunks)
    all_sections = []

    for i, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(i + 1, total, f'正在分析第 {i+1}/{total} 段...')

        sections = _analyze_chunk(chunk, api_key)
        all_sections.extend(sections)

    # 合并标题相同的相邻小节（跨块被切断的情况）
    merged = _merge_sections(all_sections)
    return merged


def _split_text(text: str, chunk_size: int = 4000) -> list:
    """按行分割文本，每块不超过 chunk_size 字符，尽量在段落边界切断"""
    lines  = text.split('\n')
    chunks = []
    current = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # +1 for '\n'
        if current_len + line_len > chunk_size and current:
            chunks.append('\n'.join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append('\n'.join(current))

    return chunks if chunks else [text]


def _analyze_chunk(chunk: str, api_key: str) -> list:
    """
    分析一个文本块，返回其中包含的小节列表。
    每节包含 title、blocks、keywords。
    """
    prompt = f"""你是一个专业的学习资料分析助手。请分析以下学习资料片段，完成三项任务：

1. 识别章节标题（如"第一节"、"Chapter 1"、"一、"等形式的标题）
2. 将每个章节的内容分成段落块，判断每块是"问题"还是"答案"还是"说明文字"
3. 仅从"答案"类型的段落中提取关键词（专业术语、核心概念），用于填空练习

返回格式为 JSON 数组，结构如下（只返回 JSON，不要任何其他文字）：
[
  {{
    "title": "章节标题（如果没有明显标题则用内容前10字概括）",
    "blocks": [
      {{"type": "question", "content": "问题原文"}},
      {{"type": "answer",   "content": "答案原文"}},
      {{"type": "text",     "content": "说明或过渡文字"}}
    ],
    "keywords": ["关键词1", "关键词2"]
  }}
]

判断规则：
- 以问号结尾、或包含"是什么""如何""为什么""请分析""试述"等提问词的段落 → question
- 紧跟在问题后面的解释性内容、带序号①②③的段落、带"答："前缀的段落 → answer  
- 章节标题行、过渡句、单独的小标题 → text
- 关键词只从 answer 块提取，控制在 5-15 个，选最核心的专业词汇

待分析内容：
{chunk}"""

    raw = _chat([{'role': 'user', 'content': prompt}], api_key)
    return _parse_json_response(raw)


def _parse_json_response(raw: str) -> list:
    """解析 AI 返回的 JSON，容错处理"""
    raw = raw.strip()
    # 去掉可能的 markdown 代码块包裹
    if raw.startswith('```'):
        lines = raw.split('\n')
        raw = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
    raw = raw.strip()

    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
        return []
    except json.JSONDecodeError:
        # 尝试找到第一个 [ 到最后一个 ] 之间的内容
        start = raw.find('[')
        end   = raw.rfind(']')
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start:end+1])
            except Exception:
                pass
        return []


def _merge_sections(sections: list) -> list:
    """合并标题相同的相邻小节（跨块切断的情况）"""
    if not sections:
        return []
    merged = [sections[0]]
    for sec in sections[1:]:
        if sec['title'] == merged[-1]['title']:
            merged[-1]['blocks'].extend(sec['blocks'])
            # 关键词去重合并
            existing = set(merged[-1]['keywords'])
            for kw in sec['keywords']:
                if kw not in existing:
                    merged[-1]['keywords'].append(kw)
                    existing.add(kw)
        else:
            merged.append(sec)
    return merged


# ──────────────────────────────────────────────
# 智能判题
# ──────────────────────────────────────────────

def judge_answer(question_word: str, user_answer: str, api_key: str = None) -> bool:
    """
    智能判题：判断用户答案与标准答案语义是否一致。
    返回 True（正确）或 False（错误）
    """
    if api_key is None:
        api_key = get_api_key()
    if not api_key:
        raise ValueError('尚未设置 API Key')

    if not user_answer.strip():
        return False

    prompt = f"""判断用户填写的答案与标准答案是否语义相同或基本一致。
标准答案：{question_word}
用户答案：{user_answer}
只返回一个单词：correct 或 wrong"""

    raw = _chat([{'role': 'user', 'content': prompt}], api_key).strip().lower()
    return 'correct' in raw


# ──────────────────────────────────────────────
# 连接测试
# ──────────────────────────────────────────────

def test_connection(api_key: str) -> str:
    """测试 API 连接，返回成功信息或抛出异常"""
    result = _analyze_chunk('第一节 测试\n法律是社会规范的一种。\n什么是法律？\n法律是由国家制定的行为规范。', api_key)
    if result:
        return f'连接成功'
    return '连接成功（返回为空，请检查文档格式）'


# ──────────────────────────────────────────────
# 综合测验：出题
# ──────────────────────────────────────────────

def generate_quiz(sections: list, api_key: str = None) -> dict:
    """
    根据多个小节内容自动出题。
    sections: [{'title': str, 'content': str}, ...]
    返回：
    {
        'questions': [
            {
                'id': 1,
                'type': 'choice',          # 选择题
                'question': str,
                'options': ['A. ...', 'B. ...', 'C. ...', 'D. ...'],
                'answer': 'A'              # 正确选项字母
            },
            {
                'id': 2,
                'type': 'essay',           # 论述题
                'question': str,
                'answer': str              # 参考答案（含要点）
            }
        ]
    }
    """
    if api_key is None:
        api_key = get_api_key()
    if not api_key:
        raise ValueError('尚未设置 API Key')

    # 拼接所有小节内容，限制总长度避免超 token
    combined = ''
    for sec in sections:
        combined += f"\n\n【{sec['title']}】\n{sec['content']}"
    if len(combined) > 8000:
        combined = combined[:8000] + '\n\n（内容过长，已截取前段）'

    # 根据字数动态决定题目数量
    char_count = len(combined)
    n_choice = 3 if char_count < 2000 else 5
    n_essay  = 2 if char_count < 2000 else 3

    prompt = f"""你是一位专业的出题老师。请根据以下学习资料，出一套综合测验题。

要求：
- 选择题 {n_choice} 道：考查基础概念，四个选项（A/B/C/D），只有一个正确答案
- 论述题 {n_essay} 道：考查重点内容，要求学生综合分析，每题附上含要点的参考答案

返回格式为 JSON（只返回 JSON，不要任何其他文字）：
{{
  "questions": [
    {{
      "id": 1,
      "type": "choice",
      "question": "题目内容",
      "options": ["A. 选项一", "B. 选项二", "C. 选项三", "D. 选项四"],
      "answer": "A"
    }},
    {{
      "id": 2,
      "type": "essay",
      "question": "题目内容",
      "answer": "参考答案，列出主要得分要点"
    }}
  ]
}}

学习资料：
{combined}"""

    raw = _chat([{'role': 'user', 'content': prompt}], api_key)

    raw = raw.strip()
    if raw.startswith('```'):
        lines = raw.split('\n')
        raw = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
    raw = raw.strip()

    try:
        result = json.loads(raw)
        if isinstance(result, dict) and 'questions' in result:
            return result
    except json.JSONDecodeError:
        start = raw.find('{')
        end   = raw.rfind('}')
        if start != -1 and end != -1:
            try:
                result = json.loads(raw[start:end+1])
                if isinstance(result, dict) and 'questions' in result:
                    return result
            except Exception:
                pass
    raise ValueError('AI 返回格式异常，请重试')


# ──────────────────────────────────────────────
# 综合测验：批改
# ──────────────────────────────────────────────

def grade_quiz(questions: list, user_answers: dict, api_key: str = None) -> list:
    """
    批改综合测验。
    questions   : generate_quiz 返回的题目列表
    user_answers: {question_id: answer_str}
    返回：
    [
        {
            'id': 1,
            'type': 'choice',
            'question': str,
            'user_answer': str,
            'correct_answer': str,
            'correct': True/False,
            'score': 10,          # 本题得分
            'full_score': 10,     # 本题满分
            'comment': str        # AI 点评
        },
        ...
    ]
    """
    if api_key is None:
        api_key = get_api_key()
    if not api_key:
        raise ValueError('尚未设置 API Key')

    results = []

    for q in questions:
        qid         = q['id']
        qtype       = q['type']
        user_ans    = user_answers.get(qid, '').strip()
        correct_ans = q.get('answer', '')

        if qtype == 'choice':
            # 选择题直接比对
            correct = user_ans.upper() == correct_ans.upper()
            results.append({
                'id':             qid,
                'type':           qtype,
                'question':       q['question'],
                'options':        q.get('options', []),
                'user_answer':    user_ans,
                'correct_answer': correct_ans,
                'correct':        correct,
                'score':          10 if correct else 0,
                'full_score':     10,
                'comment':        '回答正确！' if correct else f'正确答案是 {correct_ans}。'
            })
        else:
            # 论述题：调用 AI 批改
            if not user_ans:
                results.append({
                    'id':             qid,
                    'type':           qtype,
                    'question':       q['question'],
                    'options':        [],
                    'user_answer':    '',
                    'correct_answer': correct_ans,
                    'correct':        False,
                    'score':          0,
                    'full_score':     25,
                    'comment':        '未作答。'
                })
                continue

            prompt = f"""你是一位严格但公正的阅卷老师。请批改以下论述题答案。

题目：{q['question']}

参考答案要点：{correct_ans}

学生答案：{user_ans}

请按以下格式返回 JSON（只返回 JSON，不要其他文字）：
{{
  "score": 整数（0-25分），
  "comment": "点评内容：指出答到了哪些要点、遗漏了什么、有无错误，2-4句话"
}}"""

            try:
                raw = _chat([{'role': 'user', 'content': prompt}], api_key).strip()
                if raw.startswith('```'):
                    lines = raw.split('\n')
                    raw = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
                grade = json.loads(raw.strip())
                score   = int(grade.get('score', 0))
                comment = grade.get('comment', '')
            except Exception:
                score   = 0
                comment = 'AI 批改失败，请重试'

            results.append({
                'id':             qid,
                'type':           qtype,
                'question':       q['question'],
                'options':        [],
                'user_answer':    user_ans,
                'correct_answer': correct_ans,
                'correct':        score >= 15,
                'score':          score,
                'full_score':     25,
                'comment':        comment
            })

    return results
