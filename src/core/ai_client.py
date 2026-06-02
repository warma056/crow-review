# 模块用途：封装 DeepSeek API / Ollama API
# 功能：1.全文分析（章节识别+问答标注+关键词提取）  2.智能判题

import json
import requests
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from src.core.config import get_api_key, load_config

# FIX: Ollama 本地模型 CPU 推理很慢，需要更长超时
# DeepSeek 云端用 60s，Ollama 本地用 300s
TIMEOUT_DEEPSEEK = 60
TIMEOUT_OLLAMA   = 600


def _get_api_params() -> tuple:
    """
    根据 config 返回 (api_url, model, api_key)。
    支持 DeepSeek 和 Ollama 两种 provider。
    """
    config = load_config()
    provider = config.get('api_provider', 'deepseek')

    if provider == 'ollama':
        base_url = config.get('ollama_base_url', 'http://localhost:11434')
        model    = config.get('ollama_model', 'qwen2.5:7b')
        api_url  = f"{base_url.rstrip('/')}/v1/chat/completions"
        api_key  = 'ollama'  # Ollama 不校验 key，传任意非空字符串即可
    else:
        api_url = 'https://api.deepseek.com/v1/chat/completions'
        model   = 'deepseek-chat'
        api_key = config.get('api_key', '') or get_api_key()

    return api_url, model, api_key


def _chat(messages: list, api_key: str = None) -> str:
    """底层调用 API，返回模型回复文本。api_key 参数保留用于测试连接时直接传入。"""
    api_url, model, _key = _get_api_params()
    # 若外部显式传入 api_key（如测试连接），优先使用
    if api_key:
        _key = api_key

    # FIX: 根据 provider 选择超时时间，Ollama 本地模型需要更长时间
    config = load_config()
    # (连接超时, 读取超时)：连接5秒判断服务是否在线，读取按模型速度等
    timeout = (5, TIMEOUT_OLLAMA) if config.get('api_provider') == 'ollama' else (10, TIMEOUT_DEEPSEEK)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {_key}'
    }
    payload = {
        'model': model,
        'messages': messages,
        'temperature': 0.1,
        'max_tokens': 4096
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
        resp.raise_for_status()
        return resp.json()['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        raise ConnectionError('请求超时，请检查网络后重试')
    except requests.exceptions.ConnectionError:
        raise ConnectionError('无法连接到服务，请检查网络或 Ollama 是否已启动')
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
        'title': str,
        'blocks': [{'type': 'question'|'answer'|'text', 'content': str}, ...],
        'keywords': [str, ...]
    }
    """
    if api_key is None:
        api_key = get_api_key()
    if not api_key:
        config = load_config()
        if config.get('api_provider') != 'ollama':
            raise ValueError('尚未设置 API Key，请先前往设置页填写')

    # FIX: Ollama 本地模型推理慢，缩小每段大小避免单次请求过久卡住
    config_now = load_config()
    chunk_size = 1500 if config_now.get('api_provider') == 'ollama' else 4000
    chunks = _split_text(full_text, chunk_size=chunk_size)
    total  = len(chunks)
    all_sections = []

    for i, chunk in enumerate(chunks):
        if progress_callback:
            progress_callback(i + 1, total, f'正在分析第 {i+1}/{total} 段...')
        sections = _analyze_chunk(chunk, api_key)
        all_sections.extend(sections)

    merged = _merge_sections(all_sections)
    return merged


def _split_text(text: str, chunk_size: int = 4000) -> list:
    lines  = text.split('\n')
    chunks = []
    current = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
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

    return _parse_json_response(_chat([{'role': 'user', 'content': prompt}], api_key))


def _parse_json_response(raw: str) -> list:
    raw = raw.strip()
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
        start = raw.find('[')
        end   = raw.rfind(']')
        if start != -1 and end != -1:
            try:
                return json.loads(raw[start:end+1])
            except Exception:
                pass
        return []


def _merge_sections(sections: list) -> list:
    if not sections:
        return []
    merged = [sections[0]]
    for sec in sections[1:]:
        if sec['title'] == merged[-1]['title']:
            merged[-1]['blocks'].extend(sec['blocks'])
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
    if api_key is None:
        api_key = get_api_key()

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

def test_connection(api_key: str = None) -> str:
    """测试 API 连接，返回成功信息或抛出异常"""
    config = load_config()
    provider = config.get('api_provider', 'deepseek')

    if provider == 'ollama':
        # Ollama: 直接 GET 基础 URL，不走 AI 分析，秒出结果
        base_url = config.get('ollama_base_url', 'http://localhost:11434')
        try:
            resp = requests.get(base_url.rstrip('/') + '/', timeout=5)
            if resp.status_code == 200:
                return '连接成功，Ollama 服务正常运行'
            raise ConnectionError(f'Ollama 返回异常状态码 {resp.status_code}')
        except requests.exceptions.ConnectionError:
            raise ConnectionError('无法连接到 Ollama，请确认已启动 Ollama')
        except requests.exceptions.Timeout:
            raise ConnectionError('连接 Ollama 超时，请检查地址是否正确')
    else:
        # DeepSeek: 用短文本测试 AI 是否正常返回
        result = _analyze_chunk(
            '第一节 测试\n什么是法律？\n法律是由国家制定的行为规范。',
            api_key or ''
        )
        if result:
            return '连接成功'
        raise ValueError('连接成功但模型未返回有效内容，请检查 API Key')


# ──────────────────────────────────────────────
# 综合测验：出题
# ──────────────────────────────────────────────

def generate_quiz(sections: list, api_key: str = None) -> dict:
    if api_key is None:
        api_key = get_api_key()

    combined = ''
    for sec in sections:
        combined += f"\n\n【{sec['title']}】\n{sec['content']}"
    if len(combined) > 8000:
        combined = combined[:8000] + '\n\n（内容过长，已截取前段）'

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
    if api_key is None:
        api_key = get_api_key()

    results = []

    for q in questions:
        qid         = q['id']
        qtype       = q['type']
        user_ans    = user_answers.get(qid, '').strip()
        correct_ans = q.get('answer', '')

        if qtype == 'choice':
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
