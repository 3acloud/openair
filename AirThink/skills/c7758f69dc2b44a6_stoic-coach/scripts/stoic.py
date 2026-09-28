#!/usr/bin/env python3
"""
Stoic Coach 数据引擎
记录、统计、洞察、语录、导出——纯 Python 标准库实现，无第三方依赖。

用法：
  stoic.py log --exercise-id 1 --state-before 7 --state-after 4 \
      --insight "..." --tags 焦虑,工作 --duration 10
  stoic.py history [--limit N]
  stoic.py stats
  stoic.py insight
  stoic.py daily
  stoic.py export --format md|json [--output FILE]
"""

import argparse
import json
import os
import sys
import uuid
from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# 常量与元数据
# ---------------------------------------------------------------------------

DATA_DIR = os.environ.get(
    "STOIC_COACH_DATA_DIR",
    os.path.join(os.path.expanduser("~"), ".stoic-coach"),
)
JOURNAL_FILE = os.path.join(DATA_DIR, "journal.jsonl")

MODULES = {
    1: "控制二分法",
    2: "四大美德",
    3: "正念与智慧模式",
    4: "热爱命运与全然接纳",
    5: "韧性训练",
}

EXERCISES = {
    1:  ("拆分担忧", 1), 2:  ("命运许可保留条款", 1),
    3:  ("耐受不确定性六问", 1), 4:  ("逃出猴子陷阱", 1),
    5:  ("价值观澄清", 2), 6:  ("美德自评", 2),
    7:  ("人际交往复盘", 2), 8:  ("识别愤怒苗头", 2),
    9:  ("择善而从（贤人模仿法）", 2), 10: ("撰写自己的沉思录", 2),
    11: ("斯多葛正念练习", 3), 12: ("冲动行为复盘", 3),
    13: ("智慧模式四要素自检", 3),
    14: ("全然接纳", 4), 15: ("背诵斯多葛语录", 4),
    16: ("辩证法双视角陈述", 4), 17: ("责任分类法", 4),
    18: ("拒绝接纳的成本核算", 4),
    19: ("自愿不适暴露", 5), 20: ("从高处着眼（认知距离法）", 5),
    21: ("适应不适练习", 5), 22: ("灾难化检验", 5),
    23: ("预设逆境", 5), 24: ("勿忘你终有一死（memento mori）", 5),
    25: ("放手练习", 5),
}

QUOTES_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "references", "quotes.md"
)


def exercise_name(eid: int) -> str:
    return EXERCISES[eid][0] if eid in EXERCISES else f"练习{eid}"


def module_name(eid: int) -> str:
    mid = EXERCISES[eid][1] if eid in EXERCISES else 0
    return MODULES.get(mid, "未知模块")


# ---------------------------------------------------------------------------
# 存储层
# ---------------------------------------------------------------------------

def load_entries():
    if not os.path.exists(JOURNAL_FILE):
        return []
    entries = []
    with open(JOURNAL_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def save_entry(entry: dict) -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(JOURNAL_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


# ---------------------------------------------------------------------------
# 命令实现
# ---------------------------------------------------------------------------

def cmd_log(args):
    eid = args.exercise_id
    if eid not in EXERCISES:
        print(f"❌ 无效的练习编号 {eid}（有效范围 1-25）")
        return 1
    entry = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "date": date.today().isoformat(),
        "exercise_id": eid,
        "exercise_name": exercise_name(eid),
        "module": module_name(eid),
        "state_before": args.state_before,
        "state_after": args.state_after,
        "insight": args.insight or "",
        "tags": [t.strip() for t in (args.tags or "").split(",") if t.strip()],
        "duration_min": args.duration,
    }
    save_entry(entry)
    print(f"✅ 已记录：[{entry['module']}] {entry['exercise_name']}")
    if entry["state_before"] is not None and entry["state_after"] is not None:
        improved = entry["state_before"] - entry["state_after"]
        change = f"（不适程度改善 {improved:+d} 分）" if improved else "（持平）"
        print(f"   状态 {entry['state_before']} → {entry['state_after']} {change}")
    if entry["insight"]:
        print(f"   心得：{entry['insight']}")
    return 0


def cmd_history(args):
    entries = load_entries()
    if not entries:
        print("📚 还没有任何练习记录。第一次练习从现在开始。")
        return 0
    entries = entries[-args.limit:]
    print(f"📖 最近 {len(entries)} 条记录：\n")
    for e in reversed(entries):
        change = ""
        if e.get("state_before") is not None and e.get("state_after") is not None:
            d = e["state_before"] - e["state_after"]  # 正数=不适改善
            change = f"｜不适 {e['state_before']}→{e['state_after']}（改善{d:+d}）" if d else f"｜不适 {e['state_before']}→{e['state_after']}"
        print(f"· {e['date']} [{e['module']}] {e['exercise_name']}{change}")
        if e.get("insight"):
            print(f"  └ “{e['insight']}”")
    return 0


def cmd_stats(_args):
    entries = load_entries()
    if not entries:
        print("📊 还没有数据。练一次，再来找我。")
        return 0

    dates = sorted({e["date"] for e in entries})
    # 连续天数（截至今天或最近一次练习）
    streak, cursor = 0, date.today()
    ds = set(dates)
    if date.today().isoformat() not in ds:  # 今天没练，从最近一天起算
        latest = datetime.strptime(dates[-1], "%Y-%m-%d").date()
        cursor = latest
    while cursor.isoformat() in ds:
        streak += 1
        cursor -= timedelta(days=1)

    mod_count = {}
    ex_count = {}
    for e in entries:
        mod_count[e["module"]] = mod_count.get(e["module"], 0) + 1
        ex_count[e["exercise_name"]] = ex_count.get(e["exercise_name"], 0) + 1

    # 正数 = 不适程度下降（改善）
    deltas = [e["state_before"] - e["state_after"] for e in entries
              if e.get("state_before") is not None and e.get("state_after") is not None]

    print("📊 练习总览\n" + "─" * 36)
    print(f"总练习次数：{len(entries)} 次")
    print(f"覆盖天数：{len(dates)} 天（首次 {dates[0]}，最近 {dates[-1]}）")
    print(f"连续练习：{streak} 天")
    if deltas:
        avg = sum(deltas) / len(deltas)
        print(f"不适改善：平均 {avg:+.1f} 分（{len(deltas)} 次有前后对比）")
        print(f"练后感觉更好：{sum(1 for d in deltas if d > 0)}/{len(deltas)} 次")
    print(f"涉及练习：{len(ex_count)} 种 / 25 种")

    print("\n模块分布：")
    for m in sorted(mod_count, key=mod_count.get, reverse=True):
        bar = "█" * mod_count[m]
        print(f"  {m}：{bar} {mod_count[m]}")

    top = sorted(ex_count.items(), key=lambda x: -x[1])[:3]
    if top:
        print("\n最常练：")
        for name, n in top:
            print(f"  · {name}（{n} 次）")
    return 0


def cmd_insight(_args):
    entries = load_entries()
    if len(entries) < 2:
        print("🔍 记录还太少（至少 2 条才能看出模式）。多练几次，我再帮你照镜子。")
        return 0

    print("🔍 自我洞察报告\n" + "═" * 40)
    dates = sorted({e["date"] for e in entries})
    ds = set(dates)

    # 连续天数
    streak, cursor = 0, date.today()
    if date.today().isoformat() not in ds:
        cursor = datetime.strptime(dates[-1], "%Y-%m-%d").date()
    while cursor.isoformat() in ds:
        streak += 1
        cursor -= timedelta(days=1)

    # 模块分布
    mod_count = {}
    for e in entries:
        mod_count[e["module"]] = mod_count.get(e["module"], 0) + 1
    total = len(entries)
    dominant = max(mod_count, key=mod_count.get)
    dom_pct = mod_count[dominant] / total * 100

    # 练习有效性（正数 = 改善）
    eff = {}
    for e in entries:
        if e.get("state_before") is None or e.get("state_after") is None:
            continue
        eff.setdefault(e["exercise_name"], []).append(
            e["state_before"] - e["state_after"])
    best = max(
        ((n, sum(v) / len(v), len(v)) for n, v in eff.items() if len(v) >= 1),
        key=lambda x: x[1], default=None)

    # 近 7 天 vs 之前 7 天
    today = date.today()
    recent = [e for e in entries
              if (today - datetime.strptime(e["date"], "%Y-%m-%d").date()).days <= 7]
    prev = [e for e in entries
            if 7 < (today - datetime.strptime(e["date"], "%Y-%m-%d").date()).days <= 14]

    # 被忽视的模块
    untouched = [m for m in MODULES.values() if m not in mod_count]

    # 标签
    tags = {}
    for e in entries:
        for t in e.get("tags", []):
            tags[t] = tags.get(t, 0) + 1
    top_tags = sorted(tags.items(), key=lambda x: -x[1])[:3]

    print(f"**坚持**：共 {total} 次练习、{len(dates)} 天，"
          f"{'当前连续 ' + str(streak) + ' 天' if streak > 0 else '最近一次 ' + dates[-1]}。")

    if len(mod_count) == 1:
        only = next(iter(mod_count))
        print(f"\n**你的模式**：目前只接触过「{only}」一个模块——"
              f"这是入口，不是全部。")
    else:
        print(f"\n**你的模式**：{dom_pct:.0f}% 的练习集中在「{dominant}」——"
              f"它似乎是你最常面对的课题。")

    if best and best[1] > 0:
        print(f"**最有效的练习**：「{best[0]}」——平均改善 {best[1]:+.1f} 分"
              f"（{best[2]} 次）。它的方法值得常用。")

    if top_tags:
        tag_str = "、".join(f"{t}（{n}次）" for t, n in top_tags)
        print(f"**高频标签**：{tag_str}。这些词是你生活的常客。")

    if untouched:
        print(f"**尚未探索**：{('、'.join(untouched))}。好奇的话，可以挑一个试试。")

    if recent or prev:
        trend = ""
        if len(recent) > len(prev) and prev:
            trend = f"近 7 天 {len(recent)} 次，比之前 7 天（{len(prev)} 次）更勤了。"
        elif prev and len(recent) < len(prev):
            trend = f"近 7 天 {len(recent)} 次，比之前 7 天（{len(prev)} 次）松了一些——没关系，回来就好。"
        elif recent:
            trend = f"近 7 天 {len(recent)} 次。"
        if trend:
            print(f"**节奏**：{trend}")

    # 引用用户原话
    insights = [e for e in entries if e.get("insight")]
    if insights:
        print("\n**你自己写下的**：")
        shown = set()
        for e in reversed(insights):
            if e["exercise_name"] in shown:
                continue
            shown.add(e["exercise_name"])
            print(f"  「{e['insight']}」——{e['date']}，{e['exercise_name']}")
            if len(shown) >= 3:
                break

    print("\n（报告基于本地记录自动生成。数字只是镜子，镜子里的人是你。）")
    return 0


def cmd_daily(_args):
    quotes = []
    if os.path.exists(QUOTES_FILE):
        with open(QUOTES_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and line[0].isdigit() and '"' in line:
                    quotes.append(line[line.find('"'):])
    if not quotes:
        print("（语录库暂时不在身边。记住：你无法控制发生的事，但可以控制如何应对。）")
        return 0
    idx = date.today().toordinal() % len(quotes)
    print(f"📜 今日一句（{date.today().isoformat()}）：\n\n  {quotes[idx]}\n")
    print("（同一天再来，还是这句；明天换新。）")
    return 0


def cmd_export(args):
    entries = load_entries()
    if not entries:
        print("📂 没有可导出的记录。")
        return 0
    fmt = args.format
    out = args.output or f"stoic-export-{date.today().isoformat()}.{fmt}"

    if fmt == "json":
        with open(out, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    else:  # md
        lines = ["# 我的斯多葛练习记录", "",
                f"导出时间：{datetime.now().isoformat(timespec='seconds')}",
                f"共 {len(entries)} 条记录", "", "## 记录", ""]
        for e in reversed(entries):
            lines.append(f"### {e['date']} · {e['exercise_name']}（{e['module']}）")
            if e.get("state_before") is not None:
                lines.append(f"- 状态：{e['state_before']} → {e['state_after']}")
            if e.get("duration_min"):
                lines.append(f"- 时长：{e['duration_min']} 分钟")
            if e.get("tags"):
                lines.append(f"- 标签：{'、'.join(e['tags'])}")
            if e.get("insight"):
                lines.append(f"- 心得：{e['insight']}")
            lines.append("")
        with open(out, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    print(f"✅ 已导出 {len(entries)} 条记录 → {out}")
    return 0


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="stoic", description="斯多葛教练数据引擎")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("log", help="记录一次练习")
    p.add_argument("--exercise-id", type=int, required=True, help="练习编号 1-25")
    p.add_argument("--state-before", type=int, default=None, help="练习前状态 0-10")
    p.add_argument("--state-after", type=int, default=None, help="练习后状态 0-10")
    p.add_argument("--insight", default="", help="一句话收获")
    p.add_argument("--tags", default="", help="标签，逗号分隔")
    p.add_argument("--duration", type=int, default=None, help="时长（分钟）")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("history", help="查看历史记录")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("stats", help="统计总览")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("insight", help="生成自我洞察报告")
    p.set_defaults(func=cmd_insight)

    p = sub.add_parser("daily", help="每日一句斯多葛语录")
    p.set_defaults(func=cmd_daily)

    p = sub.add_parser("export", help="导出记录")
    p.add_argument("--format", choices=["md", "json"], default="md")
    p.add_argument("--output", default=None)
    p.set_defaults(func=cmd_export)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
