# fat-loss-tracker · 个人减脂追踪私教 Skill

一行装好（在 workspace 目录执行；豆包的技能目录是 `.user_skills/`，换一下复制目标即可）：

```bash
curl -fsSL https://github.com/weixudong808/fat-loss-tracker/archive/refs/heads/main.tar.gz | tar xz && mkdir -p skills && rm -rf skills/fat-loss-tracker && cp -r fat-loss-tracker-main skills/fat-loss-tracker && python3 -B skills/fat-loss-tracker/scripts/profile.py get
```

自托管的个人减脂助手：自然语言记录训练/饮食/体重，训练计划按渐进超负荷自动滚动，体重达标自动换档重算营养素，支持早安简报和三餐定时提醒。数据默认存本地 xlsx（零安装零授权），飞书表格为可选后端（老用户自动沿用）。

## ⚡ 快速安装

### 方式一：把这段话直接发给 AI（最快，AI 零探索直接执行）

安装——把下面整段复制粘贴给千问/豆包：

```text
帮我安装 fat-loss-tracker 技能。在 workspace 目录按顺序执行：
1. curl -fsSL https://github.com/weixudong808/fat-loss-tracker/archive/refs/heads/main.tar.gz | tar xz（下载源码归档，解压出 fat-loss-tracker-main/，天然无 .git；失败就重试同一条命令，不要改用 git clone）
2. mkdir -p skills && rm -rf skills/fat-loss-tracker && cp -r fat-loss-tracker-main skills/fat-loss-tracker（豆包的目标目录是 .user_skills/）
3. python3 -B skills/fat-loss-tracker/scripts/profile.py get 做启动检查，输出 JSON 且 ok:true 即装好（首次运行自动建表，数据在工作区 减脂数据/，重装不丢）；若提示缺 openpyxl，先 pip install openpyxl 再重跑这一步
装好后回我一句装好了，之后我说「用 fat-loss-tracker 开始建档」时会激活它。
```

更新——发这段：

```text
帮我更新 fat-loss-tracker 技能：在 workspace 重新下载源码归档（curl -fsSL https://github.com/weixudong808/fat-loss-tracker/archive/refs/heads/main.tar.gz | tar xz，解压出 fat-loss-tracker-main/），删掉旧的 skills/fat-loss-tracker 后用 fat-loss-tracker-main 覆盖（技能目录外的 减脂数据/ 是我的数据，不要动），最后跑 python3 -B skills/fat-loss-tracker/scripts/profile.py get 确认档案还在。
```

### 方式二：手动命令行

用文首的一行命令。curl 不可用的环境才用 git 兜底（**必须 `--depth 1`**，完整 clone 在云电脑必中断 `cannot pread pack file`；复制后删 `.git`——千问把 .git 算进技能包，二进制 pack 会触发注册审核拒绝）：

```bash
git clone --depth 1 https://github.com/weixudong808/fat-loss-tracker.git && mkdir -p skills && rm -rf skills/fat-loss-tracker && cp -r fat-loss-tracker skills/ && rm -rf skills/fat-loss-tracker/.git && python3 -B skills/fat-loss-tracker/scripts/profile.py get
```

### 为什么 tarball 优先、git 兜底

- 两次真机会话 `git clone` 都先摔跤（完整 clone 必中断；AI 摔完才自己改道 tarball 成功）——把对的路写死在第一步，省掉摔跤和重试
- tarball 一次 HTTP 下载（实测 1.4 秒含解压），天然无 `.git`，连"删 .git"这步都省了
- `rm -rf skills/fat-loss-tracker` 让命令可重复执行（重装/更新安全）：技能目录外的 `减脂数据/` 不受影响，重装后老数据自动接上

### 要点

- 技能目录：千问 `workspace/skills/`，豆包 `workspace/.user_skills/`
- 启动检查返回 `profile: null` 即装好：首次运行自动在工作区 `减脂数据/` 建好电子表格（4 张子表），无需任何手动初始化
- 依赖：Python 3.9+、openpyxl（缺了就 `pip install openpyxl`）；飞书后端可选，需本机 lark-cli
- 装好后新开对话，明确说「**用 fat-loss-tracker 开始建档**」——本 skill 有触发白名单，必须显式点名才激活，只提"减肥/健身"不会触发
- 放进 skills/ 后所有对话已可用（自动发现）；要在千问 App「自定义技能」界面正式显示，按 SKILL.md §10 注册

## 能力

- **一句话记录**："深蹲60kg 4×12"录训练、"体重74.5"录体重、"午餐 鸡胸+米饭"录饮食
- **建档即送首周默认计划**：健身房 2/3 练自动排好整周训练表（首周为校准周），首次反馈后渐进超负荷自动接管
- **训练计划自动滚动**：次数 10→12→15，到15重量+5%回10，循环；按你的训练日自动排期
- **阶梯式减重**：每5kg一档，营养素（碳水/蛋白/脂肪克数）随档位自动重算
- **早安简报 + 三餐提醒**：定时任务，先查表再说话，记过的不催、缺的才提醒
- **随时问答**：今天练什么、还能吃多少碳水、这周进度，全部基于你自己的数据

## 目录结构

```
fat-loss-tracker/
├── SKILL.md              # AI 行为指令（核心）
├── README.md
├── references/
│   └── cron_prompts.md   # 定时任务 prompt 模板
└── scripts/
    ├── record.py         # 训练/体重/饮食录入（带自动联动）
    ├── profile.py        # 用户档案读写
    ├── plan.py           # 训练计划生成/查询/核销/首周默认计划
    ├── storage.py        # 统一查询入口（双后端输出一致）
    ├── bootstrap.py      # 环境探测/后端初始化（首次运行自动完成，无需手动跑）
    ├── fitlib.py         # 公共库（双后端存储IO/进阶/档位/营养素公式）
    └── config.json       # 空模板；运行后写入实际后端配置，勿公开分享
```

## 数据与隐私

- 默认本地后端：数据是工作区的 `减脂数据/减脂追踪数据.xlsx`，不经过任何第三方
- 飞书后端（可选）：数据全在你自己的飞书账号下，脚本仅通过本机 lark-cli 读写
- 分享本 skill 前：清空 `scripts/config.json` 里的个人配置（表格 URL、cron 任务 id 等），保持仓库里的空模板

## 自定义

- 进阶规则、营养素倍数、减重档位步长都在 `scripts/fitlib.py` 顶部常量，可自行调整
- 回复风格在档案「回复风格」字段，直接跟 AI 说"以后说话专业一点/活泼一点"即可
