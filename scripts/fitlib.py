#!/usr/bin/env python3
"""fat-loss-tracker 公共库：配置、飞书表格读写、档案、阶梯减重、渐进超负荷。

被 record.py / profile.py / plan.py 复用，不单独执行业务。
"""
import csv
import io
import json
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"

# ---------------------------------------------------------------- 常量

# 用户档案表列顺序（单行配置：第1行表头，第2行数据）
PROFILE_COLS = [
    "创建日期", "性别", "年龄", "身高cm",
    "初始体重kg", "当前体重kg", "目标体重kg", "体脂率%",
    "活动量", "每周训练天数", "训练日安排", "训练偏好",
    "当前档位kg", "减重路径",
    "碳水g", "蛋白g", "脂肪g",
    "AI称呼", "回复风格", "记忆备注",
]

# 训练记录单表承载实际记录与滚动计划：状态=已完成（实际）/待完成（自动生成的下次计划）/已跳过（被新记录替代）
TRAIN_COLS = ["日期", "训练主题", "动作名称", "组数", "次数", "重量kg", "备注", "状态"]
PLAN_COLS = TRAIN_COLS  # 兼容旧引用
PLAN_STATUSES = ["待完成", "已完成", "已跳过"]

REP_LADDER = [10, 12, 15]  # 渐进超负荷次数阶梯
WEIGHT_STEP_KG = 5         # 阶梯式减重：每 5kg 一档

# ---------------------------------------------------------------- 基础 IO

def load_config():
    if not CONFIG_PATH.exists():
        die(f"配置文件不存在: {CONFIG_PATH}")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def die(msg):
    print(json.dumps({"ok": False, "error": msg}, ensure_ascii=False))
    sys.exit(1)


def lark(args, stdin_data=None, timeout=60):
    """执行 lark-cli 并解析 JSON 返回。"""
    cmd = ["lark-cli", "sheets"] + args
    result = subprocess.run(cmd, capture_output=True, text=True,
                            input=stdin_data, timeout=timeout)
    if result.returncode != 0:
        return {"ok": False, "error": (result.stderr or result.stdout).strip()[:500]}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": "无法解析 lark-cli 输出", "raw": result.stdout[:500]}


def append_rows(config, sheet_name, columns, dtypes, formats, rows):
    payload = {"sheets": [{
        "name": sheet_name, "mode": "append", "header": False,
        "columns": columns, "dtypes": dtypes, "formats": formats, "data": rows,
    }]}
    return lark(["+table-put", "--url", config["spreadsheet_url"], "--sheets", "-"],
                stdin_data=json.dumps(payload, ensure_ascii=False))


def _auto_num(v):
    v = (v or "").strip()
    if v == "":
        return None
    try:
        f = float(v)
        return int(f) if f.is_integer() else f
    except ValueError:
        return v


def read_sheet(config, sheet_name, last_col, max_row=500):
    """读子表，返回 (表头list, 记录list[dict])。每条记录额外带 _row（表格行号，1-based）。"""
    rng = f"A1:{last_col}{max_row}"
    r = lark(["+csv-get", "--url", config["spreadsheet_url"],
              "--sheet-name", sheet_name, "--range", rng])
    if not r.get("ok"):
        return None, r
    annotated = r.get("data", {}).get("annotated_csv", "")
    header, records = [], []
    for line in annotated.split("\n"):
        m = re.match(r"\[row=(\d+)\]\s?(.*)$", line)
        if not m:
            continue
        row_idx = int(m.group(1))
        vals = next(csv.reader([m.group(2)]))
        if not any((v or "").strip() for v in vals):
            continue
        if row_idx == 1:
            header = [v.strip() for v in vals]
            continue
        rec = {h: _auto_num(v) for h, v in zip(header, vals)}
        rec["_row"] = row_idx
        records.append(rec)
    return header, records


def set_cells(config, sheet_name, a1_range, values_2d):
    """按区域写值（values_2d 为行×列，None/"" 写空串）。"""
    cells = [[{"value": "" if v is None else v} for v in row] for row in values_2d]
    return lark(["+cells-set", "--url", config["spreadsheet_url"],
                 "--sheet-name", sheet_name, "--range", a1_range,
                 "--cells", json.dumps(cells, ensure_ascii=False)])


def out(obj, code=None):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    sys.exit(code if code is not None else (0 if obj.get("ok", True) else 1))


# ---------------------------------------------------------------- 用户档案

def get_profile(config):
    """读取档案（第2行）。无档案返回 None。"""
    _, records = read_sheet(config, "用户档案", "T")
    if isinstance(records, dict):  # 出错
        return records
    if not records:
        return None
    rec = records[0]
    rec.pop("_row", None)
    return rec


def upsert_profile(config, fields):
    """合并写回档案单行（第2行）。fields 中 None 不覆盖已有值。返回合并后的完整档案。"""
    _, existing_rows = read_sheet(config, "用户档案", "T")
    if isinstance(existing_rows, dict) and not existing_rows.get("ok", True):
        return existing_rows
    current = {k: None for k in PROFILE_COLS}
    if existing_rows:
        for k in PROFILE_COLS:
            current[k] = existing_rows[0].get(k)
    for k, v in fields.items():
        if k not in PROFILE_COLS:
            return {"ok": False, "error": f"档案无此字段: {k}，合法字段：{PROFILE_COLS}"}
        current[k] = v  # 显式传入即写入（含 None/"" = 清空）；未传入的键保持原值
    values = [[current.get(k) for k in PROFILE_COLS]]
    r = set_cells(config, "用户档案", "A2:T2", values)
    if not r.get("ok"):
        return r
    return {"ok": True, "profile": current}


# ---------------------------------------------------------------- 阶梯减重 / 营养素

def build_tiers(start_weight, target_weight, step=WEIGHT_STEP_KG):
    """初始体重 → 目标体重，每 step kg 一档（含首尾）。"""
    if start_weight is None or target_weight is None or start_weight <= target_weight:
        return []
    tiers = []
    w = start_weight
    while w > target_weight:
        w -= step
        tiers.append(round(max(w, target_weight), 1))
    if not tiers or tiers[-1] != target_weight:
        tiers.append(round(target_weight, 1))
    return tiers


def protein_multiplier(days_per_week):
    """按每周训练天数定蛋白倍数：1-2练×1 / 3-4练×1.2 / 5-6练×1.5。"""
    try:
        d = int(days_per_week)
    except (TypeError, ValueError):
        return 1.2
    if d <= 2:
        return 1.0
    if d <= 4:
        return 1.2
    return 1.5


def calc_macros(tier_weight, days_per_week, carb_mult=2.0):
    """按当前档位体重算营养素（克）。碳水×2~3（新手3起步，适应后2）；蛋白按天数；脂肪×1。"""
    if tier_weight is None:
        return {"carb_g": None, "protein_g": None, "fat_g": None}
    return {
        "carb_g": round(tier_weight * carb_mult),
        "protein_g": round(tier_weight * protein_multiplier(days_per_week)),
        "fat_g": round(tier_weight * 1.0),
    }


def advance_tier(profile, today_weight):
    """阶段联动：体重达标则进下一档。返回 (新档案fields, 进阶信息dict 或 None)。"""
    cur_tier = profile.get("当前档位kg")
    path = (profile.get("减重路径") or "")
    tiers = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(path))]
    if cur_tier is None or today_weight is None:
        return {}, None
    try:
        cur_tier = float(cur_tier)
    except (TypeError, ValueError):
        return {}, None
    if today_weight > cur_tier:
        return {}, None
    # 达标：找下一档
    next_tier = None
    for t in tiers:
        if t < cur_tier - 1e-9:
            next_tier = t
            break
    if next_tier is None:
        # 已到最终档
        return {}, {"reached_final": True, "tier": cur_tier}
    macros = calc_macros(next_tier, profile.get("每周训练天数"))
    fields = {"当前档位kg": next_tier, "碳水g": macros["carb_g"],
              "蛋白g": macros["protein_g"], "脂肪g": macros["fat_g"]}
    return fields, {"advanced": True, "from_kg": cur_tier, "to_kg": next_tier, "macros": macros}


# ---------------------------------------------------------------- 渐进超负荷

def next_progression(weight, reps):
    """次数 10→12→15；到15后重量+5%、次数回10。返回 (新重量, 新次数)。"""
    try:
        w = float(weight or 0)
        r = int(float(reps))
    except (TypeError, ValueError):
        return weight, reps
    nxt = next((x for x in REP_LADDER if x > r), None)
    if nxt is not None:
        return _fmt_weight(w), nxt
    new_w = round(w * 1.05, 1)
    return _fmt_weight(new_w), 10


def _fmt_weight(w):
    if w is None:
        return 0
    if abs(w - round(w)) < 0.01:
        return int(round(w))
    return round(w, 1)


# ---------------------------------------------------------------- 训练日

def parse_training_days(text):
    """'1,3,5' / '一三五' / '周一周三' → [1,3,5]（1=周一…7=周日）。"""
    if text is None:
        return []
    s = str(text)
    cn = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7, "天": 7}
    days = set()
    for ch in s:
        if ch in cn:
            days.add(cn[ch])
    for n in re.findall(r"[1-7]", s):
        days.add(int(n))
    return sorted(days)


def next_training_date(profile, after=None):
    """档案训练日安排之后的第一个训练日；未配置则返回明天。"""
    after = after or date.today()
    days = parse_training_days(profile.get("训练日安排") if profile else None)
    d = after + timedelta(days=1)
    if not days:
        return d, False
    for _ in range(7):
        if d.isoweekday() in days:  # isoweekday: Mon=1
            return d, True
        d += timedelta(days=1)
    return after + timedelta(days=1), False


def today_str():
    return datetime.now().strftime("%Y-%m-%d")
