# -*- coding: utf-8 -*-
"""
记忆管理模块 - MemoryManager
负责处理所有SQLite数据库操作，包括对话历史和用户信息的存储与检索
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class MemoryManager:
    """
    记忆管理器
    使用SQLite数据库存储对话历史和用户重要信息
    """

    def __init__(self, db_path: str = "memory.db"):
        """
        初始化记忆管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def _init_database(self):
        """初始化数据库表结构"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 对话历史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                emotion TEXT DEFAULT 'neutral',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 用户信息表（保存重要信息：姓名、喜好等）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 重要记忆表（AI提取的关键信息）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS important_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                source_conv_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_conv_id) REFERENCES conversations(id)
            )
        """)

        conn.commit()

    def save_message(self, role: str, content: str, emotion: str = "neutral") -> int:
        """
        保存一条消息到数据库

        Args:
            role: 角色（'user' 或 'assistant'）
            content: 消息内容
            emotion: 情绪标签

        Returns:
            新插入记录的ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (role, content, emotion) VALUES (?, ?, ?)",
            (role, content, emotion)
        )
        conn.commit()
        return cursor.lastrowid

    def get_recent_conversations(self, limit: int = 20) -> List[Dict]:
        """
        获取最近的对话记录

        Args:
            limit: 返回的最大条数

        Returns:
            对话记录列表，格式为 [{"role": ..., "content": ...}, ...]
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT role, content, emotion, timestamp
               FROM conversations
               ORDER BY timestamp DESC
               LIMIT ?""",
            (limit,)
        )
        rows = cursor.fetchall()
        # 反转顺序，使最旧的在前
        result = []
        for row in reversed(rows):
            result.append({
                "role": row["role"],
                "content": row["content"],
                "emotion": row["emotion"],
                "timestamp": row["timestamp"]
            })
        return result

    def get_all_conversations(self) -> List[Dict]:
        """获取所有对话记录（用于显示）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role, content, emotion, timestamp FROM conversations ORDER BY timestamp ASC"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def save_user_info(self, key: str, value: str):
        """
        保存或更新用户信息

        Args:
            key: 信息键（如 'name', 'hobby'）
            value: 信息值
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO user_info (key, value, updated_at)
               VALUES (?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(key) DO UPDATE SET
               value = excluded.value,
               updated_at = CURRENT_TIMESTAMP""",
            (key, value)
        )
        conn.commit()

    def get_user_info(self, key: str = None) -> Dict:
        """
        获取用户信息

        Args:
            key: 指定键，为None时返回所有信息

        Returns:
            用户信息字典
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        if key:
            cursor.execute("SELECT key, value FROM user_info WHERE key = ?", (key,))
            row = cursor.fetchone()
            return {row["key"]: row["value"]} if row else {}
        else:
            cursor.execute("SELECT key, value FROM user_info")
            rows = cursor.fetchall()
            return {row["key"]: row["value"] for row in rows}

    def save_important_memory(self, category: str, content: str, source_conv_id: int = None):
        """
        保存重要记忆

        Args:
            category: 分类（如 '用户信息', '喜好', '重要事件'）
            content: 记忆内容
            source_conv_id: 来源对话ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO important_memories (category, content, source_conv_id) VALUES (?, ?, ?)",
            (category, content, source_conv_id)
        )
        conn.commit()

    def get_important_memories(self, category: str = None, limit: int = 10) -> List[Dict]:
        """
        获取重要记忆

        Args:
            category: 指定分类，为None时返回所有
            limit: 返回最大条数

        Returns:
            重要记忆列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        if category:
            cursor.execute(
                """SELECT category, content, created_at FROM important_memories
                   WHERE category = ? ORDER BY created_at DESC LIMIT ?""",
                (category, limit)
            )
        else:
            cursor.execute(
                """SELECT category, content, created_at FROM important_memories
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def build_memory_context(self) -> str:
        """
        构建记忆上下文字符串，用于插入到AI的system prompt中

        Returns:
            格式化的记忆上下文
        """
        context_parts = []

        # 获取用户基本信息
        user_info = self.get_user_info()
        if user_info:
            info_str = "、".join([f"{k}：{v}" for k, v in user_info.items()])
            context_parts.append(f"【用户基本信息】{info_str}")

        # 获取重要记忆
        memories = self.get_important_memories(limit=15)
        if memories:
            mem_lines = []
            for mem in memories:
                mem_lines.append(f"- [{mem['category']}] {mem['content']}")
            context_parts.append("【重要记忆】\n" + "\n".join(mem_lines))

        if context_parts:
            return "\n\n".join(context_parts)
        return ""

    def clean_old_memories(self, days: int = 30):
        """
        清理超过指定天数的旧记忆

        Args:
            days: 保留的天数
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "DELETE FROM conversations WHERE timestamp < ?",
            (cutoff_str,)
        )
        cursor.execute(
            "DELETE FROM important_memories WHERE created_at < ?",
            (cutoff_str,)
        )
        conn.commit()

    def clear_all_memories(self):
        """清空所有记忆"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM conversations")
        cursor.execute("DELETE FROM important_memories")
        cursor.execute("DELETE FROM user_info")
        conn.commit()

    def get_conversation_count(self) -> int:
        """获取对话总条数"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversations")
        return cursor.fetchone()[0]

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """析构时关闭连接"""
        self.close()
