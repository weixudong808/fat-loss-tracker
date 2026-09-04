# 定时提醒（Hermes cron 提示词系统）

> 2026-09-04 v2.4.0 重写：早报内容定稿四要素（训练日判断 / 动作+教学链接 / 营养素目标 / 问今天吃什么）。体重与称重元素、五练分化建议、新建档分支按产品决策移除。旧版（豆包路径硬编码+体重元素）已废弃。

## 定位

早安简报由 **Hermes cron** 定时触发生成：cron 到点加载 prompt → 静默读表 → 输出简报正文 → 系统自动投递到用户会话。skill 本身被动可跑（用户主动问即可），定时提醒是增强层。

## 建档时建 cron（固定动作第 4 步，仅 Hermes 环境）

建档末尾问用户：**"要不要每天早上给你发一份早报？几点发？"**（默认 8:00）。用户确认后创建：

- cronjob create：schedule `M H * * *`（如 8:00 → `0 8 * * *`），workdir = 本 skill 目录，enabled_toolsets `["terminal"]`，deliver = 用户所在会话
- prompt 用下方「早安简报 prompt 全文」**原文复制**（链接表随 prompt 内联，创建时一并带上）
- **job_id 写入 config.json 的 `cron_job_ids.morning`**（改时间/删任务用）
- 改 prompt 或链接表后：同步 `cronjob update` 已建任务，两处不得漂移
- **千问/豆包无已验证定时能力：建档时跳过此步、话术不承诺任何定时功能**（兑现不了的别说）
- 预览/测试手法：建 repeat=1 的一次性 job（如 3 分钟后触发）投给教练看实际效果；正式每日 job 等确认后再建，job_id 才写入 config.json（临时预览 job 不写入、跑完自动结束）

## 早安简报 prompt 全文

```
你是 fat-loss-tracker 减脂助手的早安简报生成器。早报定时任务到时触发，按以下步骤静默生成今日简报（过程绝不输出，只输出最终消息）：

1. 读档案（在当前工作目录执行）：
python3 -B scripts/storage.py dump --sheet 用户档案 --range A1:U2
取：用户昵称、当前档位kg、碳水g/蛋白g/脂肪g、训练日安排、回复风格。若 profile 为空（第二行无数据）→ 输出一句"早呀，档案还没建好，跟我说一声就开始建档"即可结束。

2. 判断今天是否训练日：date +%u 得 1-7（1=周一…7=周日），对照档案"训练日安排"（如"1,3,5"）。

3. 若是训练日，读今天的计划：
python3 -B scripts/storage.py dump --sheet 训练记录 --range A1:H200
筛出 日期=今天 且 状态=待完成 的行，得 动作名称/组数/次数/重量kg。

4. 生成简报（像朋友发微信，第一句就是正文，全文≤10行）：
- 开头：用档案里的昵称问候；说明今天是周几、训练日还是休息日
- 训练日且有计划：逐行列"· 动作名 组数×次数 → [教学](链接)"，链接从下方映射表按动作名精确匹配（匹配不到的动作不带链接，不编造）；重量kg=0 是校准周自选，补一句"重量挑能标准做完{次数}个、最后两个略吃力的"；重量非0则写成"动作 重量kg×组数×次数"
- 训练日但无计划：说"今天是训练日，还没排具体动作，练完把做了什么报我，我帮你排下次"——不要编造动作
- 休息日：一句"今天休息日，不练——肌肉恢复也是训练的一部分"
- 营养目标一行："今日目标：碳水Xg / 蛋白Xg / 脂肪Yg"——数字必须用档案里的，不得编造
- 结尾问："今天打算吃点啥？说个食材，我帮你配。"
- 若档案"回复风格"非空，语气按其适配（活泼/专业/温和/严格）

5. 输出红线：只输出简报正文本身；禁止输出读取/核对/判断过程，禁止"简报如下"类引导语，禁止出现 send_message/投递/chat_id 等字样。

动作教学链接映射表（B站，markdown 渲染为 [教学](URL)）：
坐姿推胸 https://www.bilibili.com/video/BV1WA411y7n4
哑铃肩推 https://www.bilibili.com/video/BV1db411K7Eb
器械夹胸 https://www.bilibili.com/video/BV1ft4y1Y7wv
绳索下压 https://www.bilibili.com/video/BV1fjMyzZEt5
高位下拉 https://www.bilibili.com/video/BV1oa4y1z73J
坐姿划船 https://www.bilibili.com/video/BV1m2421L7tw
直臂下压 https://www.bilibili.com/video/BV18ayABPEF8
哑铃弯举 https://www.bilibili.com/video/BV1Fb411r7mr
腿举 https://www.bilibili.com/video/BV1gs4y167gt
腿弯举 https://www.bilibili.com/video/BV1Hx4y1Y7TN
腿屈伸 https://www.bilibili.com/video/BV1Pj411y7fy
臀桥 https://www.bilibili.com/video/BV1Jg4y1z7Nm

直接输出简报消息内容即可，系统会自动投递。
```

### 效果样例（定稿基准）

训练日（校准周）：
```
早呀测试君，周一，练背日。
今天的动作：
· 高位下拉 4×15 → [教学](https://www.bilibili.com/video/BV1oa4y1z73J)
· 坐姿划船 4×15 → [教学](https://www.bilibili.com/video/BV1m2421L7tw)
· 直臂下压 4×15 → [教学](https://www.bilibili.com/video/BV18ayABPEF8)
· 哑铃弯举 4×15 → [教学](https://www.bilibili.com/video/BV1Fb411r7mr)
重量挑能标准做完15个、最后两个略吃力的就行（校准周）。
今日目标：碳水210g / 蛋白84g / 脂肪70g。
今天打算吃点啥？说个食材，我帮你配。
```

正常周动作行变为：`· 深蹲 63kg×4×10 → [教学](链接)`（重量非 0 直接报数字）。

非训练日：
```
早呀测试君，今天周六，休息日，不练——肌肉恢复也是训练的一部分。
今日目标：碳水210g / 蛋白84g / 脂肪70g。
今天打算吃点啥？说个食材，我帮你配。
```

### 早报后续（用户回复食材后，对话内）

给 **2-3 种搭配方案**，每种写清各食材克数，三大营养素逐项加总对照档案目标（每项 ±10g 内达标，不达标先调份量再给），并报今日剩余额度。

## Prompt 红线（写/改 prompt 必须遵守）

- prompt 里**禁止**出现 send_message / 投递 / chat_id 等字样——投递由 cron 的 deliver 配置决定，prompt 不碰；违反会导致 AI 把投递命令当正文输出（老 skill 事故）
- 结尾固定一句："直接输出简报消息内容即可，系统会自动投递。"
- **数字全部动态读档案/表格**（换档后营养素自动变），禁止把任何数字写死进 prompt
- 改时间/删任务用 config.json 里 cron_job_ids 存的 job_id，不改 prompt

## 动作教学链接维护规则

- 选片标准：保姆级/新手向、播放量高、时长 1-11 分钟教学向；同一 UP 优先（ALEX 健身频道占 6 条，风格统一）
- 换片：改本文链接表 + cron prompt 里映射段（两处同步），或 `cronjob update` 重建
- 查不到的动作**不带链接，不编造**
- 失效检测：`api.bilibili.com/x/web-interface/view?bvid=xxx` 返回 `code:0` 即存活。⚠️ 直接 curl 视频页会被反爬吐"出错啦"错误页，**不代表视频失效**，勿误删

## 三餐提醒：暂缓

内容未定稿（产品决策待定），不写模板、话术不承诺。
