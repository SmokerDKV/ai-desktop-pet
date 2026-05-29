# 🐱 AI 桌面二次元老婆

一个基于 DeepSeek API 的智能桌面宠物程序，支持 AI 对话、情绪表情、眨眼动画、长期记忆和性格配置。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

## ✨ 特性

- 🤖 **智能对话**：基于 DeepSeek API 的自然语言交互
- 😊 **情绪表情**：根据对话内容自动切换 7 种表情
- 👁️ **眨眼动画**：自然的眨眼效果，让宠物更生动
- 🧠 **长期记忆**：自动记住用户信息和重要对话
- 🎭 **性格配置**：自定义角色名称、性格、说话风格
- 🖼️ **自定义形象**：支持上传自己喜欢的角色图片
- 📌 **桌面置顶**：始终显示在桌面最前方
- 💾 **数据持久化**：所有配置和记忆自动保存


## 🚀 快速开始

### 环境要求

- Windows 7/10/11
- Python 3.7 或更高版本
- DeepSeek API Key（[免费注册](https://platform.deepseek.com/)）

### 安装步骤

#### 方法一：使用启动脚本（推荐）

1. **克隆或下载项目**
   ```bash
   git clone https://github.com/你的用户名/ai-desktop-pet.git
   cd ai-desktop-pet
   ```

2. **双击运行 `启动.bat`**
   - 会自动安装依赖并启动程序

#### 方法二：手动安装

1. **克隆项目**
   ```bash
   git clone https://github.com/你的用户名/ai-desktop-pet.git
   cd ai-desktop-pet
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **创建配置文件**
   ```bash
   copy 配置文件\config.example.json 配置文件\config.json
   ```

4. **运行程序**
   ```bash
   python deskpet.py
   ```

### 初次配置

1. **设置 API Key**
   - 右键点击桌面宠物 → **设置 API Key**
   - 输入你的 DeepSeek API Key
   - 获取地址：https://platform.deepseek.com/

2. **上传表情图片**
   - 右键 → **上传表情图片**
   - 为 7 种情绪各上传一张图片：
     - 😊 开心 (happy)
     - 😢 伤心 (sad)
     - 😠 生气 (angry)
     - 😲 惊讶 (surprised)
     - 😍 喜爱 (love)
     - 🤔 疑惑 (confused)
     - 😐 平静 (neutral)

3. **上传眨眼图片（可选）**
   - 右键 → **上传眨眼图片**
   - 上传睁眼和闭眼两张图片
   - 启用后会有自然的眨眼动画

4. **开始聊天**
   - 左键单击桌面宠物即可打开聊天窗口

## 📖 使用指南

### 基本操作

| 操作 | 功能 |
|------|------|
| **左键单击** | 打开聊天窗口 |
| **左键拖拽** | 移动宠物位置 |
| **右键单击** | 打开功能菜单 |
| **Enter** | 发送消息 |
| **Shift+Enter** | 换行 |

### 功能菜单

右键点击桌面宠物可以访问以下功能：

- **设置 API Key**：配置 DeepSeek API 密钥
- **上传表情图片**：上传 7 种情绪的表情图片
- **上传眨眼图片**：上传睁眼/闭眼图片启用眨眼动画
- **性格设定**：自定义角色性格和说话风格
- **查看记忆**：管理 AI 的长期记忆
- **退出**：关闭程序

### 性格配置

通过 **右键 → 性格设定** 可以自定义角色：

1. **基本信息**
   - 角色名称
   - 性格描述
   - 说话风格
   - 口头禅

2. **高级功能**
   - 保存多个角色配置
   - 随时切换不同角色
   - 导入/导出配置文件
   - 实时测试对话效果

### 记忆系统

AI 会自动记住：
- 用户的姓名、喜好、习惯
- 重要的对话内容
- 历史聊天记录

记忆管理：
- 右键 → **查看记忆** 可以查看和管理所有记忆
- 自动清理 30 天前的旧记忆
- 支持手动清空所有记忆

## 📁 项目结构

```
ai-desktop-pet/
├── deskpet.py              # 主程序
├── memory_manager.py       # 记忆管理模块
├── personality_manager.py  # 性格管理模块
├── personality_setting.py  # 性格设定界面
├── requirements.txt        # Python 依赖
├── 启动.bat                # Windows 启动脚本
├── 初始化.bat              # 依赖安装脚本
├── 重置所有数据.bat        # 数据重置脚本
├── .gitignore              # Git 忽略文件
├── README.md               # 项目说明
├── 配置文件/
│   ├── config.example.json # 配置文件示例
│   ├── config.json         # 实际配置（不上传）
│   ├── logs/               # 日志目录
│   └── pet_images/         # 表情图片目录
└── 人物图片/               # 用户上传的图片目录
```

## ⚙️ 配置文件说明

### config.json

```json
{
  "api_key": "你的 DeepSeek API Key",
  "api_url": "https://api.deepseek.com/v1/chat/completions",
  "window_size": [200, 210],
  "window_pos": [100, 100],
  "auto_start": false,
  "theme": "light"
}
```

| 字段 | 说明 |
|------|------|
| `api_key` | DeepSeek API 密钥 |
| `api_url` | API 接口地址 |
| `window_size` | 窗口大小 [宽, 高] |
| `window_pos` | 窗口位置 [x, y] |
| `auto_start` | 是否开机自启动 |
| `theme` | 主题（light/dark） |

### personality_config.json

存储所有角色性格配置，通过界面管理，也可手动编辑。

### memory.db

SQLite 数据库，包含三张表：

| 表名 | 说明 |
|------|------|
| `conversations` | 所有对话记录 |
| `user_info` | 用户基本信息 |
| `important_memories` | AI 提取的重要记忆 |

## 🔧 高级功能

### 数据重置

如需完全重置所有数据：

1. 双击运行 `重置所有数据.bat`
2. 输入 `YES` 确认
3. 将清空：
   - API Key
   - 对话记忆
   - 性格配置
   - 所有图片
   - 缓存文件

### 自定义 API

支持使用其他兼容 OpenAI 格式的 API：

1. 修改 `配置文件/config.json` 中的 `api_url`
2. 设置对应的 `api_key`
3. 重启程序

### 图片要求

- **格式**：PNG、JPG、GIF
- **尺寸**：建议正方形（如 200x200）
- **背景**：透明背景效果更好
- **大小**：建议不超过 5MB

## ❓ 常见问题

<details>
<summary><b>Q: 桌宠不显示图片？</b></summary>

A: 检查 `配置文件/pet_images/` 或 `人物图片/` 目录下是否有对应的图片文件。确保图片格式正确（PNG/JPG/GIF）。
</details>

<details>
<summary><b>Q: API 调用失败？</b></summary>

A: 
1. 检查 API Key 是否正确
2. 确认网络能访问 api.deepseek.com
3. 查看 `配置文件/logs/` 下的日志文件
</details>

<details>
<summary><b>Q: 眨眼动画不工作？</b></summary>

A: 需要上传 `eye_open.png` 和 `eye_close.png` 两张图片才能启用眨眼功能。
</details>

<details>
<summary><b>Q: 如何完全重置记忆？</b></summary>

A: 
- 方法一：右键 → 查看记忆 → 清空所有记忆
- 方法二：直接删除 `memory.db` 文件
- 方法三：运行 `重置所有数据.bat`
</details>

<details>
<summary><b>Q: 程序启动后没有反应？</b></summary>

A: 
1. 检查是否已安装所有依赖：`pip install -r requirements.txt`
2. 查看控制台是否有错误信息
3. 检查 Python 版本是否 >= 3.7
</details>

<details>
<summary><b>Q: 可以使用其他 AI 模型吗？</b></summary>

A: 可以！只要 API 兼容 OpenAI 格式，修改 `config.json` 中的 `api_url` 和 `api_key` 即可。
</details>

## 🛠️ 开发

### 依赖项

```
tkinter          # GUI 界面
requests         # HTTP 请求
Pillow           # 图片处理
sqlite3          # 数据库（Python 内置）
```

### 运行测试

```bash
python deskpet.py
```

### 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v1.0.0 (2026-05-29)
- ✨ 初始版本发布
- 🤖 支持 DeepSeek API 对话
- 😊 7 种情绪表情系统
- 👁️ 眨眼动画
- 🧠 长期记忆功能
- 🎭 性格配置系统

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [DeepSeek](https://www.deepseek.com/) - 提供强大的 AI 能力
- [Tkinter](https://docs.python.org/3/library/tkinter.html) - Python GUI 框架
- [Pillow](https://python-pillow.org/) - Python 图像处理库

## 📧 联系方式

- 项目地址：https://github.com/你的用户名/ai-desktop-pet
- 问题反馈：https://github.com/你的用户名/ai-desktop-pet/issues

---

⭐ 如果这个项目对你有帮助，请给个 Star 支持一下！
