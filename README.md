# fat-loss-tracker · 个人减脂追踪私教 Skill

自托管的个人减脂助手：自然语言记录训练/饮食/体重，训练计划按渐进超负荷自动滚动，体重达标自动换档重算营养素，支持早安简报和三餐定时提醒。数据默认存本地 xlsx（零安装零授权），飞书表格为可选后端（老用户自动沿用）。

## ⚡ 快速安装（先看这里，按顺序执行）

在 workspace 目录下执行。**⚠️ 必须 `--depth 1` 浅克隆**：云电脑环境完整 clone 极易传输中断（`cannot pread pack file`），失败重试纯浪费时间：

```bash
git clone --depth 1 https://github.com/weixudong808/fat-loss-tracker.git
mkdir -p skills && cp -r fat-loss-tracker skills/ && rm -rf skills/fat-loss-tracker/.git
python3 -B skills/fat-loss-tracker/scripts/profile.py get
```

要点：

- **复制进 skills/ 后立刻删 `.git`**：千问把 .git 算进技能包，其中的二进制 pack 文件会触发注册审核拒绝
- 技能目录：千问 `workspace/skills/`，豆包 `workspace/.user_skills/`（上面第 2 条的复制目标换一下即可）
- 启动检查返回 `profile: null` 即装好：首次运行自动在工作区 `减脂数据/` 建好电子表格（4 张子表），无需任何手动初始化
- 依赖：Python 3.9+、openpyxl（缺了就 `pip install openpyxl`，本地 xlsx 后端需要它）；飞书后端可选，需本机 lark-cli
- 装好后新开对话，明确说「**用 fat-loss-tracker 开始建档**」——本 skill 有触发白名单，必须显式点名才激活，只提"减肥/健身"不会触发
- 放进 skills/ 后所有对话已可用（自动发现）；要在千问 App「自定义技能」界面正式显示，按 SKILL.md §10 注册（包内禁二进制、验证脚本一律加 `-B`）

## 能力

- **一句话记录**："深蹲60kg 4×12"录训练、"体重74.5"录体重、"午餐 鸡胸+米饭"录饮食
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
    ├── plan.py           # 训练计划生成/查询/核销
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
