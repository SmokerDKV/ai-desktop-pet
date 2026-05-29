# GitHub 上传指南

本文档说明如何将项目上传到 GitHub。

## 准备工作

### 1. 安装 Git

如果还没有安装 Git，请访问 [git-scm.com](https://git-scm.com/) 下载安装。

### 2. 配置 Git

首次使用需要配置用户信息：

```bash
git config --global user.name "你的用户名"
git config --global user.email "你的邮箱"
```

### 3. 创建 GitHub 账号

访问 [github.com](https://github.com/) 注册账号（如果还没有）。

## 上传步骤

### 方法一：通过 GitHub 网页创建仓库

1. **登录 GitHub**，点击右上角 `+` → `New repository`

2. **填写仓库信息**：
   - Repository name: `ai-desktop-pet`（或其他名称）
   - Description: `一个基于 DeepSeek API 的智能桌面宠物程序`
   - Public/Private: 选择公开或私有
   - ❌ 不要勾选 "Initialize this repository with a README"（我们已经有了）

3. **在项目目录打开命令行**：
   ```bash
   cd "c:\Users\Administrator\Desktop\ai老婆"
   ```

4. **初始化 Git 仓库**：
   ```bash
   git init
   ```

5. **添加所有文件**：
   ```bash
   git add .
   ```

6. **提交到本地仓库**：
   ```bash
   git commit -m "Initial commit: AI Desktop Pet v1.0.0"
   ```

7. **关联远程仓库**（替换为你的仓库地址）：
   ```bash
   git remote add origin https://github.com/你的用户名/ai-desktop-pet.git
   ```

8. **推送到 GitHub**：
   ```bash
   git branch -M main
   git push -u origin main
   ```

### 方法二：使用 GitHub Desktop（图形界面）

1. **下载安装** [GitHub Desktop](https://desktop.github.com/)

2. **登录 GitHub 账号**

3. **添加本地仓库**：
   - File → Add Local Repository
   - 选择项目目录
   - 点击 "create a repository"

4. **发布到 GitHub**：
   - 点击 "Publish repository"
   - 填写仓库名称和描述
   - 选择公开或私有
   - 点击 "Publish Repository"

## 验证上传

访问 `https://github.com/你的用户名/ai-desktop-pet` 查看项目是否上传成功。

## 后续更新

当你修改代码后，使用以下命令更新到 GitHub：

```bash
git add .
git commit -m "描述你的更改"
git push
```

## 注意事项

### ✅ 已自动排除的敏感文件

`.gitignore` 已配置，以下文件不会上传：

- ❌ `memory.db` - 对话记忆数据库
- ❌ `personality_config.json` - 性格配置
- ❌ `配置文件/config.json` - 包含 API Key
- ❌ `人物图片/*.png` - 用户上传的图片
- ❌ `配置文件/pet_images/*.png` - 表情图片
- ❌ `__pycache__/` - Python 缓存

### ⚠️ 上传前检查

运行以下命令查看将要上传的文件：

```bash
git status
```

如果看到敏感文件（如包含 API Key 的 config.json），请确保它在 `.gitignore` 中。

### 🔒 如果不小心上传了敏感信息

1. **立即删除远程文件**：
   ```bash
   git rm --cached 配置文件/config.json
   git commit -m "Remove sensitive file"
   git push
   ```

2. **更换 API Key**（如果已泄露）

3. **清理历史记录**（可选，较复杂）：
   使用 `git filter-branch` 或 [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)

## 常见问题

**Q: 提示 "fatal: remote origin already exists"**

A: 删除现有远程仓库再添加：
```bash
git remote remove origin
git remote add origin https://github.com/你的用户名/ai-desktop-pet.git
```

**Q: 推送时要求输入用户名密码**

A: GitHub 已不支持密码认证，需要使用 Personal Access Token：
1. GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token，勾选 `repo` 权限
3. 使用 token 代替密码

**Q: 推送失败 "rejected"**

A: 远程仓库有本地没有的提交，先拉取：
```bash
git pull origin main --rebase
git push
```

## 项目地址示例

上传成功后，你的项目地址将是：

```
https://github.com/你的用户名/ai-desktop-pet
```

别人可以通过以下命令克隆你的项目：

```bash
git clone https://github.com/你的用户名/ai-desktop-pet.git
```

---

🎉 完成！现在你的项目已经在 GitHub 上了！
