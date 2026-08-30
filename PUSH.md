# 推送更新到 GitHub 指南

## 重要前提：每个 session 是独立的云电脑

豆包的每个对话（session）运行在独立的云电脑实例上，**文件系统不共享**。A 对话里创建的文件，B 对话里不存在。所以新 session 里没有 `dist/` 目录、没有本地 git 仓库，需要先从 GitHub clone。

---

## 场景 A：新 session 推送（最常用）

### 1. 从 GitHub clone 仓库

```bash
cd /home/user/.super_doubao/super-doubao-runtime/workspace
git clone https://github.com/weixudong808/fat-loss-tracker.git
cd fat-loss-tracker
```

### 2. 改代码

在 clone 出来的 `fat-loss-tracker/` 目录里直接改。
通常涉及：`SKILL.md`、`scripts/`、`references/`、`README.md`。

改完可以先本地测试（把改好的文件复制到 `.user_skills/fat-loss-tracker/` 覆盖，然后验证功能）。

### 3. 提交并推送

```bash
git add -A
git commit -m "简短描述改动，如：早报加昵称称呼"
git push https://x-access-token:<你的GitHub_TOKEN>@github.com/weixudong808/fat-loss-tracker.git main
```

推送成功后，访问 https://github.com/weixudong808/fat-loss-tracker 确认。

---

## 场景 B：原有开发 session（本地已有 dist/ 目录）

仅适用于最初创建仓库的那个 session，本地有两份代码：

| 版本 | 路径 | 用途 |
|---|---|---|
| 个人版（日常用） | `/home/user/.super_doubao/super-doubao-runtime/workspace/.user_skills/fat-loss-tracker/` | 实际加载运行的 skill |
| 公开版（git 仓库） | `/home/user/.super_doubao/super-doubao-runtime/workspace/dist/fat-loss-tracker/` | 推送到 GitHub 的版本 |

流程：改个人版 → 同步到公开版 → 提交推送（同场景 A 第 3 步）。

---

## GitHub Token 获取

推送需要一个有仓库写权限的 Fine-grained token：

1. 打开 https://github.com/settings/tokens?type=beta
2. Generate new token → 名字随便填（如 `push-skill`）
3. Repository access → Only select repositories → 选 `fat-loss-tracker`
4. Permissions → Repository permissions → **Contents** 设为 **Read and write**
5. 拉到底 Generate token，复制那串 `github_pat_...`

---

## 新 session 一句话触发话术

把下面这段话发给新 session 的 AI，它就能独立完成推送：

> 帮我把 fat-loss-tracker skill 的更新推到 GitHub。先 clone 仓库：`git clone https://github.com/weixudong808/fat-loss-tracker.git`，然后在 clone 的目录里改【这里填改了什么】。改完 git add/commit/push。GitHub token：【把 token 贴这】。仓库地址 https://github.com/weixudong808/fat-loss-tracker

---

## 注意事项

- **Token 不要写进代码、不要提交到仓库、不要发到公开场合**
- Token 有效期建议设 7-90 天，用完可在 token 列表里 Delete
- 推送命令里的 token 会出现在 shell 历史中，敏感环境下推送后可清理历史
- 仓库已重命名为 `fat-loss-tracker`，旧地址 `public-fat-loss-test` 会自动跳转
- 新 session 里 clone 的仓库是最新版，不用担心本地文件过期
- 如果 clone 时提示需要认证，说明仓库不是公开的；用 token  clone：`git clone https://x-access-token:<TOKEN>@github.com/weixudong808/fat-loss-tracker.git`
