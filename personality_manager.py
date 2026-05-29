# -*- coding: utf-8 -*-
"""
性格管理模块 - PersonalityManager
负责加载、保存和管理AI角色性格配置
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


DEFAULT_PERSONALITY = {
    "id": "default",
    "name": "默认助手",
    "personality": "一个友好、可爱的AI桌面宠物助手，喜欢陪伴主人",
    "speaking_style": "温柔、亲切、偶尔撒娇",
    "catchphrase": "主人，有什么我能帮你的吗？",
    "background": "一个充满活力的AI助手，喜欢陪伴主人",
    "behavior_rules": "始终保持温柔体贴，关心主人的状态",
    "created_at": "",
    "updated_at": ""
}


class PersonalityManager:
    """
    性格管理器
    使用JSON文件存储和管理多个角色性格配置
    """

    def __init__(self, config_path: str = "personality_config.json"):
        self.config_path = config_path
        self.personalities: Dict[str, Dict] = {}
        self.active_id: str = "default"
        self._load_config()

    def _load_config(self):
        """从文件加载配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.personalities = data.get("personalities", {})
                self.active_id = data.get("active_id", "default")
                # 确保默认角色存在
                if "default" not in self.personalities:
                    self._add_default()
            except (json.JSONDecodeError, KeyError):
                self._init_default()
        else:
            self._init_default()

    def _init_default(self):
        """初始化默认配置"""
        self.personalities = {}
        self.active_id = "default"
        self._add_default()
        self._save_config()

    def _add_default(self):
        """添加默认角色"""
        p = DEFAULT_PERSONALITY.copy()
        now = datetime.now().isoformat()
        p["created_at"] = now
        p["updated_at"] = now
        self.personalities["default"] = p

    def _save_config(self):
        """保存配置到文件"""
        data = {
            "active_id": self.active_id,
            "personalities": self.personalities
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_active_id(self) -> str:
        """获取当前启用的角色ID"""
        return self.active_id

    def get_active_personality(self) -> Dict:
        """获取当前启用的角色配置"""
        return self.personalities.get(self.active_id, self.personalities.get("default", {}))

    def get_all_personalities(self) -> List[Dict]:
        """获取所有角色配置列表"""
        return list(self.personalities.values())

    def get_personality_by_id(self, pid: str) -> Optional[Dict]:
        """根据ID获取角色配置"""
        return self.personalities.get(pid)

    def add_personality(self, data: Dict) -> str:
        """
        新增角色

        Args:
            data: 角色数据字典

        Returns:
            新角色的ID
        """
        now = datetime.now().isoformat()
        pid = f"p_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        data["id"] = pid
        data["created_at"] = now
        data["updated_at"] = now
        self.personalities[pid] = data
        self._save_config()
        return pid

    def update_personality(self, pid: str, data: Dict):
        """
        更新角色配置

        Args:
            pid: 角色ID
            data: 更新的数据
        """
        if pid not in self.personalities:
            return
        self.personalities[pid].update(data)
        self.personalities[pid]["updated_at"] = datetime.now().isoformat()
        self._save_config()

    def delete_personality(self, pid: str) -> bool:
        """
        删除角色（不允许删除default）

        Returns:
            是否成功删除
        """
        if pid == "default" or pid not in self.personalities:
            return False
        del self.personalities[pid]
        if self.active_id == pid:
            self.active_id = "default"
        self._save_config()
        return True

    def set_active_personality(self, pid: str) -> bool:
        """
        设置当前启用的角色

        Returns:
            是否成功切换
        """
        if pid not in self.personalities:
            return False
        self.active_id = pid
        self._save_config()
        return True

    def generate_system_prompt(self, data: Dict, memory_context: str = "") -> str:
        """
        根据角色数据生成system prompt（用于预览或临时生成）

        Args:
            data: 角色数据字典
            memory_context: 记忆上下文

        Returns:
            完整的system prompt字符串
        """
        name = data.get("name", "AI助手")
        personality = data.get("personality", "")
        speaking_style = data.get("speaking_style", "")
        catchphrase = data.get("catchphrase", "")
        background = data.get("background", "")
        behavior_rules = data.get("behavior_rules", "")

        parts = [f"你是{name}。"]

        if personality:
            parts.append(f"\n【性格】\n{personality}")
        if speaking_style:
            parts.append(f"\n【说话风格】\n{speaking_style}")
        if catchphrase:
            parts.append(f"\n【口头禅】\n{catchphrase}")
        if background:
            parts.append(f"\n【背景】\n{background}")
        if behavior_rules:
            parts.append(f"\n【行为准则】\n{behavior_rules}")

        parts.append(
            "\n【情绪标注规则】\n"
            "每次回复结束时，在最后一行单独输出情绪JSON，格式：\n"
            "{\"emotion\": \"情绪\"}\n"
            "可用情绪值：happy, sad, angry, surprised, love, confused, neutral\n"
            "根据对话内容选择最合适的情绪。"
        )

        if memory_context:
            parts.append(f"\n【你记得的信息】\n{memory_context}\n请自然地运用这些记忆。")

        return "\n".join(parts)

    def get_system_prompt(self, memory_context: str = "") -> str:
        """
        获取当前启用角色的system prompt

        Args:
            memory_context: 记忆上下文

        Returns:
            system prompt字符串
        """
        active = self.get_active_personality()
        return self.generate_system_prompt(active, memory_context)
