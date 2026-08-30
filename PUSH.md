# 推送更新到 GitHub 指南

本仓库的开发环境在同一台云电脑上，分两份代码：

| 版本 | 路径 | 用途 |
|---|---|---|
| 个人版（日常用） | `/home/user/.super_doubao/super-doubao-runtime/workspace/.user_skills/fat-loss-tracker/` | 实际加载运行的 skill，定时任务读这份 |
| 公开版（git 仓库） | `/home/user/.super_doubao/super-doubao-runtime/workspace/dist/fat-loss-tracker/` | 推送到 GitHub 的版本，本文件所在目录 |

## 推送流程

### 1. 改代码
日常在**个人版**目录里改（`.user_skills/fat-loss-tracker/`），改完测试通过。

### 2. 同步到公开版
把改动的文件复制到公开版目录（`dist/fat-loss-tracker/`），保持两份一致。
通常涉及：`SKILL.md`、`scripts/`、`references/`、`README.md`。

### 3. 提交并推送
```bash
cd /home/user/.super_doubao/super-doubao-runtime/workspace/dist/fat-loss-tracker
git add -A
git commit -m "简短描述改动，如：早报加昵称称呼"
git push https://x-access-token:<你的GitHub_TOKEN>@github.com/weixudong808/fat-loss-tracker.git main
```

推送成功后，访问 https://github.com/weixudong808/fat-loss-tracker 确认。

## GitHub Token 获取

推送需要一个有仓库写权限的 Fine-grained token：

1. 打开 https://github.com/settings/tokens?type=beta
2. Generate new token → 名字随便填（如 `push-skill`）
3. Repository access → Only select repositories → 选 `fat-loss-tracker`
4. Permissions → Repository permissions → **Contents** 设为 **Read and write**
5. 拉到底 Generate token，复制那串 `github_pat_...`

## 注意事项

- **Token 不要写进代码、不要提交到仓库、不要发到公开场合**
- Token 有效期建议设 7-90 天，用完可在 token 列表里 Delete
- 推送命令里的 token 会出现在 shell 历史中，敏感环境下推送后可清理历史
- 仓库已重命名为 `fat-loss-tracker`，旧地址 `public-fat-loss-test` 会自动跳转
- 个人版和公开版要保持同步，只改一份会导致两边不一致
