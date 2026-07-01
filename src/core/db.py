# 模块用途：初始化 SQLite 数据库
# 打包后数据库保存到 exe 所在目录，确保数据持久化

import sqlite3
import os
import sys
import json
from datetime import datetime


def _get_app_dir() -> str:
    """
    获取数据存储目录：
    - 打包为 exe 时：exe 文件所在目录
    - 直接运行 py 时：项目根目录
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')


def _get_db_path() -> str:
    return os.path.join(_get_app_dir(), 'app.db')


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL,
            content      TEXT    NOT NULL,
            analyzed     INTEGER DEFAULT 0,
            folder       TEXT    DEFAULT '',
            created_at   TEXT    NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sections (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id  INTEGER NOT NULL,
            title        TEXT    NOT NULL,
            order_index  INTEGER NOT NULL,
            content      TEXT    NOT NULL,
            blocks       TEXT    DEFAULT '[]',
            keywords     TEXT    DEFAULT '[]',
            reviewed     INTEGER DEFAULT 0,
            created_at   TEXT    NOT NULL,
            FOREIGN KEY (material_id) REFERENCES materials(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id   INTEGER NOT NULL,
            material_id  INTEGER NOT NULL,
            score        REAL    NOT NULL,
            total        INTEGER NOT NULL,
            correct      INTEGER NOT NULL,
            detail       TEXT    DEFAULT '[]',
            mode         TEXT    NOT NULL,
            created_at   TEXT    NOT NULL,
            FOREIGN KEY (section_id)  REFERENCES sections(id),
            FOREIGN KEY (material_id) REFERENCES materials(id)
        )
    ''')

    # 奖励小说
    c.execute('''
        CREATE TABLE IF NOT EXISTS reward_books (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            title        TEXT    NOT NULL,
            total_chunks INTEGER NOT NULL DEFAULT 0,
            chunk_size   INTEGER NOT NULL DEFAULT 500,
            created_at   TEXT    NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS reward_chunks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id      INTEGER NOT NULL,
            chunk_index  INTEGER NOT NULL,
            content      TEXT    NOT NULL,
            FOREIGN KEY (book_id) REFERENCES reward_books(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS reward_unlocks (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id      INTEGER NOT NULL,
            chunk_index  INTEGER NOT NULL,
            unlocked_at  TEXT    NOT NULL,
            UNIQUE(book_id, chunk_index)
        )
    ''')

    # 间隔复习提醒
    c.execute('''
        CREATE TABLE IF NOT EXISTS review_reminders (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            section_id   INTEGER NOT NULL UNIQUE,
            remind_date  TEXT    NOT NULL,
            created_at   TEXT    NOT NULL,
            FOREIGN KEY (section_id) REFERENCES sections(id)
        )
    ''')

    # 错题本（论述题）
    c.execute('''
        CREATE TABLE IF NOT EXISTS wrong_book (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            question       TEXT    NOT NULL,
            ref_answer     TEXT    NOT NULL,
            source_label   TEXT    NOT NULL,
            added_at       TEXT    NOT NULL
        )
    ''')

    # ── 自动升级：老数据库的 materials 表可能没有 folder 字段，检测并补上 ──
    cols = [r['name'] for r in c.execute("PRAGMA table_info(materials)").fetchall()]
    if 'folder' not in cols:
        c.execute("ALTER TABLE materials ADD COLUMN folder TEXT DEFAULT ''")

    conn.commit()
    conn.close()


# ── 资料操作 ──

def insert_material(name: str, content: str) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO materials (name, content, analyzed, created_at) VALUES (?, ?, 0, ?)',
        (name, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def get_all_materials() -> list:
    conn = get_conn()
    rows = conn.execute(
        'SELECT id, name, analyzed, folder, created_at FROM materials ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_material_folder(material_id: int, folder: str):
    """把某条资料移动到指定文件夹；folder 传空字符串表示「未分类」"""
    conn = get_conn()
    conn.execute(
        'UPDATE materials SET folder = ? WHERE id = ?',
        (folder or '', material_id)
    )
    conn.commit()
    conn.close()


def get_all_folders() -> list:
    """返回所有非空文件夹名（去重，按名称排序）"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT folder FROM materials "
        "WHERE folder IS NOT NULL AND folder != '' ORDER BY folder"
    ).fetchall()
    conn.close()
    return [r['folder'] for r in rows]


def get_material(material_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute('SELECT * FROM materials WHERE id = ?', (material_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def set_material_analyzed(material_id: int):
    conn = get_conn()
    conn.execute('UPDATE materials SET analyzed = 1 WHERE id = ?', (material_id,))
    conn.commit()
    conn.close()


def delete_material(material_id: int):
    conn = get_conn()
    rows = conn.execute(
        'SELECT id FROM sections WHERE material_id = ?', (material_id,)
    ).fetchall()
    for row in rows:
        conn.execute('DELETE FROM sessions WHERE section_id = ?', (row['id'],))
    conn.execute('DELETE FROM sections WHERE material_id = ?', (material_id,))
    conn.execute('DELETE FROM materials WHERE id = ?', (material_id,))
    conn.commit()
    conn.close()


# ── 小节操作 ──

def insert_section(material_id: int, title: str, order_index: int,
                   content: str, blocks: list, keywords: list) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO sections
           (material_id, title, order_index, content, blocks, keywords, reviewed, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 0, ?)''',
        (material_id, title, order_index, content,
         json.dumps(blocks, ensure_ascii=False),
         json.dumps(keywords, ensure_ascii=False),
         datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def get_sections_by_material(material_id: int) -> list:
    conn = get_conn()
    rows = conn.execute(
        '''SELECT id, title, order_index, reviewed, keywords
           FROM sections WHERE material_id = ?
           ORDER BY order_index ASC''',
        (material_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_section(section_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute('SELECT * FROM sections WHERE id = ?', (section_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d['blocks']   = json.loads(d['blocks'])
    d['keywords'] = json.loads(d['keywords'])
    return d


def update_section_blocks_keywords(section_id: int, blocks: list, keywords: list):
    conn = get_conn()
    conn.execute(
        'UPDATE sections SET blocks = ?, keywords = ?, reviewed = 1 WHERE id = ?',
        (json.dumps(blocks, ensure_ascii=False),
         json.dumps(keywords, ensure_ascii=False),
         section_id)
    )
    conn.commit()
    conn.close()


def update_section_keywords(section_id: int, keywords: list):
    conn = get_conn()
    conn.execute(
        'UPDATE sections SET keywords = ? WHERE id = ?',
        (json.dumps(keywords, ensure_ascii=False), section_id)
    )
    conn.commit()
    conn.close()


def delete_sections_by_material(material_id: int):
    conn = get_conn()
    rows = conn.execute(
        'SELECT id FROM sections WHERE material_id = ?', (material_id,)
    ).fetchall()
    for row in rows:
        conn.execute('DELETE FROM sessions WHERE section_id = ?', (row['id'],))
    conn.execute('DELETE FROM sections WHERE material_id = ?', (material_id,))
    conn.execute('UPDATE materials SET analyzed = 0 WHERE id = ?', (material_id,))
    conn.commit()
    conn.close()


# ── 练习记录操作 ──

def insert_session(section_id: int, material_id: int, score: float,
                   total: int, correct: int, detail_json: str, mode: str) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO sessions
           (section_id, material_id, score, total, correct, detail, mode, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (section_id, material_id, score, total, correct, detail_json, mode,
         datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def get_sessions_by_material(material_id: int) -> list:
    conn = get_conn()
    rows = conn.execute(
        '''SELECT s.id, s.score, s.total, s.correct, s.mode, s.created_at,
                  sec.title as section_title
           FROM sessions s
           JOIN sections sec ON s.section_id = sec.id
           WHERE s.material_id = ?
           ORDER BY s.created_at DESC''',
        (material_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_sessions() -> list:
    conn = get_conn()
    rows = conn.execute(
        '''SELECT s.id, s.score, s.total, s.correct, s.mode, s.created_at,
                  sec.title as section_title,
                  m.name   as material_name
           FROM sessions s
           JOIN sections  sec ON s.section_id  = sec.id
           JOIN materials m   ON s.material_id = m.id
           ORDER BY s.created_at DESC'''
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_detail(session_id: int) -> dict | None:
    """返回单次练习的完整信息，含解析后的每题明细 detail（列表）。
    detail 每项形如 {'keyword': 正确答案, 'answer': 用户作答, 'correct': 是否正确}"""
    conn = get_conn()
    row = conn.execute(
        '''SELECT s.id, s.score, s.total, s.correct, s.mode, s.detail, s.created_at,
                  sec.title as section_title,
                  m.name   as material_name
           FROM sessions s
           JOIN sections  sec ON s.section_id  = sec.id
           JOIN materials m   ON s.material_id = m.id
           WHERE s.id = ?''',
        (session_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    try:
        d['detail'] = json.loads(d['detail']) if d['detail'] else []
    except (json.JSONDecodeError, TypeError):
        d['detail'] = []
    return d


# ── 奖励小说操作 ──

def insert_reward_book(title: str, chunks: list, chunk_size: int = 500) -> int:
    """导入一本小说，chunks 是切好的段落列表"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO reward_books (title, total_chunks, chunk_size, created_at) VALUES (?, ?, ?, ?)',
        (title, len(chunks), chunk_size, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    book_id = c.lastrowid
    for i, content in enumerate(chunks):
        c.execute(
            'INSERT INTO reward_chunks (book_id, chunk_index, content) VALUES (?, ?, ?)',
            (book_id, i, content)
        )
    conn.commit()
    conn.close()
    return book_id


def get_all_reward_books() -> list:
    conn = get_conn()
    rows = conn.execute(
        'SELECT id, title, total_chunks, chunk_size, created_at FROM reward_books ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_reward_book(book_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute('SELECT * FROM reward_books WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_reward_book(book_id: int):
    conn = get_conn()
    conn.execute('DELETE FROM reward_chunks WHERE book_id = ?', (book_id,))
    conn.execute('DELETE FROM reward_unlocks WHERE book_id = ?', (book_id,))
    conn.execute('DELETE FROM reward_books WHERE id = ?', (book_id,))
    conn.commit()
    conn.close()


def get_unlocked_count(book_id: int) -> int:
    conn = get_conn()
    row = conn.execute(
        'SELECT COUNT(*) as cnt FROM reward_unlocks WHERE book_id = ?', (book_id,)
    ).fetchone()
    conn.close()
    return row['cnt'] if row else 0


def unlock_chunks(book_id: int, count: int):
    """解锁接下来 count 个段落（跳过已解锁的）"""
    conn = get_conn()
    unlocked = conn.execute(
        'SELECT chunk_index FROM reward_unlocks WHERE book_id = ? ORDER BY chunk_index',
        (book_id,)
    ).fetchall()
    unlocked_set = {r['chunk_index'] for r in unlocked}

    total = conn.execute(
        'SELECT total_chunks FROM reward_books WHERE id = ?', (book_id,)
    ).fetchone()['total_chunks']

    added = 0
    for i in range(total):
        if added >= count:
            break
        if i not in unlocked_set:
            conn.execute(
                'INSERT OR IGNORE INTO reward_unlocks (book_id, chunk_index, unlocked_at) VALUES (?, ?, ?)',
                (book_id, i, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            added += 1

    conn.commit()
    conn.close()
    return added


def get_chunk(book_id: int, chunk_index: int) -> str | None:
    conn = get_conn()
    row = conn.execute(
        'SELECT content FROM reward_chunks WHERE book_id = ? AND chunk_index = ?',
        (book_id, chunk_index)
    ).fetchone()
    conn.close()
    return row['content'] if row else None


def is_chunk_unlocked(book_id: int, chunk_index: int) -> bool:
    conn = get_conn()
    row = conn.execute(
        'SELECT id FROM reward_unlocks WHERE book_id = ? AND chunk_index = ?',
        (book_id, chunk_index)
    ).fetchone()
    conn.close()
    return row is not None


# ── 复习提醒操作 ──

def set_reminder(section_id: int, remind_date: str):
    """设置或更新某小节的复习提醒日期（格式 YYYY-MM-DD）"""
    conn = get_conn()
    conn.execute(
        '''INSERT INTO review_reminders (section_id, remind_date, created_at)
           VALUES (?, ?, ?)
           ON CONFLICT(section_id) DO UPDATE SET remind_date=excluded.remind_date,
                                                  created_at=excluded.created_at''',
        (section_id, remind_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    conn.close()


def delete_reminder(section_id: int):
    conn = get_conn()
    conn.execute('DELETE FROM review_reminders WHERE section_id = ?', (section_id,))
    conn.commit()
    conn.close()


def get_reminder(section_id: int) -> str | None:
    """返回该小节的提醒日期字符串，没有则返回 None"""
    conn = get_conn()
    row = conn.execute(
        'SELECT remind_date FROM review_reminders WHERE section_id = ?', (section_id,)
    ).fetchone()
    conn.close()
    return row['remind_date'] if row else None


def get_due_reminders() -> list:
    """返回今天及之前到期的所有提醒，含小节标题和资料名"""
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_conn()
    rows = conn.execute(
        '''SELECT r.section_id, r.remind_date,
                  sec.title as section_title,
                  sec.material_id,
                  m.name as material_name
           FROM review_reminders r
           JOIN sections  sec ON r.section_id  = sec.id
           JOIN materials m   ON sec.material_id = m.id
           WHERE r.remind_date <= ?
           ORDER BY r.remind_date ASC''',
        (today,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_reminders() -> list:
    """返回所有提醒（含未到期），用于章节列表展示"""
    conn = get_conn()
    rows = conn.execute(
        'SELECT section_id, remind_date FROM review_reminders'
    ).fetchall()
    conn.close()
    return {r['section_id']: r['remind_date'] for r in rows}


# ── 错题本操作 ──

def add_wrong_question(question: str, ref_answer: str, source_label: str) -> int:
    """加入错题本，source_label 例如「综合测验·2024-01-01」"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO wrong_book (question, ref_answer, source_label, added_at) VALUES (?, ?, ?, ?)',
        (question, ref_answer, source_label, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    )
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return new_id


def get_all_wrong_questions() -> list:
    conn = get_conn()
    rows = conn.execute(
        'SELECT * FROM wrong_book ORDER BY added_at DESC'
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_wrong_question(wrong_id: int):
    conn = get_conn()
    conn.execute('DELETE FROM wrong_book WHERE id = ?', (wrong_id,))
    conn.commit()
    conn.close()


def wrong_question_exists(question: str) -> bool:
    """避免重复加入同一道题"""
    conn = get_conn()
    row = conn.execute(
        'SELECT id FROM wrong_book WHERE question = ?', (question,)
    ).fetchone()
    conn.close()
    return row is not None
