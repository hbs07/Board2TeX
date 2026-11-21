# -*- coding: utf-8 -*-
"""vault/db.py —— SQLite 错题本(主责: D 李若宸;骨架: A 提供)

验证命令(已实现,单测在 tests/test_acceptance.py):
    python -m pytest -q -k vault
期望结果: 增/查/按课程筛选/删除 全部通过。

AI 辅助说明: 见 README「诚信声明」。

表结构(冻结接口,不许改字段名):
    problems(id, course, tags, tex, image_path, created_at)

设计约定:
    - tags 存库前用英文逗号 join 成一个字符串(如 "极限,第一章"),查出来再 split;
    - course 参数: None/不传 = 不筛选,返回全部(参考文档 §3.2 的 search);
    - 每次写操作(增/删)后 con.commit(),别忘了;
    - 桌面单进程使用,连接由调用方(init_db)返回并保管,用完在 GUI 退出时 close。

与其他模块的关系:
    - 调用方是 D 自己的 GUI 控件("存入错题本"按钮、错题本列表页);
    - 不在识别主链路上,未实现时调用会抛出明确的 NotImplementedError。
"""

from __future__ import annotations

import sqlite3


def init_db(path: str = "vault/board2tex.db") -> sqlite3.Connection:
    """连接(必要时创建)SQLite 库并建表,返回连接对象。

    CREATE TABLE IF NOT EXISTS 保证重复调用不报错。
    """
    con = sqlite3.connect(path)
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS problems (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            course     TEXT NOT NULL,
            tags       TEXT NOT NULL DEFAULT '',
            tex        TEXT NOT NULL,
            image_path TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    con.commit()
    return con


def add_problem(con: sqlite3.Connection, course: str, tags: list[str],
                tex: str, image_path: str) -> None:
    """插入一条错题记录。tags 是列表,入库前 join(",")。"""
    con.execute(
        "INSERT INTO problems (course, tags, tex, image_path) VALUES (?, ?, ?, ?)",
        (course, ",".join(tags), tex, image_path),
    )
    con.commit()


def list_problems(con: sqlite3.Connection) -> list[tuple]:
    """返回全部记录,按 id 倒序(最新的在前)。

    列序固定: (id, course, tags, tex, image_path, created_at)。
    """
    return con.execute(
        "SELECT id, course, tags, tex, image_path, created_at "
        "FROM problems ORDER BY id DESC"
    ).fetchall()


def search(con: sqlite3.Connection, course: str | None = None) -> list[tuple]:
    """按课程筛选;course 为 None 时等价于 list_problems。"""
    if course is None:
        return list_problems(con)
    return con.execute(
        "SELECT id, course, tags, tex, image_path, created_at "
        "FROM problems WHERE course = ? ORDER BY id DESC",
        (course,),
    ).fetchall()


def delete_problem(con: sqlite3.Connection, pid: int) -> None:
    """按 id 删除记录。"""
    con.execute("DELETE FROM problems WHERE id = ?", (pid,))
    con.commit()
