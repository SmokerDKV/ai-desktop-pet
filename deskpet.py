# -*- coding: utf-8 -*-
"""
桌面宠物主程序 - DeskPet
无边框置顶窗口，支持AI对话、表情切换、眨眼动画、记忆系统、性格配置
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import json
import os
import sys
import threading
import random
import re
import time
import requests
from PIL import Image, ImageTk

from memory_manager import MemoryManager
from personality_manager import PersonalityManager
from personality_setting import PersonalitySettingWindow

# ─────────────────────────────────────────────
# 路径工具
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "配置文件", "pet_images")
CONFIG_PATH = os.path.join(BASE_DIR, "配置文件", "config.json")
MEMORY_DB_PATH = os.path.join(BASE_DIR, "memory.db")
PERSONALITY_CONFIG_PATH = os.path.join(BASE_DIR, "personality_config.json")

# 情绪 → 图片文件名映射
EMOTION_MAP = {
    "happy":     "happy.png",
    "sad":       "sad.png",
    "angry":     "angry.png",
    "surprised": "surprised.png",
    "love":      "love.png",
    "confused":  "confused.png",
    "neutral":   "neutral.png",
}

# 眨眼图片文件名
BLINK_OPEN  = "eye_open.png"
BLINK_CLOSE = "eye_close.png"


# ─────────────────────────────────────────────
# 配置管理
# ─────────────────────────────────────────────
def load_config() -> dict:
    """加载配置文件"""
    default = {
        "api_key": "",
        "api_url": "https://api.deepseek.com/v1/chat/completions",
        "window_size": [200, 200],
        "window_pos": [100, 100],
        "auto_start": False,
        "theme": "light"
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            default.update(data)
        except Exception:
            pass
    return default


def save_config(cfg: dict):
    """保存配置文件"""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# 记忆查看窗口
# ─────────────────────────────────────────────
class MemoryViewWindow:
    """记忆查看与管理窗口"""

    def __init__(self, parent, memory_manager: MemoryManager):
        self.parent = parent
        self.mm = memory_manager

        self.window = tk.Toplevel(parent)
        self.window.title("记忆管理")
        self.window.geometry("620x480")
        self.window.resizable(True, True)
        self.window.grab_set()

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        nb = ttk.Notebook(self.window)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ── 对话历史 ──
        hist_frame = ttk.Frame(nb, padding=5)
        nb.add(hist_frame, text="💬 对话历史")

        self.hist_text = tk.Text(hist_frame, wrap=tk.WORD, font=("微软雅黑", 9),
                                 state=tk.DISABLED)
        sb1 = ttk.Scrollbar(hist_frame, command=self.hist_text.yview)
        self.hist_text.config(yscrollcommand=sb1.set)
        sb1.pack(side=tk.RIGHT, fill=tk.Y)
        self.hist_text.pack(fill=tk.BOTH, expand=True)

        self.hist_text.tag_config("user", foreground="#2563eb")
        self.hist_text.tag_config("assistant", foreground="#059669")
        self.hist_text.tag_config("time", foreground="#9ca3af", font=("微软雅黑", 8))

        # ── 重要记忆 ──
        mem_frame = ttk.Frame(nb, padding=5)
        nb.add(mem_frame, text="⭐ 重要记忆")

        self.mem_text = tk.Text(mem_frame, wrap=tk.WORD, font=("微软雅黑", 9),
                                state=tk.DISABLED)
        sb2 = ttk.Scrollbar(mem_frame, command=self.mem_text.yview)
        self.mem_text.config(yscrollcommand=sb2.set)
        sb2.pack(side=tk.RIGHT, fill=tk.Y)
        self.mem_text.pack(fill=tk.BOTH, expand=True)

        # ── 用户信息 ──
        info_frame = ttk.Frame(nb, padding=5)
        nb.add(info_frame, text="👤 用户信息")

        self.info_text = tk.Text(info_frame, wrap=tk.WORD, font=("微软雅黑", 9),
                                 state=tk.DISABLED)
        sb3 = ttk.Scrollbar(info_frame, command=self.info_text.yview)
        self.info_text.config(yscrollcommand=sb3.set)
        sb3.pack(side=tk.RIGHT, fill=tk.Y)
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # 底部按钮
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        ttk.Button(btn_frame, text="🔄 刷新", command=self._refresh).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="🧹 清理30天前记忆",
                   command=self._clean_old).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="🗑️ 清空所有记忆",
                   command=self._clear_all).pack(side=tk.LEFT, padx=3)

        self.status_label = ttk.Label(btn_frame, text="", foreground="gray")
        self.status_label.pack(side=tk.RIGHT)

    def _refresh(self):
        """刷新所有数据"""
        # 对话历史
        self.hist_text.config(state=tk.NORMAL)
        self.hist_text.delete("1.0", tk.END)
        convs = self.mm.get_all_conversations()
        for c in convs:
            self.hist_text.insert(tk.END, f"[{c['timestamp']}]\n", "time")
            tag = "user" if c["role"] == "user" else "assistant"
            prefix = "你：" if c["role"] == "user" else "AI："
            self.hist_text.insert(tk.END, f"{prefix}{c['content']}\n\n", tag)
        self.hist_text.config(state=tk.DISABLED)

        # 重要记忆
        self.mem_text.config(state=tk.NORMAL)
        self.mem_text.delete("1.0", tk.END)
        mems = self.mm.get_important_memories(limit=50)
        for m in mems:
            self.mem_text.insert(tk.END,
                f"[{m['category']}] {m['content']}\n  ({m['created_at']})\n\n")
        self.mem_text.config(state=tk.DISABLED)

        # 用户信息
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        info = self.mm.get_user_info()
        for k, v in info.items():
            self.info_text.insert(tk.END, f"{k}：{v}\n")
        self.info_text.config(state=tk.DISABLED)

        count = self.mm.get_conversation_count()
        self.status_label.config(text=f"共 {count} 条对话记录")

    def _clean_old(self):
        """清理30天前的记忆"""
        if messagebox.askyesno("确认", "清理30天前的对话记录和重要记忆？",
                               parent=self.window):
            self.mm.clean_old_memories(days=30)
            self._refresh()
            messagebox.showinfo("完成", "已清理旧记忆", parent=self.window)

    def _clear_all(self):
        """清空所有记忆"""
        if messagebox.askyesno("警告", "确定要清空所有记忆吗？此操作不可恢复！",
                               parent=self.window):
            self.mm.clear_all_memories()
            self._refresh()
            messagebox.showinfo("完成", "已清空所有记忆", parent=self.window)


# ─────────────────────────────────────────────
# 眨眼图片上传窗口
# ─────────────────────────────────────────────
class BlinkImageUploadWindow:
    """上传睁眼/闭眼图片的窗口"""

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("上传眨眼图片")
        self.window.geometry("400x260")
        self.window.resizable(False, False)
        self.window.grab_set()

        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        ttk.Label(self.window,
                  text="请上传睁眼和闭眼两张图片，用于实现眨眼动画效果",
                  wraplength=360, justify="center").pack(pady=12)

        # 睁眼
        open_frame = ttk.LabelFrame(self.window, text="睁眼图片", padding=8)
        open_frame.pack(fill=tk.X, padx=20, pady=5)

        self.open_status = ttk.Label(open_frame, text="未上传", foreground="gray")
        self.open_status.pack(side=tk.LEFT, expand=True)
        ttk.Button(open_frame, text="选择图片",
                   command=lambda: self._upload("open")).pack(side=tk.RIGHT)

        # 闭眼
        close_frame = ttk.LabelFrame(self.window, text="闭眼图片", padding=8)
        close_frame.pack(fill=tk.X, padx=20, pady=5)

        self.close_status = ttk.Label(close_frame, text="未上传", foreground="gray")
        self.close_status.pack(side=tk.LEFT, expand=True)
        ttk.Button(close_frame, text="选择图片",
                   command=lambda: self._upload("close")).pack(side=tk.RIGHT)

        ttk.Label(self.window,
                  text="图片将保存到 配置文件/pet_images/ 目录",
                  foreground="gray", font=("微软雅黑", 8)).pack(pady=8)

        ttk.Button(self.window, text="完成",
                   command=self.window.destroy).pack(pady=5)

    def _upload(self, eye_type: str):
        """上传图片"""
        path = filedialog.askopenfilename(
            parent=self.window,
            title=f"选择{'睁眼' if eye_type == 'open' else '闭眼'}图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if not path:
            return

        dest_name = BLINK_OPEN if eye_type == "open" else BLINK_CLOSE
        dest_path = os.path.join(IMG_DIR, dest_name)

        try:
            img = Image.open(path)
            img.save(dest_path, "PNG")
            self._refresh_status()
            messagebox.showinfo("成功", f"图片已保存", parent=self.window)
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}", parent=self.window)

    def _refresh_status(self):
        """刷新状态显示"""
        open_path = os.path.join(IMG_DIR, BLINK_OPEN)
        close_path = os.path.join(IMG_DIR, BLINK_CLOSE)

        if os.path.exists(open_path):
            self.open_status.config(text="✅ 已上传", foreground="green")
        else:
            self.open_status.config(text="❌ 未上传", foreground="red")

        if os.path.exists(close_path):
            self.close_status.config(text="✅ 已上传", foreground="green")
        else:
            self.close_status.config(text="❌ 未上传", foreground="red")


# ─────────────────────────────────────────────
# 聊天窗口
# ─────────────────────────────────────────────
class ChatWindow:
    """
    聊天对话窗口 - 无边框粉色风格，气泡式布局
    """

    # 颜色常量
    BG_COLOR       = "#3a3a3a"   # 窗口背景灰
    BUBBLE_BG      = "#2e2e2e"   # 气泡背景（略深）
    BUBBLE_FG      = "#ffb6c1"   # 气泡粉色文字
    BORDER_COLOR   = "#ffb6c1"   # 粉色边框
    INPUT_BORDER   = "#87ceeb"   # 天蓝色输入框边框
    INPUT_FG       = "#ffb6c1"   # 输入框文字色
    TITLE_FG       = "#ffb6c1"   # 标题文字
    SYSTEM_FG      = "#aaaaaa"   # 系统提示色
    SEND_BTN_BG    = "#ff9ab5"   # 发送按钮
    SEND_BTN_FG    = "#ffffff"

    def __init__(self, parent, config: dict, memory_manager: MemoryManager,
                 personality_manager: PersonalityManager,
                 on_emotion_change=None):
        self.parent = parent
        self.config = config
        self.mm = memory_manager
        self.pm = personality_manager
        self.on_emotion_change = on_emotion_change

        # 透明度
        self._alpha_val = 92

        # 拖拽
        self._drag_x = 0
        self._drag_y = 0

        self.window = tk.Toplevel(parent)
        self.window.title("和我聊天")
        self.window.geometry("420x560")
        self.window.resizable(True, True)
        self.window.overrideredirect(True)
        self.window.wm_attributes("-alpha", self._alpha_val / 100)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._load_history()

    def _build_ui(self):
        bg = self.BG_COLOR
        bb = self.BUBBLE_BG

        # 最外层粉色边框容器
        self.outer = tk.Frame(self.window, bg=self.BORDER_COLOR, bd=0)
        self.outer.pack(fill=tk.BOTH, expand=True)

        self.inner = tk.Frame(self.outer, bg=bg, bd=0)
        self.inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # ── 标题栏（可拖拽）──
        self.title_bar = tk.Frame(self.inner, bg=bg, height=32)
        self.title_bar.pack(fill=tk.X)
        self.title_bar.pack_propagate(False)

        active = self.pm.get_active_personality()
        self.char_label = tk.Label(
            self.title_bar,
            text=f"  ♡ 正在和 {active.get('name', 'AI')} 聊天",
            bg=bg, fg=self.TITLE_FG,
            font=("微软雅黑", 9, "bold"), anchor="w"
        )
        self.char_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 透明度滑块
        alpha_frame = tk.Frame(self.title_bar, bg=bg)
        alpha_frame.pack(side=tk.RIGHT, padx=4)
        tk.Label(alpha_frame, text="透明", bg=bg, fg=self.SYSTEM_FG,
                 font=("微软雅黑", 7)).pack(side=tk.LEFT)
        self.alpha_slider = tk.Scale(
            alpha_frame, from_=30, to=100, orient=tk.HORIZONTAL,
            length=60, showvalue=False, bg=bg, fg=self.BORDER_COLOR,
            troughcolor="#555555", highlightthickness=0, bd=0,
            command=self._on_alpha_change
        )
        self.alpha_slider.set(self._alpha_val)
        self.alpha_slider.pack(side=tk.LEFT)

        # 关闭按钮
        close_btn = tk.Label(
            self.title_bar, text="✕", bg=bg, fg=self.BORDER_COLOR,
            font=("微软雅黑", 10), cursor="hand2", padx=8
        )
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", lambda e: self._on_close())

        for w in (self.title_bar, self.char_label):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_move)

        tk.Frame(self.inner, bg=self.BORDER_COLOR, height=1).pack(fill=tk.X)

        # ── 消息显示区 ──
        self.msg_frame = tk.Frame(self.inner, bg=bg)
        self.msg_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_canvas = tk.Canvas(self.msg_frame, bg=bg, highlightthickness=0, bd=0)
        sb = tk.Scrollbar(self.msg_frame, orient=tk.VERTICAL,
                          command=self.chat_canvas.yview,
                          bg=bg, troughcolor=bg)
        self.chat_canvas.config(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.bubble_frame = tk.Frame(self.chat_canvas, bg=bg)
        self._canvas_window = self.chat_canvas.create_window(
            (0, 0), window=self.bubble_frame, anchor="nw"
        )
        self.bubble_frame.bind("<Configure>", self._on_bubble_frame_resize)
        self.chat_canvas.bind("<Configure>", self._on_canvas_resize)
        self.chat_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # ── 输入区：灰底 + 天蓝色边框 ──
        input_border = tk.Frame(self.inner, bg=self.INPUT_BORDER, bd=0)
        input_border.pack(fill=tk.X, padx=4, pady=(2, 4))

        self.input_area = tk.Frame(input_border, bg=bg, bd=0)
        self.input_area.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.input_box = tk.Text(
            self.input_area, height=3, font=("微软雅黑", 10),
            wrap=tk.WORD, bg=bg, fg=self.INPUT_FG,
            insertbackground=self.INPUT_FG, relief=tk.FLAT,
            bd=4, selectbackground="#5ba3c9"
        )
        self.input_box.pack(fill=tk.X, expand=True)
        self.input_box.bind("<Return>", self._on_enter)
        self.input_box.bind("<Shift-Return>", lambda e: None)

        btn_row = tk.Frame(self.input_area, bg=bg)
        btn_row.pack(fill=tk.X, padx=6, pady=(0, 4))

        self.status_label = tk.Label(
            btn_row, text="", bg=bg, fg=self.SYSTEM_FG,
            font=("微软雅黑", 8)
        )
        self.status_label.pack(side=tk.LEFT)

        clear_btn = tk.Button(
            btn_row, text="清空",
            bg="#666666", fg="#cccccc",
            font=("微软雅黑", 8), relief=tk.FLAT,
            activebackground="#888888", activeforeground="#ffffff",
            cursor="hand2", padx=6, pady=2,
            command=self._clear_bubbles
        )
        clear_btn.pack(side=tk.LEFT, padx=(6, 0))

        self.send_btn = tk.Button(
            btn_row, text="发送  ↵",
            bg=self.SEND_BTN_BG, fg=self.SEND_BTN_FG,
            font=("微软雅黑", 9, "bold"), relief=tk.FLAT,
            activebackground="#ff7fa0", activeforeground="#ffffff",
            cursor="hand2", padx=10, pady=2,
            command=self._send_message
        )
        self.send_btn.pack(side=tk.RIGHT)

    # ── 气泡渲染 ──────────────────────────────
    def _add_bubble(self, text: str, role: str):
        """向气泡区追加一条消息气泡"""
        is_user = (role == "user")
        side = tk.RIGHT if is_user else tk.LEFT
        anchor = "e" if is_user else "w"
        padx_args = (60, 8) if is_user else (8, 60)

        row = tk.Frame(self.bubble_frame, bg=self.BG_COLOR)
        row.pack(fill=tk.X, pady=3, padx=4)

        bubble = tk.Label(
            row, text=text,
            bg=self.BUBBLE_BG,
            fg=self.BUBBLE_FG,
            font=("微软雅黑", 10),
            wraplength=260, justify=tk.LEFT,
            relief=tk.FLAT, bd=0,
            padx=10, pady=6,
            anchor="w"
        )
        bubble.pack(side=side, anchor=anchor,
                    padx=padx_args, pady=0)

        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def _add_system_line(self, text: str):
        lbl = tk.Label(
            self.bubble_frame, text=text,
            bg=self.BG_COLOR, fg=self.SYSTEM_FG,
            font=("微软雅黑", 8)
        )
        lbl.pack(pady=2)

    def _on_bubble_frame_resize(self, event):
        self.chat_canvas.config(scrollregion=self.chat_canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.chat_canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.chat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── 透明度 ────────────────────────────────
    def _on_alpha_change(self, val):
        self._alpha_val = int(val)
        self.window.wm_attributes("-alpha", self._alpha_val / 100)

    # ── 拖拽 ──────────────────────────────────
    def _drag_start(self, event):
        self._drag_x = event.x_root - self.window.winfo_x()
        self._drag_y = event.y_root - self.window.winfo_y()

    def _drag_move(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.window.geometry(f"+{x}+{y}")

    def _load_history(self):
        recent = self.mm.get_recent_conversations(limit=30)
        if recent:
            self._add_system_line("── 历史记录 ──")
            for msg in recent:
                if msg["role"] == "user":
                    self._add_bubble(msg["content"], "user")
                else:
                    content = self._strip_emotion_json(msg["content"])
                    self._add_bubble(content, "assistant")
            self._add_system_line("── 新对话开始 ──")

    def _append_display(self, text: str, tag: str = ""):
        """兼容旧调用，映射到气泡"""
        if tag in ("system",):
            self._add_system_line(text.strip())
        elif tag in ("user_name", "user_msg"):
            # 用户消息在 _send_message 里整体调用 _add_bubble，这里忽略分段
            pass
        elif tag in ("ai_name", "ai_msg"):
            pass
        else:
            self._add_system_line(text.strip())

    def _strip_emotion_json(self, text: str) -> str:
        """从AI回复中去掉情绪JSON标注"""
        return re.sub(r'\{[\s]*"emotion"[\s]*:[\s]*"[^"]*"[\s]*\}', "", text).strip()

    def _extract_emotion(self, text: str) -> str:
        """从AI回复中提取情绪"""
        match = re.search(r'\{[\s]*"emotion"[\s]*:[\s]*"([^"]*)"[\s]*\}', text)
        if match:
            emotion = match.group(1).lower()
            if emotion in EMOTION_MAP:
                return emotion
        return "neutral"

    def _on_enter(self, event):
        """Enter键发送，Shift+Enter换行"""
        if not event.state & 0x1:  # 没按Shift
            self._send_message()
            return "break"

    def _send_message(self):
        """发送消息"""
        msg = self.input_box.get("1.0", tk.END).strip()
        if not msg:
            return

        if not self.config.get("api_key"):
            messagebox.showwarning("提示", "请先设置API Key（右键桌宠→设置API Key）",
                                   parent=self.window)
            return

        self.input_box.delete("1.0", tk.END)
        self.send_btn.config(state=tk.DISABLED)
        self.status_label.config(text="AI思考中...")

        # 显示用户气泡
        self._add_bubble(msg, "user")

        # 保存用户消息到数据库
        self.mm.save_message("user", msg)

        # 异步调用API
        threading.Thread(target=self._call_api, args=(msg,), daemon=True).start()

    def _call_api(self, user_msg: str):
        """在后台线程调用DeepSeek API"""
        try:
            # 构建记忆上下文
            memory_ctx = self.mm.build_memory_context()
            system_prompt = self.pm.get_system_prompt(memory_ctx)

            # 获取最近对话历史
            recent = self.mm.get_recent_conversations(limit=15)
            messages = [{"role": "system", "content": system_prompt}]
            for conv in recent[:-1]:  # 排除刚保存的用户消息（最后一条）
                messages.append({"role": conv["role"], "content": conv["content"]})
            messages.append({"role": "user", "content": user_msg})

            headers = {
                "Authorization": f"Bearer {self.config['api_key']}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": messages,
                "max_tokens": 800,
                "temperature": 0.85
            }

            resp = requests.post(
                self.config.get("api_url", "https://api.deepseek.com/v1/chat/completions"),
                headers=headers, json=payload, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()

            # 提取情绪
            emotion = self._extract_emotion(reply)
            clean_reply = self._strip_emotion_json(reply)

            # 保存AI回复
            self.mm.save_message("assistant", reply, emotion)

            # 异步提取重要信息
            threading.Thread(
                target=self._extract_important_info,
                args=(user_msg, clean_reply),
                daemon=True
            ).start()

            # 回到主线程更新UI
            self.window.after(0, lambda: self._on_api_success(clean_reply, emotion))

        except requests.exceptions.Timeout:
            self.window.after(0, lambda: self._on_api_error("请求超时，请检查网络"))
        except requests.exceptions.HTTPError as e:
            self.window.after(0, lambda: self._on_api_error(f"API错误：{e.response.status_code}"))
        except Exception as e:
            self.window.after(0, lambda: self._on_api_error(str(e)))

    def _on_api_success(self, reply: str, emotion: str):
        """API调用成功后更新UI"""
        # 显示AI气泡
        self._add_bubble(reply, "assistant")

        self.send_btn.config(state=tk.NORMAL)
        self.status_label.config(text="")

        # 触发情绪变化回调
        if self.on_emotion_change:
            self.on_emotion_change(emotion)

    def _on_api_error(self, error_msg: str):
        """API调用失败后更新UI"""
        self._add_system_line(f"[错误] {error_msg}")
        self.send_btn.config(state=tk.NORMAL)
        self.status_label.config(text="")

    def _extract_important_info(self, user_msg: str, ai_reply: str):
        """
        尝试从对话中提取重要信息并保存到记忆
        使用简单的关键词匹配，避免额外API调用
        """
        # 检测用户姓名
        name_patterns = [
            r"我叫([^\s，。！？,!?]{2,5})",
            r"我的名字是([^\s，。！？,!?]{2,5})",
            r"叫我([^\s，。！？,!?]{2,5})就好",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, user_msg)
            if match:
                name = match.group(1)
                self.mm.save_user_info("姓名", name)
                self.mm.save_important_memory("用户信息", f"用户姓名：{name}")
                break

        # 检测喜好
        like_patterns = [
            r"我(?:喜欢|爱|热爱)([^，。！？,!?\n]{2,15})",
            r"我(?:不喜欢|讨厌|不爱)([^，。！？,!?\n]{2,15})",
        ]
        for pattern in like_patterns:
            match = re.search(pattern, user_msg)
            if match:
                content = match.group(0)
                self.mm.save_important_memory("喜好", content)
                break

    def _clear_bubbles(self):
        """清空聊天界面气泡，不影响记忆数据库"""
        for widget in self.bubble_frame.winfo_children():
            widget.destroy()

    def _on_close(self):
        """关闭聊天窗口"""
        self.window.destroy()

    def update_char_label(self):
        """更新角色名称标签"""
        active = self.pm.get_active_personality()
        self.char_label.config(text=f"  ♡ 正在和 {active.get('name', 'AI')} 聊天")


# ─────────────────────────────────────────────
# 主桌宠窗口
# ─────────────────────────────────────────────
class DeskPet:
    """
    桌面宠物主窗口
    无边框、置顶、可拖拽，支持眨眼动画和情绪表情切换
    """

    def __init__(self):
        self.config = load_config()
        self.mm = MemoryManager(MEMORY_DB_PATH)
        self.pm = PersonalityManager(PERSONALITY_CONFIG_PATH)

        # 当前情绪
        self.current_emotion = "neutral"

        # 眨眼状态
        self.is_blinking = False
        self.blink_images_available = False

        # 子窗口引用
        self.chat_window: ChatWindow = None
        self.memory_window: MemoryViewWindow = None
        self.personality_window = None

        # 图片缓存
        self.emotion_images: dict = {}
        self.blink_open_img = None
        self.blink_close_img = None

        # 拖拽状态
        self._drag_x = 0
        self._drag_y = 0

        self._build_window()
        self._load_images()
        self._start_blink_loop()

        # 启动时清理旧记忆
        self.mm.clean_old_memories(days=30)

    def _build_window(self):
        """构建主窗口"""
        self.root = tk.Tk()
        self.root.title("桌面宠物")

        w, h = self.config.get("window_size", [200, 200])
        x, y = self.config.get("window_pos", [100, 100])

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.overrideredirect(True)   # 无边框
        self.root.wm_attributes("-topmost", True)  # 置顶
        self.root.wm_attributes("-transparentcolor", "#010101")  # 透明色
        self.root.config(bg="#010101")

        # 画布显示宠物图片
        self.canvas = tk.Canvas(
            self.root, width=w, height=h,
            bg="#010101", highlightthickness=0
        )
        self.canvas.pack()

        # 绑定事件
        self.canvas.bind("<Button-1>", self._on_left_click)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self.canvas.bind("<ButtonRelease-1>", self._drag_end)

        self.root.protocol("WM_DELETE_WINDOW", self._on_quit)

        # 图片显示项
        self.img_item = self.canvas.create_image(w // 2, h // 2, anchor=tk.CENTER)

    def _load_images(self):
        """加载所有情绪图片和眨眼图片"""
        w, h = self.config.get("window_size", [200, 200])

        for emotion, filename in EMOTION_MAP.items():
            path = os.path.join(IMG_DIR, filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path).resize((w, h), Image.LANCZOS)
                    self.emotion_images[emotion] = ImageTk.PhotoImage(img)
                except Exception:
                    pass

        # 眨眼图片
        open_path = os.path.join(IMG_DIR, BLINK_OPEN)
        close_path = os.path.join(IMG_DIR, BLINK_CLOSE)

        if os.path.exists(open_path) and os.path.exists(close_path):
            try:
                oi = Image.open(open_path).resize((w, h), Image.LANCZOS)
                ci = Image.open(close_path).resize((w, h), Image.LANCZOS)
                self.blink_open_img = ImageTk.PhotoImage(oi)
                self.blink_close_img = ImageTk.PhotoImage(ci)
                self.blink_images_available = True
            except Exception:
                pass

        self._show_emotion(self.current_emotion)

    def _show_emotion(self, emotion: str):
        """显示指定情绪的图片"""
        self.current_emotion = emotion
        img = self.emotion_images.get(emotion) or self.emotion_images.get("neutral")
        if img:
            self.canvas.itemconfig(self.img_item, image=img)

    def _start_blink_loop(self):
        """启动眨眼循环"""
        if self.blink_images_available:
            self._schedule_blink()

    def _schedule_blink(self):
        """随机2-3秒后触发一次眨眼"""
        delay = random.randint(2000, 3000)
        self.root.after(delay, self._do_blink)

    def _do_blink(self):
        """执行一次眨眼动作"""
        if not self.blink_images_available or self.is_blinking:
            self._schedule_blink()
            return

        self.is_blinking = True

        # 闭眼
        self.canvas.itemconfig(self.img_item, image=self.blink_close_img)
        # 150ms后睁眼
        self.root.after(150, self._end_blink)

    def _end_blink(self):
        """结束眨眼，恢复当前情绪图片"""
        self.is_blinking = False
        self._show_emotion(self.current_emotion)
        self._schedule_blink()

    # ── 拖拽 ──────────────────────────────────
    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
        self._dragging = False

    def _drag_move(self, event):
        self._dragging = True
        dx = event.x - self._drag_x
        dy = event.y - self._drag_y
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _drag_end(self, event):
        # 保存位置
        self.config["window_pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        save_config(self.config)

    # ── 点击事件 ──────────────────────────────
    def _on_left_click(self, event):
        """左键单击：打开/聚焦聊天窗口"""
        if getattr(self, "_dragging", False):
            self._dragging = False
            return
        self._open_chat()

    def _open_chat(self):
        """打开聊天窗口"""
        if self.chat_window and tk.Toplevel.winfo_exists(self.chat_window.window):
            self.chat_window.window.lift()
            self.chat_window.window.focus_force()
        else:
            self.chat_window = ChatWindow(
                self.root, self.config, self.mm, self.pm,
                on_emotion_change=self._on_emotion_change
            )

    def _on_emotion_change(self, emotion: str):
        """AI回复后切换表情，3秒后恢复平静"""
        self._show_emotion(emotion)
        if emotion != "neutral":
            self.root.after(3000, lambda: self._show_emotion("neutral"))

    # ── 右键菜单 ──────────────────────────────
    def _on_right_click(self, event):
        """右键菜单"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="💬 打开聊天", command=self._open_chat)
        menu.add_separator()
        menu.add_command(label="🎭 性格设定", command=self._open_personality)
        menu.add_command(label="🧠 查看记忆", command=self._open_memory)
        menu.add_separator()
        menu.add_command(label="😊 上传表情图片", command=self._open_emotion_upload)
        menu.add_command(label="👁️ 上传眨眼图片", command=self._open_blink_upload)
        menu.add_separator()
        menu.add_command(label="🔑 设置API Key", command=self._set_api_key)
        menu.add_command(label="📐 调整窗口大小", command=self._resize_window)
        menu.add_separator()
        menu.add_command(label="❌ 退出", command=self._on_quit)
        menu.tk_popup(event.x_root, event.y_root)

    def _open_personality(self):
        """打开性格设定窗口"""
        if self.personality_window and tk.Toplevel.winfo_exists(
                self.personality_window.window):
            self.personality_window.window.lift()
        else:
            self.personality_window = PersonalitySettingWindow(
                self.root, self.pm,
                api_key=self.config.get("api_key", ""),
                api_url=self.config.get("api_url", "")
            )
            # 关闭后更新聊天窗口角色名
            self.personality_window.window.bind(
                "<Destroy>", lambda e: self._on_personality_closed()
            )

    def _on_personality_closed(self):
        """性格窗口关闭后刷新聊天窗口"""
        if self.chat_window and tk.Toplevel.winfo_exists(self.chat_window.window):
            self.chat_window.update_char_label()

    def _open_memory(self):
        """打开记忆查看窗口"""
        if self.memory_window and tk.Toplevel.winfo_exists(self.memory_window.window):
            self.memory_window.window.lift()
        else:
            self.memory_window = MemoryViewWindow(self.root, self.mm)

    def _open_emotion_upload(self):
        """打开表情图片上传窗口"""
        EmotionUploadWindow(self.root, self)

    def _open_blink_upload(self):
        """打开眨眼图片上传窗口"""
        win = BlinkImageUploadWindow(self.root)
        self.root.wait_window(win.window)
        # 重新加载眨眼图片
        self._load_images()

    def _set_api_key(self):
        """设置API Key"""
        key = simpledialog.askstring(
            "设置API Key",
            "请输入DeepSeek API Key：",
            initialvalue=self.config.get("api_key", ""),
            parent=self.root,
            show="*"
        )
        if key is not None:
            self.config["api_key"] = key.strip()
            save_config(self.config)
            messagebox.showinfo("成功", "API Key已保存", parent=self.root)

    def _resize_window(self):
        """调整窗口大小"""
        size_str = simpledialog.askstring(
            "调整大小",
            "输入宽x高（如 200x200）：",
            initialvalue="x".join(map(str, self.config.get("window_size", [200, 200]))),
            parent=self.root
        )
        if not size_str:
            return
        try:
            w, h = map(int, size_str.lower().split("x"))
            w = max(80, min(w, 600))
            h = max(80, min(h, 600))
            self.config["window_size"] = [w, h]
            save_config(self.config)
            self.root.geometry(f"{w}x{h}")
            self.canvas.config(width=w, height=h)
            self.canvas.coords(self.img_item, w // 2, h // 2)
            self._load_images()
        except ValueError:
            messagebox.showerror("错误", "格式错误，请输入如 200x200", parent=self.root)

    def _on_quit(self):
        """退出程序"""
        self.config["window_pos"] = [self.root.winfo_x(), self.root.winfo_y()]
        save_config(self.config)
        self.mm.close()
        self.root.destroy()

    def run(self):
        """启动主循环"""
        self.root.mainloop()


# ─────────────────────────────────────────────
# 表情图片上传窗口
# ─────────────────────────────────────────────
class EmotionUploadWindow:
    """上传7种情绪表情图片的窗口"""

    EMOTION_LABELS = {
        "happy":     "😊 开心",
        "sad":       "😢 伤心",
        "angry":     "😠 生气",
        "surprised": "😲 惊讶",
        "love":      "😍 喜爱",
        "confused":  "😕 困惑",
        "neutral":   "😐 平静",
    }

    def __init__(self, parent, desk_pet: DeskPet):
        self.parent = parent
        self.desk_pet = desk_pet

        self.window = tk.Toplevel(parent)
        self.window.title("上传表情图片")
        self.window.geometry("420x380")
        self.window.resizable(False, False)
        self.window.grab_set()

        self._build_ui()
        self._refresh_status()

    def _build_ui(self):
        ttk.Label(self.window,
                  text="为每种情绪上传对应的图片（PNG/JPG，建议正方形）",
                  wraplength=380, justify="center").pack(pady=8)

        grid_frame = ttk.Frame(self.window, padding=8)
        grid_frame.pack(fill=tk.BOTH, expand=True)

        self.status_labels = {}

        for i, (emotion, label) in enumerate(self.EMOTION_LABELS.items()):
            row, col = divmod(i, 2)

            cell = ttk.Frame(grid_frame, padding=4)
            cell.grid(row=row, column=col, padx=5, pady=3, sticky="ew")

            ttk.Label(cell, text=label, width=10).pack(side=tk.LEFT)

            status = ttk.Label(cell, text="", width=8)
            status.pack(side=tk.LEFT)
            self.status_labels[emotion] = status

            ttk.Button(
                cell, text="上传",
                command=lambda e=emotion: self._upload(e)
            ).pack(side=tk.RIGHT)

        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=1)

        btn_frame = ttk.Frame(self.window, padding=8)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="完成并刷新",
                   command=self._done).pack(side=tk.RIGHT)

    def _upload(self, emotion: str):
        """上传指定情绪的图片"""
        path = filedialog.askopenfilename(
            parent=self.window,
            title=f"选择图片 - {self.EMOTION_LABELS[emotion]}",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if not path:
            return

        dest = os.path.join(IMG_DIR, EMOTION_MAP[emotion])
        try:
            img = Image.open(path)
            img.save(dest, "PNG")
            self._refresh_status()
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}", parent=self.window)

    def _refresh_status(self):
        """刷新各情绪图片状态"""
        for emotion, label in self.status_labels.items():
            path = os.path.join(IMG_DIR, EMOTION_MAP[emotion])
            if os.path.exists(path):
                label.config(text="✅", foreground="green")
            else:
                label.config(text="❌", foreground="red")

    def _done(self):
        """完成上传，刷新桌宠图片"""
        self.desk_pet._load_images()
        self.window.destroy()


# ─────────────────────────────────────────────
# 程序入口
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # 确保图片目录存在
    os.makedirs(IMG_DIR, exist_ok=True)

    pet = DeskPet()
    pet.run()
