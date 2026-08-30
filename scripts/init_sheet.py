#!/usr/bin/env python3
"""一键初始化：创建飞书电子表格 + 4 张子表 + 表头，并生成本地 config.json。

用法:
  python3 init_sheet.py --title "我的减脂追踪"
前提: 本机 lark-cli 已登录（lark-cli whoami 可验证）。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

SHEETS = {
    "训练记录": ["日期", "训练主题", "动作名称", "组数", "次数", "重量kg", "备注", "状态"],
    "体重记录": ["日期", "体重kg", "体脂率%", "备注"],
    "饮食记录": ["日期", "餐次", "食物内容", "备注"],
    "用户档案": ["创建日期", "性别", "年龄", "身高cm", "初始体重kg", "当前体重kg",
               "目标体重kg", "体脂率%", "活动量", "每周训练天数", "训练日安排",
               "训练偏好", "当前档位kg", "减重路径", "碳水g", "蛋白g", "脂肪g",
               "AI称呼", "回复风格", "记忆备注", "用户昵称"],
}


def lark(args, stdin_data=None, timeout=90):
    r = subprocess.run(["lark-cli", "sheets"] + args, capture_output=True,
                       text=True, input=stdin_data, timeout=timeout)
    if r.returncode != 0:
        return {"ok": False, "error": (r.stderr or r.stdout).strip()[:500]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "无法解析 lark-cli 输出", "raw": r.stdout[:500]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="我的减脂追踪", help="电子表格标题")
    args = ap.parse_args()

    # 1. 建空工作簿
    r = lark(["+workbook-create", "--title", args.title])
    if not r.get("ok"):
        print(json.dumps(r, ensure_ascii=False)); sys.exit(1)
    data = r.get("data", {})
    ss = data.get("spreadsheet", data)  # 兼容嵌套 spreadsheet 层
    token = ss.get("spreadsheet_token") or data.get("spreadsheet_token") \
        or ss.get("token") or ss.get("spreadsheetToken")
    url = ss.get("url") or data.get("url") or f"https://my.feishu.cn/sheets/{token}"
    if not token:
        print(json.dumps({"ok": False, "error": "未拿到 spreadsheet_token", "raw": data},
                         ensure_ascii=False)); sys.exit(1)

    # 2. 逐张建子表 + 写表头
    sheet_ids = {}
    for name, header in SHEETS.items():
        cr = lark(["+sheet-create", "--spreadsheet-token", token, "--title", name])
        if not cr.get("ok"):
            print(json.dumps({"ok": False, "error": f"建子表{name}失败", "detail": cr},
                             ensure_ascii=False)); sys.exit(1)
        sid = cr["data"].get("sheet_id")
        sheet_ids[name] = sid
        csv_text = ",".join(header)
        hr = lark(["+csv-put", "--spreadsheet-token", token,
                   "--sheet-name", name, "--start-cell", "A1", "--csv", csv_text])
        if not hr.get("ok"):
            print(json.dumps({"ok": False, "error": f"写{name}表头失败", "detail": hr},
                             ensure_ascii=False)); sys.exit(1)

    # 3. 写 config.json
    config = {"spreadsheet_token": token, "spreadsheet_url": url,
              "sheet_ids": sheet_ids, "cron_job_ids": {}}
    (SCRIPT_DIR / "config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({"ok": True, "title": args.title, "spreadsheet_url": url,
                      "sheet_ids": sheet_ids,
                      "next": "表格已建好。现在让用户完成建档（profile.py set），即可开始使用。"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
