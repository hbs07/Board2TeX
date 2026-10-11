# -*- coding: utf-8 -*-
"""vault/db.py —— SQLite 错题本(主责: D 李若宸;骨架: A 提供)

验证命令(先按《分工_D_应用与评估.md》§3.3 写好 tests/test_vault.py 再跑):
    pytest tests/test_vault.py -v
期望结果: 3 个测试全绿(增/查/按课程搜)。

AI 辅助范围(课程要求):
    本骨架由 AI 依据《分工_D_应用与评估.md》§3 生成函数签名、类型注解、
    文档字符串;四个函数体均为待实现,由 D 独立完成并替换。

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

    要点: CREATE TABLE IF NOT EXISTS 保证重复调用不报错。
    参考实现:《分工_D_应用与评估.md》§3.1。
    """
    # TODO(D): 参考文档 §3.1 实现(约 7 行)
    raise NotImplementedError("vault.init_db 待 D 实现")


def add_problem(con: sqlite3.Connection, course: str, tags: list[str],
                tex: str, image_path: str) -> None:
    """插入一条错题记录。tags 是列表,入库前 join(",")。

    参考实现: 文档 §3.2 的 add_problem(created_at 用 datetime('now'))。
    """
    # TODO(D): 参考文档 §3.2 实现(约 4 行)
    raise NotImplementedError("vault.add_problem 待 D 实现")


def list_problems(con: sqlite3.Connection) -> list[tuple]:
    """返回全部记录,按 id 倒序(最新的在前)。参考实现: 文档 §3.2。"""
    # TODO(D): 参考文档 §3.2 实现(1 行)
    raise NotImplementedError("vault.list_problems 待 D 实现")


def search(con: sqlite3.Connection, course: str | None = None) -> list[tuple]:
    """按课程筛选;course 为 None 时等价于 list_problems。参考实现: 文档 §3.2。"""
    # TODO(D): 参考文档 §3.2 实现(约 4 行)
    raise NotImplementedError("vault.search 待 D 实现")


def delete_problem(con: sqlite3.Connection, pid: int) -> None:
    """按 id 删除记录。参考实现: 文档 §3.2。"""
    # TODO(D): 参考文档 §3.2 实现(约 3 行)
    raise NotImplementedError("vault.delete_problem 待 D 实现")
