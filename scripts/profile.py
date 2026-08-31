#!/usr/bin/env python3
"""用户档案读写（电子表格「用户档案」子表，单行配置）。

用法:
  # 读取档案
  python3 profile.py get [--field 当前档位kg]
  # 首次建档（row2 已有数据时拒绝，--force 覆盖）
  python3 profile.py init '{"性别":"女","年龄":30,...}'
  # 局部更新（任意列名，自动 merge）
  python3 profile.py set --当前体重kg 70.5 --体脂率 24
  python3 profile.py set --json '{"训练日安排":"1,3,5"}'
  # 按当前档位+每周训练天数重算营养素并写回
  python3 profile.py macros [--carb-mult 2]
"""
import argparse
import json
import sys

from fitlib import (PROFILE_COLS, calc_macros, get_profile, load_config, out,
                    today_str, upsert_profile)


def cmd_get(config, args):
    p = get_profile(config)
    if isinstance(p, dict) and not p.get("ok", True):
        out(p)
    if not p:
        out({"ok": True, "profile": None, "message": "尚未建档"})
    if args.field:
        out({"ok": True, "field": args.field, "value": p.get(args.field)})
    out({"ok": True, "profile": p})


def cmd_init(config, args):
    existing = get_profile(config)
    if isinstance(existing, dict) and not existing.get("ok", True):
        out(existing)
    if existing and any(v not in (None, "") for v in existing.values()) and not args.force:
        out({"ok": False, "error": "档案已存在，如需覆盖请加 --force，或用 set 局部更新",
             "existing": existing})
    fields = json.loads(args.data)
    fields.setdefault("创建日期", today_str())
    # 用户没自备营养素时，建档即按档位自动算好，省去二次跑 macros
    if all(fields.get(k) in (None, "") for k in ("碳水g", "蛋白g", "脂肪g")):
        tier = fields.get("当前档位kg")
        days = fields.get("每周训练天数")
        if tier and days:
            m = calc_macros(float(tier), int(days))
            fields.update({"碳水g": m["carb_g"], "蛋白g": m["protein_g"], "脂肪g": m["fat_g"]})
    r = upsert_profile(config, fields)
    if r.get("ok"):
        r["action"] = "init"
    out(r)


def cmd_set(config, args):
    fields = {}
    if args.json:
        fields.update(json.loads(args.json))
    for kv in args.fields or []:
        if "=" not in kv:
            out({"ok": False, "error": f"字段格式应为 列名=值，收到: {kv}"})
        k, v = kv.split("=", 1)
        fields[k.strip()] = _convert(k.strip(), v)
    if not fields:
        out({"ok": False, "error": "未提供要更新的字段"})
    r = upsert_profile(config, fields)
    if r.get("ok"):
        r["action"] = "set"
    out(r)


def cmd_macros(config, args):
    p = get_profile(config)
    if not p:
        out({"ok": False, "error": "尚未建档"})
    tier = p.get("当前档位kg")
    if tier is None:
        out({"ok": False, "error": "档案缺少「当前档位kg」，无法计算营养素"})
    macros = calc_macros(float(tier), p.get("每周训练天数"),
                         carb_mult=args.carb_mult)
    r = upsert_profile(config, {"碳水g": macros["carb_g"],
                                "蛋白g": macros["protein_g"],
                                "脂肪g": macros["fat_g"]})
    if r.get("ok"):
        r["macros"] = macros
    out(r)


_NUM_FIELDS = {"年龄", "身高cm", "初始体重kg", "当前体重kg", "目标体重kg", "体脂率%",
               "每周训练天数", "当前档位kg", "碳水g", "蛋白g", "脂肪g"}


def _convert(key, val):
    if val == "":
        return None
    if key in _NUM_FIELDS:
        try:
            f = float(val)
            return int(f) if f.is_integer() else f
        except ValueError:
            return val
    return val


def main():
    ap = argparse.ArgumentParser(description="用户档案读写")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_get = sub.add_parser("get")
    p_get.add_argument("--field")

    p_init = sub.add_parser("init")
    p_init.add_argument("data", help="档案 JSON")
    p_init.add_argument("--force", action="store_true")

    p_set = sub.add_parser("set")
    p_set.add_argument("--json", help="字段 JSON")
    p_set.add_argument("fields", nargs="*", help="列名=值（可多个）")

    p_macros = sub.add_parser("macros")
    p_macros.add_argument("--carb-mult", type=float, default=3.0,
                          help="碳水倍数，新手3 / 适应后2，默认3")

    args = ap.parse_args()
    config = load_config()
    {"get": cmd_get, "init": cmd_init, "set": cmd_set, "macros": cmd_macros}[args.cmd](config, args)


if __name__ == "__main__":
    main()
