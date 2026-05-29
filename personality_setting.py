# -*- coding: utf-8 -*-
"""
性格设定界面模块 - PersonalitySettingWindow
提供可视化的性格配置界面，支持角色创建、编辑、切换和测试
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import threading
import requests
from personality_manager import PersonalityManager


class PersonalitySettingWindow:
    """
    性格设定窗口
    包含3个标签页：性格编辑、角色库、实时测试
    """

    def __init__(self, parent, personality_manager: PersonalityManager,
                 api_key: str = "", api_url: str = ""):
        """
        初始化性格设定窗口

        Args:
            parent: 父窗口
            personality_manager: 性格管理器实例
            api_key: DeepSeek API密钥
            api_url: API地址
        """
        self.parent = parent
        self.pm = personality_manager
        self.api_key = api_key
        self.api_url = api_url

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("性格设定")
        self.window.geometry("700x550")
        self.window.resizable(True, True)
        self.window.grab_set()  # 模态窗口

        # 当前编辑的性格ID
        self.current_edit_id = None

        self._build_ui()
        self._refresh_character_list()

    def _build_ui(self):
        """构建界面"""
        # 主框架
        main_frame = ttk.Frame(self.window, padding=5)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标签页
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 三个标签页
        self._build_editor_tab()
        self._build_library_tab()
        self._build_test_tab()

    # =========================================================
    # 标签页1：性格编辑
    # =========================================================
    def _build_editor_tab(self):
        """构建性格编辑标签页"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="✏️ 性格编辑")

        # 滚动区域
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 表单字段
        fields = [
            ("角色名称 *", "name", False, 2),
            ("性格描述 *\n（详细描述角色性格特点）", "personality", True, 5),
            ("说话风格\n（如：温柔、活泼、傲娇等）", "speaking_style", True, 3),
            ("口头禅\n（角色常用的特色词语，每行一个）", "catchphrase", True, 3),
            ("背景故事\n（角色的背景设定）", "background", True, 4),
            ("行为准则\n（角色的特定行为规范）", "behavior_rules", True, 3),
        ]

        self.editor_vars = {}
        row = 0

        for label_text, field_name, multiline, height in fields:
            ttk.Label(scroll_frame, text=label_text, wraplength=150,
                      justify="right").grid(row=row, column=0, sticky="ne",
                                            padx=(0, 8), pady=5)

            if multiline:
                widget = tk.Text(scroll_frame, height=height, width=45,
                                 wrap=tk.WORD, font=("微软雅黑", 9))
                widget.grid(row=row, column=1, sticky="ew", pady=5)
            else:
                var = tk.StringVar()
                widget = ttk.Entry(scroll_frame, textvariable=var, width=47)
                widget.grid(row=row, column=1, sticky="ew", pady=5)
                self.editor_vars[field_name + "_var"] = var

            self.editor_vars[field_name] = widget
            row += 1

        scroll_frame.columnconfigure(1, weight=1)

        # 按钮区
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="💾 保存角色",
                   command=self._save_character).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="🔄 清空表单",
                   command=self._clear_editor).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="📋 生成预览",
                   command=self._preview_prompt).pack(side=tk.LEFT, padx=3)

        self.edit_status_label = ttk.Label(btn_frame, text="", foreground="gray")
        self.edit_status_label.pack(side=tk.RIGHT, padx=5)

    def _get_editor_value(self, field_name: str) -> str:
        """获取编辑器字段的值"""
        widget = self.editor_vars.get(field_name)
        if widget is None:
            return ""
        if isinstance(widget, tk.Text):
            return widget.get("1.0", tk.END).strip()
        else:
            var = self.editor_vars.get(field_name + "_var")
            return var.get().strip() if var else ""

    def _set_editor_value(self, field_name: str, value: str):
        """设置编辑器字段的值"""
        widget = self.editor_vars.get(field_name)
        if widget is None:
            return
        if isinstance(widget, tk.Text):
            widget.delete("1.0", tk.END)
            widget.insert("1.0", value)
        else:
            var = self.editor_vars.get(field_name + "_var")
            if var:
                var.set(value)

    def _save_character(self):
        """保存当前编辑的角色"""
        name = self._get_editor_value("name")
        personality = self._get_editor_value("personality")

        if not name:
            messagebox.showwarning("提示", "角色名称不能为空！", parent=self.window)
            return
        if not personality:
            messagebox.showwarning("提示", "性格描述不能为空！", parent=self.window)
            return

        data = {
            "name": name,
            "personality": personality,
            "speaking_style": self._get_editor_value("speaking_style"),
            "catchphrase": self._get_editor_value("catchphrase"),
            "background": self._get_editor_value("background"),
            "behavior_rules": self._get_editor_value("behavior_rules"),
        }

        if self.current_edit_id:
            self.pm.update_personality(self.current_edit_id, data)
            self.edit_status_label.config(text="✅ 已更新", foreground="green")
        else:
            new_id = self.pm.add_personality(data)
            self.current_edit_id = new_id
            self.edit_status_label.config(text="✅ 已保存", foreground="green")

        self._refresh_character_list()
        self.window.after(2000, lambda: self.edit_status_label.config(text=""))

    def _clear_editor(self):
        """清空编辑器"""
        self.current_edit_id = None
        for field in ["name", "personality", "speaking_style",
                      "catchphrase", "background", "behavior_rules"]:
            self._set_editor_value(field, "")
        self.edit_status_label.config(text="")

    def _preview_prompt(self):
        """预览生成的System Prompt"""
        name = self._get_editor_value("name")
        personality = self._get_editor_value("personality")
        if not name or not personality:
            messagebox.showinfo("提示", "请先填写角色名称和性格描述", parent=self.window)
            return

        data = {
            "name": name,
            "personality": personality,
            "speaking_style": self._get_editor_value("speaking_style"),
            "catchphrase": self._get_editor_value("catchphrase"),
            "background": self._get_editor_value("background"),
            "behavior_rules": self._get_editor_value("behavior_rules"),
        }
        prompt = self.pm.generate_system_prompt(data)

        # 显示预览窗口
        preview_win = tk.Toplevel(self.window)
        preview_win.title("System Prompt 预览")
        preview_win.geometry("500x400")

        text = tk.Text(preview_win, wrap=tk.WORD, font=("微软雅黑", 9), padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        text.insert("1.0", prompt)
        text.config(state=tk.DISABLED)

    # =========================================================
    # 标签页2：角色库
    # =========================================================
    def _build_library_tab(self):
        """构建角色库标签页"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="📚 角色库")

        # 左侧列表
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        ttk.Label(left_frame, text="角色列表", font=("微软雅黑", 10, "bold")).pack()

        self.char_listbox = tk.Listbox(left_frame, width=20, height=18,
                                       font=("微软雅黑", 9))
        self.char_listbox.pack(fill=tk.Y, expand=True)
        self.char_listbox.bind("<<ListboxSelect>>", self._on_char_select)

        # 右侧详情
        right_frame = ttk.Frame(frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        ttk.Label(right_frame, text="角色详情", font=("微软雅黑", 10, "bold")).pack()

        self.detail_text = tk.Text(right_frame, wrap=tk.WORD, font=("微软雅黑", 9),
                                   state=tk.DISABLED, height=15)
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # 按钮区
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(btn_frame, text="✅ 启用此角色",
                   command=self._activate_selected).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="✏️ 编辑",
                   command=self._edit_selected).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="🗑️ 删除",
                   command=self._delete_selected).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="📤 导出",
                   command=self._export_selected).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="📥 导入",
                   command=self._import_character).pack(side=tk.LEFT, padx=3)

        self.lib_status_label = ttk.Label(btn_frame, text="", foreground="gray")
        self.lib_status_label.pack(side=tk.RIGHT)

        # 存储列表中的ID映射
        self._char_ids = []

    def _refresh_character_list(self):
        """刷新角色列表"""
        self.char_listbox.delete(0, tk.END)
        self._char_ids = []

        personalities = self.pm.get_all_personalities()
        active_id = self.pm.get_active_id()

        for p in personalities:
            display = p["name"]
            if p["id"] == active_id:
                display = "★ " + display
            self.char_listbox.insert(tk.END, display)
            self._char_ids.append(p["id"])

    def _on_char_select(self, event):
        """选中角色时显示详情"""
        selection = self.char_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        if idx >= len(self._char_ids):
            return

        char_id = self._char_ids[idx]
        char = self.pm.get_personality_by_id(char_id)
        if not char:
            return

        # 显示详情
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)

        active_id = self.pm.get_active_id()
        status = "【当前启用】" if char_id == active_id else ""

        detail = f"角色名称：{char.get('name', '')} {status}\n\n"
        detail += f"性格描述：\n{char.get('personality', '')}\n\n"
        if char.get("speaking_style"):
            detail += f"说话风格：{char.get('speaking_style')}\n\n"
        if char.get("catchphrase"):
            detail += f"口头禅：\n{char.get('catchphrase')}\n\n"
        if char.get("background"):
            detail += f"背景故事：\n{char.get('background')}\n\n"
        if char.get("behavior_rules"):
            detail += f"行为准则：\n{char.get('behavior_rules')}\n"

        self.detail_text.insert("1.0", detail)
        self.detail_text.config(state=tk.DISABLED)

    def _get_selected_id(self) -> str:
        """获取当前选中的角色ID"""
        selection = self.char_listbox.curselection()
        if not selection:
            return None
        idx = selection[0]
        if idx >= len(self._char_ids):
            return None
        return self._char_ids[idx]

    def _activate_selected(self):
        """启用选中的角色"""
        char_id = self._get_selected_id()
        if not char_id:
            messagebox.showinfo("提示", "请先选择一个角色", parent=self.window)
            return
        self.pm.set_active_personality(char_id)
        self._refresh_character_list()
        char = self.pm.get_personality_by_id(char_id)
        name = char.get("name", "") if char else ""
        self.lib_status_label.config(text=f"✅ 已启用：{name}", foreground="green")
        self.window.after(2000, lambda: self.lib_status_label.config(text=""))

    def _edit_selected(self):
        """将选中的角色加载到编辑器"""
        char_id = self._get_selected_id()
        if not char_id:
            messagebox.showinfo("提示", "请先选择一个角色", parent=self.window)
            return

        char = self.pm.get_personality_by_id(char_id)
        if not char:
            return

        self.current_edit_id = char_id
        for field in ["name", "personality", "speaking_style",
                      "catchphrase", "background", "behavior_rules"]:
            self._set_editor_value(field, char.get(field, ""))

        # 切换到编辑标签页
        self.notebook.select(0)
        self.edit_status_label.config(text=f"编辑中：{char.get('name', '')}", foreground="blue")

    def _delete_selected(self):
        """删除选中的角色"""
        char_id = self._get_selected_id()
        if not char_id:
            messagebox.showinfo("提示", "请先选择一个角色", parent=self.window)
            return

        char = self.pm.get_personality_by_id(char_id)
        name = char.get("name", "") if char else ""

        if messagebox.askyesno("确认删除", f"确定要删除角色「{name}」吗？",
                               parent=self.window):
            self.pm.delete_personality(char_id)
            self._refresh_character_list()
            self.detail_text.config(state=tk.NORMAL)
            self.detail_text.delete("1.0", tk.END)
            self.detail_text.config(state=tk.DISABLED)

    def _export_selected(self):
        """导出选中的角色配置"""
        char_id = self._get_selected_id()
        if not char_id:
            messagebox.showinfo("提示", "请先选择一个角色", parent=self.window)
            return

        char = self.pm.get_personality_by_id(char_id)
        if not char:
            return

        file_path = filedialog.asksaveasfilename(
            parent=self.window,
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")],
            title="导出角色配置",
            initialfile=f"{char.get('name', 'character')}.json"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(char, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"已导出到：{file_path}", parent=self.window)

    def _import_character(self):
        """导入角色配置"""
        file_path = filedialog.askopenfilename(
            parent=self.window,
            filetypes=[("JSON文件", "*.json")],
            title="导入角色配置"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 验证必填字段
            if "name" not in data or "personality" not in data:
                messagebox.showerror("错误", "角色配置文件格式不正确", parent=self.window)
                return

            # 移除ID，作为新角色导入
            data.pop("id", None)
            self.pm.add_personality(data)
            self._refresh_character_list()
            messagebox.showinfo("成功", f"已导入角色：{data.get('name', '')}", parent=self.window)
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}", parent=self.window)

    # =========================================================
    # 标签页3：实时测试
    # =========================================================
    def _build_test_tab(self):
        """构建实时测试标签页"""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="🧪 实时测试")

        # 顶部提示
        ttk.Label(frame, text="使用当前启用的角色进行对话测试",
                  foreground="gray").pack(pady=(0, 5))

        # 对话显示区
        self.test_display = tk.Text(frame, wrap=tk.WORD, height=16,
                                    font=("微软雅黑", 9), state=tk.DISABLED,
                                    bg="#f9f9f9")
        self.test_display.pack(fill=tk.BOTH, expand=True)

        # 配置文字颜色
        self.test_display.tag_config("user", foreground="#2563eb")
        self.test_display.tag_config("ai", foreground="#059669")
        self.test_display.tag_config("system", foreground="#9ca3af", font=("微软雅黑", 8))

        # 输入区
        input_frame = ttk.Frame(frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))

        self.test_input = ttk.Entry(input_frame, font=("微软雅黑", 10))
        self.test_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.test_input.bind("<Return>", lambda e: self._send_test_message())

        self.test_send_btn = ttk.Button(input_frame, text="发送",
                                        command=self._send_test_message)
        self.test_send_btn.pack(side=tk.LEFT)

        ttk.Button(input_frame, text="清空",
                   command=self._clear_test).pack(side=tk.LEFT, padx=(5, 0))

        # 测试对话历史（不带记忆，纯测试）
        self._test_history = []

    def _append_test_display(self, text: str, tag: str = ""):
        """向测试对话框追加文字"""
        self.test_display.config(state=tk.NORMAL)
        self.test_display.insert(tk.END, text + "\n", tag)
        self.test_display.see(tk.END)
        self.test_display.config(state=tk.DISABLED)

    def _send_test_message(self):
        """发送测试消息"""
        msg = self.test_input.get().strip()
        if not msg:
            return

        if not self.api_key:
            messagebox.showwarning("提示", "请先在主程序中设置API Key", parent=self.window)
            return

        self.test_input.delete(0, tk.END)
        self.test_send_btn.config(state=tk.DISABLED)
        self._append_test_display(f"你：{msg}", "user")

        # 获取当前角色的system prompt
        active = self.pm.get_active_personality()
        system_prompt = self.pm.get_system_prompt()

        self._test_history.append({"role": "user", "content": msg})

        def _call_api():
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt}
                    ] + self._test_history[-10:],  # 最近10条
                    "max_tokens": 500,
                    "temperature": 0.9
                }
                resp = requests.post(self.api_url, headers=headers,
                                     json=payload, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                reply = data["choices"][0]["message"]["content"].strip()
                self._test_history.append({"role": "assistant", "content": reply})

                char_name = active.get("name", "AI") if active else "AI"
                self.window.after(0, lambda: self._append_test_display(
                    f"{char_name}：{reply}", "ai"))
            except Exception as e:
                self.window.after(0, lambda: self._append_test_display(
                    f"[错误] {str(e)}", "system"))
            finally:
                self.window.after(0, lambda: self.test_send_btn.config(state=tk.NORMAL))

        threading.Thread(target=_call_api, daemon=True).start()

    def _clear_test(self):
        """清空测试对话"""
        self._test_history = []
        self.test_display.config(state=tk.NORMAL)
        self.test_display.delete("1.0", tk.END)
        self.test_display.config(state=tk.DISABLED)
