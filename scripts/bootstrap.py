#!/usr/bin/env python3
"""存储后端初始化 / 状态查看。
正常使用无需手动运行：任意脚本首次运行时 fitlib.load_config() 会自动探测并初始化。
用法:
  python3 bootstrap.py status                      # 只探测环境、查看当前后端，不做修改
  python3 bootstrap.py init                         # 自动探测初始化（本地优先）
  python3 bootstrap.py init --backend local [--path /abs/减脂追踪数据.xlsx]
  python3 bootstrap.py init --backend feishu --url https://my.feishu.cn/sheets/xxx
"""
import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import fitlib as fl  # noqa: E402


def cmd_status(args):
    """只读探测，不写任何东西。"""
    report = fl.detect_report()
    if report.get("backend_in_config"):
        cfg = json.loads(fl.CONFIG_PATH.read_text(encoding="utf-8"))
        report["storage"] = fl.storage_info(cfg) if cfg.get("backend") else None
    else:
        report["storage"] = None
    report["suggestion"] = (
        "本地 xlsx 可用，init 将自动启用本地后端"
        if report["openpyxl_available"] and report["skill_dir_writable"]
        else ("本地不可用，可 pip install openpyxl；或配置飞书表格 URL 走 feishu 后端"
              if report["lark_cli_path"]
              else "请先 pip install openpyxl（推荐）或安装 lark-cli"))
    fl.out(report)


def cmd_init(args):
    # 从磁盘读原始 config（不存在则自动落空模板，不挡首次初始化）
    if not fl.CONFIG_PATH.exists():
        fl.save_config(json.loads(json.dumps(fl.DEFAULT_CONFIG)))
    config = json.loads(fl.CONFIG_PATH.read_text(encoding="utf-8"))
    if args.backend == "local":
        config = fl.bootstrap_local(config, args.path)
    elif args.backend == "feishu":
        config = fl.bootstrap_feishu(config, args.url)
    else:
        config = fl.ensure_backend(config)
    out = {"ok": True, "action": "init"}
    out.update(fl.storage_info(config))
    fl.out(out)


def main():
    ap = argparse.ArgumentParser(description="存储后端初始化/状态")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_status = sub.add_parser("status")
    p_init = sub.add_parser("init")
    p_init.add_argument("--backend", choices=["local", "feishu"],
                        help="不指定则自动探测（本地优先）")
    p_init.add_argument("--path", help="backend=local 时 xlsx 路径（默认 skill 目录旁的 减脂数据/ 下）")
    p_init.add_argument("--url", help="backend=feishu 时飞书表格 URL")
    args = ap.parse_args()
    {"status": cmd_status, "init": cmd_init}[args.cmd](args)


if __name__ == "__main__":
    main()
