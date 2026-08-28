#!/usr/bin/env python3
"""训练计划（单表版：计划与记录都在「训练记录」表，用「状态」列区分）。

状态：已完成=实际训练 / 待完成=自动生成的下次计划 / 已跳过=被新记录替代的旧计划。

用法:
  # 基于最近一次该部位实际训练生成下次计划（日期默认=档案中下一个训练日）
  python3 plan.py generate --theme 腿
  # 指定基准动作 / 日期
  python3 plan.py generate --theme 胸 \
      --exercises '[{"name":"卧推","sets":4,"reps":10,"weight":40}]' --date 2026-09-01
  # 查询（今天练什么：--date 今天 --status 待完成）
  python3 plan.py list [--date 2026-08-31] [--status 待完成] [--theme 腿]
  # 标记完成（录训练时已自动处理，一般不用手动调）
  python3 plan.py complete --theme 腿
"""
import argparse
import json

from fitlib import (TRAIN_COLS, append_rows, get_profile, load_config,
                    next_progression, next_training_date, out, read_sheet,
                    set_cells, today_str)

SHEET = "训练记录"


def _date_key(rec):
    return str(rec.get("日期") or "")


def _is_done(rec):
    return str(rec.get("状态") or "已完成").strip() == "已完成"


def last_theme_exercises(config, theme):
    """取该主题最近一次「已完成」训练的动作（每个动作名取最新一条）。"""
    _, records = read_sheet(config, SHEET, "H")
    if isinstance(records, dict):
        return records
    rows = [r for r in records
            if str(r.get("训练主题") or "").strip() == theme and _is_done(r)]
    if not rows:
        return []
    latest_date = max(_date_key(r) for r in rows)
    latest = [r for r in rows if _date_key(r) == latest_date]
    result, seen = [], set()
    for r in sorted(latest, key=lambda x: -x.get("_row", 0)):
        name = str(r.get("动作名称") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        result.append({"name": name, "sets": r.get("组数") or 3,
                       "reps": r.get("次数") or 10, "weight": r.get("重量kg") or 0})
    return result


def cmd_generate(config, args):
    theme = args.theme
    exercises = json.loads(args.exercises) if args.exercises else last_theme_exercises(config, theme)
    if isinstance(exercises, dict):
        out(exercises)
    if not exercises:
        out({"ok": False, "error": f"没有「{theme}」的已完成训练记录，无法生成计划；请先录入一次该部位训练"})

    profile = get_profile(config)
    if isinstance(profile, dict) and not profile.get("ok", True):
        out(profile)

    if args.date:
        plan_date, scheduled = args.date, True
    else:
        d, scheduled = next_training_date(profile or {})
        plan_date = d.strftime("%Y-%m-%d")

    _, all_rows = read_sheet(config, SHEET, "H")
    if isinstance(all_rows, dict):
        out(all_rows)
    dup = [p for p in all_rows
           if _date_key(p) == plan_date
           and str(p.get("训练主题") or "").strip() == theme
           and str(p.get("状态") or "").strip() == "待完成"]
    if dup and not args.force:
        out({"ok": False, "skipped": "duplicate",
             "error": f"{plan_date} 已有「{theme}」待完成计划，不重复生成；加 --force 可再生成",
             "existing_rows": [p.get("_row") for p in dup]})

    rows, progressed = [], []
    for ex in exercises:
        w, reps = next_progression(ex.get("weight", 0), ex.get("reps", 10))
        sets = int(float(ex.get("sets", 3)))
        rows.append([plan_date, theme, ex.get("name", ""), sets, reps, w,
                     f"基于{today_str()}训练自动进阶", "待完成"])
        progressed.append({"name": ex.get("name"), "sets": sets, "reps": reps,
                           "weight": w, "from": f"{ex.get('weight', 0)}kg×{ex.get('reps', 10)}"})
    r = append_rows(
        config, SHEET, TRAIN_COLS,
        {"日期": "datetime64[ns]", "组数": "float64", "次数": "float64", "重量kg": "float64"},
        {"日期": "yyyy-mm-dd"}, rows)
    if not r.get("ok"):
        out(r)
    out({"ok": True, "action": "generate", "theme": theme, "date": plan_date,
         "scheduled_by_profile": scheduled, "plan": progressed})


def cmd_list(config, args):
    _, rows = read_sheet(config, SHEET, "H")
    if isinstance(rows, dict):
        out(rows)
    result = rows
    if args.date:
        result = [p for p in result if _date_key(p) == args.date]
    if args.theme:
        result = [p for p in result if str(p.get("训练主题") or "").strip() == args.theme]
    if args.status:
        result = [p for p in result if str(p.get("状态") or "").strip() == args.status]
    for p in result:
        p.pop("_row", None)
    out({"ok": True, "count": len(result), "plans": result})


def cmd_complete(config, args):
    _, rows = read_sheet(config, SHEET, "H")
    if isinstance(rows, dict):
        out(rows)
    target_date = args.date or today_str()
    todo = [p for p in rows
            if _date_key(p) == target_date
            and str(p.get("训练主题") or "").strip() == args.theme
            and str(p.get("状态") or "").strip() == "待完成"]
    if not todo:
        out({"ok": False, "error": f"{target_date} 没有「{args.theme}」待完成计划"})
    for p in todo:
        r = set_cells(config, SHEET, f"H{p['_row']}", [["已完成"]])
        if not r.get("ok"):
            out(r)
    out({"ok": True, "action": "complete", "date": target_date,
         "theme": args.theme, "updated_rows": [p["_row"] for p in todo]})


def main():
    ap = argparse.ArgumentParser(description="训练计划生成/查询/完成（训练记录单表）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("generate")
    p_gen.add_argument("--theme", required=True)
    p_gen.add_argument("--exercises", help="基准动作 JSON；不给则取最近已完成训练")
    p_gen.add_argument("--date", help="计划日期 YYYY-MM-DD，默认档案下一训练日")
    p_gen.add_argument("--force", action="store_true")

    p_list = sub.add_parser("list")
    p_list.add_argument("--date")
    p_list.add_argument("--theme")
    p_list.add_argument("--status")

    p_done = sub.add_parser("complete")
    p_done.add_argument("--theme", required=True)
    p_done.add_argument("--date", help="默认今天")

    args = ap.parse_args()
    config = load_config()
    {"generate": cmd_generate, "list": cmd_list, "complete": cmd_complete}[args.cmd](config, args)


if __name__ == "__main__":
    main()
