#!/usr/bin/env python3
"""查账统计脚本 - 支持多种查询模式和统计汇总"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

DATA_FILE = "./expense_records.json"


def load_records():
    """加载所有记录"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("records", [])
    except (json.JSONDecodeError, IOError):
        return []


def get_date_range(period):
    """根据周期获取日期范围"""
    today = datetime.now()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "today":
        end = start + timedelta(days=1)
    elif period == "week":
        start = start - timedelta(days=start.weekday())
        end = start + timedelta(days=7)
    elif period == "month":
        start = start.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
    elif period == "year":
        start = start.replace(month=1, day=1)
        end = start.replace(year=start.year + 1)
    else:
        return None, None

    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def filter_records(records, start_date=None, end_date=None, category=None,
                   record_type=None, fuzzy_category=False):
    """筛选记录"""
    filtered = records

    if start_date:
        filtered = [r for r in filtered if r.get("date", "") >= start_date]
    if end_date:
        filtered = [r for r in filtered if r.get("date", "") <= end_date]
    if record_type:
        filtered = [r for r in filtered if r.get("type") == record_type]
    if category:
        if fuzzy_category:
            cat_lower = category.lower()
            filtered = [r for r in filtered
                        if cat_lower in r.get("category", "").lower()]
        else:
            filtered = [r for r in filtered if r.get("category") == category]

    return filtered


def calculate_summary(records):
    """计算统计汇总"""
    income = sum(r["amount"] for r in records if r.get("type") == "income")
    expense = sum(r["amount"] for r in records if r.get("type") == "expense")

    # 按类目统计
    category_stats = {}
    for r in records:
        cat = r.get("category", "其他")
        if cat not in category_stats:
            category_stats[cat] = {"income": 0, "expense": 0, "count": 0}
        category_stats[cat][r.get("type", "expense")] += r["amount"]
        category_stats[cat]["count"] += 1

    # 收支笔数
    income_count = len([r for r in records if r.get("type") == "income"])
    expense_count = len([r for r in records if r.get("type") == "expense"])

    return {
        "total_income": round(income, 2),
        "total_expense": round(expense, 2),
        "net": round(income - expense, 2),
        "income_count": income_count,
        "expense_count": expense_count,
        "category_breakdown": category_stats
    }


def query_recent(records, limit=20):
    """查询最近记录"""
    sorted_records = sorted(records, key=lambda x: x.get("created_at", ""), reverse=True)
    return sorted_records[:limit]


def query_detail(records, start_date=None, end_date=None, category=None,
                 record_type=None, fuzzy_category=False, limit=100):
    """查询明细"""
    filtered = filter_records(records, start_date, end_date, category,
                              record_type, fuzzy_category)

    # 按日期倒序
    filtered = sorted(filtered, key=lambda x: (x.get("date", ""), x.get("created_at", "")),
                     reverse=True)

    return filtered[:limit]


def query_summary(records, start_date=None, end_date=None, period=None):
    """查询统计汇总"""
    # 确定日期范围
    if not start_date or not end_date:
        s, e = get_date_range(period or "month")
        start_date = start_date or s
        end_date = end_date or e

    filtered = filter_records(records, start_date, end_date)
    summary = calculate_summary(filtered)
    summary["start_date"] = start_date
    summary["end_date"] = end_date
    summary["record_count"] = len(filtered)

    return summary


def main():
    parser = argparse.ArgumentParser(description="查账统计脚本")
    parser.add_argument("--mode", choices=["summary", "detail", "recent"],
                       default="recent", help="查询模式")
    parser.add_argument("--period", choices=["today", "week", "month", "year"],
                       help="时间周期")
    parser.add_argument("--start-date", help="开始日期 (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="结束日期 (YYYY-MM-DD)")
    parser.add_argument("--category", help="类目名称")
    parser.add_argument("--type", choices=["income", "expense"], help="收支类型过滤")
    parser.add_argument("--limit", type=int, default=20, help="返回条数")

    args = parser.parse_args()

    records = load_records()

    if not records:
        print(json.dumps({"status": "empty", "message": "暂无记录"}))
        sys.exit(0)

    try:
        if args.mode == "recent":
            result = query_recent(records, args.limit)
            print(json.dumps({
                "status": "success",
                "mode": "recent",
                "records": result
            }, ensure_ascii=False))
        elif args.mode == "detail":
            result = query_detail(
                records,
                args.start_date,
                args.end_date,
                args.category,
                args.type,
                limit=args.limit
            )
            print(json.dumps({
                "status": "success",
                "mode": "detail",
                "records": result
            }, ensure_ascii=False))
        elif args.mode == "summary":
            result = query_summary(
                records,
                args.start_date,
                args.end_date,
                args.period
            )
            print(json.dumps({
                "status": "success",
                "mode": "summary",
                "summary": result
            }, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
