# fat-loss-tracker · 个人减脂追踪私教 Skill

一个自托管的个人减脂助手：自然语言记录训练/饮食/体重到你自己的飞书电子表格，自动按渐进超负荷滚动生成下次训练计划，体重达标自动换档重算营养素，支持早安简报和三餐定时提醒。

## 能力

- **一句话记录**："深蹲60kg 4×12"录训练、"体重74.5"录体重、"午餐 鸡胸+米饭"录饮食
- **训练计划自动滚动**：次数 10→12→15，到15重量+5%回10，循环；按你的训练日自动排期
- **阶梯式减重**：每5kg一档，营养素（碳水/蛋白/脂肪克数）随档位自动重算
- **早安简报 + 三餐提醒**：定时任务，先查表再说话，记过的不催、缺的才提醒
- **随时问答**：今天练什么、还能吃多少碳水、这周进度，全部基于你自己的数据

## 环境要求

- 支持 Skills 的 AI 助手（豆包 / Claude 类 agent），能执行本地脚本
- 本机已安装并登录 [`lark-cli`](https://open.feishu.cn/)（飞书命令行，数据写进你自己的飞书表格）
- Python 3.9+

## 安装

1. 把整个 `fat-loss-tracker/` 文件夹放进 AI 的 skills 目录（豆包：`~/.super_doubao/super-doubao-runtime/workspace/.user_skills/`）
2. 重启/新开会话，直接说："用 fat-loss-tracker 开始建档"
3. AI 会自动执行：
   - `python3 scripts/init_sheet.py --title "我的减脂追踪"`（建你专属的飞书表格）
   - 一题一轮问你：性别/年龄/身高/体重/目标/训练日/训练环境/风格
4. 建档完成即可用。想定时提醒再说"开早报和三餐提醒"，AI 按 `references/cron_prompts.md` 创建

## 目录结构

```
fat-loss-tracker/
├── SKILL.md              # AI 行为指令（核心）
├── README.md
├── references/
│   └── cron_prompts.md   # 定时任务 prompt 模板
└── scripts/
    ├── init_sheet.py     # 首次一键建表
    ├── record.py         # 训练/体重/饮食录入（带自动联动）
    ├── profile.py        # 用户档案读写
    ├── plan.py           # 训练计划生成/查询/核销
    ├── fitlib.py         # 公共库（进阶/档位/营养素公式）
    └── config.example.json
```

首次运行 `init_sheet.py` 后会自动生成 `scripts/config.json`（你的表格地址，勿公开分享）。

## 数据与隐私

- 所有数据在**你自己的飞书账号**下，脚本只通过本机 lark-cli 读写，不经过任何第三方
- 分享本 skill 前确认：删掉 `scripts/config.json`（含你的表格 token），版本里只保留 `config.example.json`

## 自定义

- 进阶规则、营养素倍数、减重档位步长都在 `scripts/fitlib.py` 顶部常量，可自行调整
- 回复风格在档案"回复风格"字段，直接跟 AI 说"以后说话专业一点/活泼一点"即可
