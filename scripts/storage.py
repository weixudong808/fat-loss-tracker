#!/usr/bin/env python3
"""统一存储查询入口（后端无关：local xlsx / feishu 表格输出一致）。
用法:
  # 导出整张子表（默认 csv，第一行表头，其后每行数据）
  python3 storage.py dump --sheet 训练记录
  # 指定范围与格式
  python3 storage.py dump --sheet 体重记录 --range A1:D200 --format csv
  python3 storage.py dump --sheet 用户档案 --range A1:T2 --format json
  # 查看当前后端与数据位置
  python3 storage.py info
"""
import argparse
import csv
import io
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import fitlib as fl  # noqa: E402

# 各子表默认读取范围（最后一列 + 最大行）
DEFAULT_RANGE = {
    "训练记录": ("H", 500),
    "体重记录": ("D", 500),
    "饮食记录": ("D", 500),
    "用户档案": ("U", 50),
}


def parse_range(rng):
    """A1:H200 → (last_col='H', max_row=200)；缺省部分回退默认。"""
    if not rng:
        return None, None
    m = re.match(r"^A\d*:([A-Z]+)(\d*)$", rng.strip().upper())
    if not m:
        fl.out({"ok": False, "error": f"范围格式应为 A1:H200，收到: {rng}"})
    return m.group(1), int(m.group(2)) if m.group(2) else 500


def cmd_dump(config, args):
    last_col, max_row = parse_range(args.range)
    if last_col is None:
        last_col, max_row = DEFAULT_RANGE.get(args.sheet, ("Z", 500))
    header, records = fl.read_sheet(config, args.sheet, last_col, max_row)
    if isinstance(records, dict):  # 出错
        fl.out(records)
    # 以表头为列顺序
    cols = header or []
    if args.format == "json":
        out_records = [{c: rec.get(c) for c in cols} for rec in records]
        fl.out({"ok": True, "backend": config.get("backend"),
                "sheet": args.sheet, "header": cols, "records": out_records})
    # csv 输出（纯表格，第一行表头，供 Agent/人直接读）
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(cols)
    for rec in records:
        writer.writerow(["" if rec.get(c) is None else rec.get(c) for c in cols])
    out_text = buf.getvalue()
    sys.stdout.write(out_text)
    if not out_text.endswith("\n"):
        sys.stdout.write("\n")
    sys.exit(0)


def cmd_info(config, args):
    info = fl.storage_info(config)
    info["ok"] = True
    fl.out(info)


def main():
    ap = argparse.ArgumentParser(description="统一存储查询入口（后端无关）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_dump = sub.add_parser("dump", help="导出子表内容")
    p_dump.add_argument("--sheet", required=True,
                        help="子表名：训练记录/体重记录/饮食记录/用户档案")
    p_dump.add_argument("--range", help="A1:H200 形式，不给用各表默认范围")
    p_dump.add_argument("--format", choices=["csv", "json"], default="csv")
    p_info = sub.add_parser("info", help="当前后端与数据位置")
    args = ap.parse_args()
    config = fl.load_config()
    {"dump": cmd_dump, "info": cmd_info}[args.cmd](config, args)


if __name__ == "__main__":
    main()
