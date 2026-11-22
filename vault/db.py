# -*- coding: utf-8 -*-
"""vault/db.py —— 笔记库(SQLite)(主责: D 李若宸)

一个"笔记"= 一份可以不断追加的 LaTeX 正文;主界面识别完可以存入/追加,
笔记窗口里可以新建、预览、删除。

表结构(2026-11-22 起):
    notes(id, title, body, created_at, updated_at)
    body 只存 LaTeX 正文(不含模板头尾),预览时再套模板。

验证命令:
    python -m pytest -q -k notes

AI 辅助说明: 见 README「诚信声明」。
"""

from __future__ import annotations

import sqlite3

SEP = "\n\n\\newpage\n\n"      # 多次追加之间的分页符


def init_db(path: str = "vault/board2tex.db") -> sqlite3.Connection:
    """连接(必要时创建)SQLite 库并建表,返回连接对象。"""
    con = sqlite3.connect(path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT NOT NULL,
            body       TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        )
        """
    )
    con.commit()
    return con


def create_note(con: sqlite3.Connection, title: str) -> int:
    """新建一份空笔记,返回 id。标题为空时用"未命名笔记"。"""
    title = (title or "").strip() or "未命名笔记"
    cur = con.execute("INSERT INTO notes (title) VALUES (?)", (title,))
    con.commit()
    return int(cur.lastrowid)


def list_notes(con: sqlite3.Connection) -> list[tuple]:
    """返回 [(id, title, updated_at), ...],最近更新的在前。"""
    return con.execute(
        "SELECT id, title, updated_at FROM notes ORDER BY updated_at DESC, id DESC"
    ).fetchall()


def get_note(con: sqlite3.Connection, note_id: int) -> tuple[str, str] | None:
    """返回 (title, body);不存在返回 None。"""
    row = con.execute(
        "SELECT title, body FROM notes WHERE id = ?", (note_id,)
    ).fetchone()
    return (row[0], row[1]) if row else None


def append_to_note(con: sqlite3.Connection, note_id: int, body: str) -> None:
    """把一段 LaTeX 正文追加到笔记末尾(分页符隔开),并刷新更新时间。"""
    row = con.execute("SELECT body FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        raise ValueError(f"笔记不存在: {note_id}")
    old = row[0] or ""
    new = body if not old.strip() else old.rstrip() + SEP + body.lstrip()
    con.execute(
        "UPDATE notes SET body = ?, updated_at = datetime('now','localtime') "
        "WHERE id = ?",
        (new, note_id),
    )
    con.commit()


def delete_note(con: sqlite3.Connection, note_id: int) -> None:
    con.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    con.commit()
