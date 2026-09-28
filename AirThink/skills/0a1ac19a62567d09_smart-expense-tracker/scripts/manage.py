#!/usr/bin/env python3
"""记录管理脚本 - 修改和删除记账记录"""

import argparse
import json
import os
import sys
from datetime import datetime

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


def save_records(records):
    """保存记录"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"records": records}, f, ensure_ascii=False, indent=2)


def find_record_by_id(records, record_id):
    """根据ID查找记录"""
    for i, r in enumerate(records):
        if r.get("id") == record_id:
            return i, r
    return None, None


def update_record(records, record_id, field, value):
    """更新单条记录"""
    idx, record = find_record_by_id(records, record_id)
    if record is None:
        return None, "记录不存在"

    # 验证字段
    if field not in ["category", "amount", "description", "date"]:
        return None, f"不支持修改字段: {field}"

    # 类型转换
    if field == "amount":
        try:
            value = float(value)
            if value <= 0:
                return None, "金额必须大于0"
        except ValueError:
            return None, "无效的金额格式"
    elif field == "date":
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None, "日期格式应为 YYYY-MM-DD"

    records[idx][field] = value
    return records[idx], None


def delete_record(records, record_id):
    """删除单条记录"""
    idx, record = find_record_by_id(records, record_id)
    if record is None:
        return None, "记录不存在"

    deleted = records.pop(idx)
    return deleted, None


def delete_batch(records, start_date=None, end_date=None, category=None):
    """批量删除记录"""
    if not start_date and not end_date and not category:
        return [], "至少需要指定一个删除条件"

    deleted = []
    remaining = []

    for r in records:
        match = True

        if start_date and r.get("date", "") < start_date:
            match = False
        if end_date and r.get("date", "") > end_date:
            match = False
        if category and r.get("category") != category:
            match = False

        if match:
            deleted.append(r)
        else:
            remaining.append(r)

    return deleted, None


def main():
    parser = argparse.ArgumentParser(description="记录管理脚本")
    parser.add_argument("--action", choices=["update", "delete", "delete-batch"],
                       required=True, help="操作类型")
    parser.add_argument("--id", help="记录ID (update/delete时必需)")
    parser.add_argument("--field", choices=["category", "amount", "description", "date"],
                       help="要修改的字段 (update时必需)")
    parser.add_argument("--value", help="新值 (update时必需)")
    parser.add_argument("--start-date", help="开始日期 (delete-batch时)")
    parser.add_argument("--end-date", help="结束日期 (delete-batch时)")
    parser.add_argument("--category", help="类目 (delete-batch时)")

    args = parser.parse_args()

    records = load_records()

    if not records:
        print(json.dumps({"status": "error", "message": "暂无记录"}))
        sys.exit(1)

    try:
        if args.action == "update":
            if not args.id or not args.field or args.value is None:
                print(json.dumps({"status": "error",
                                "message": "update操作需要 --id --field --value"}))
                sys.exit(1)

            updated, error = update_record(records, args.id, args.field, args.value)
            if error:
                print(json.dumps({"status": "error", "message": error}))
                sys.exit(1)

            save_records(records)
            print(json.dumps({
                "status": "success",
                "message": "记录已更新",
                "record": updated
            }, ensure_ascii=False))

        elif args.action == "delete":
            if not args.id:
                print(json.dumps({"status": "error", "message": "delete操作需要 --id"}))
                sys.exit(1)

            deleted, error = delete_record(records, args.id)
            if error:
                print(json.dumps({"status": "error", "message": error}))
                sys.exit(1)

            save_records(records)
            print(json.dumps({
                "status": "success",
                "message": "记录已删除",
                "deleted": deleted
            }, ensure_ascii=False))

        elif args.action == "delete-batch":
            deleted, error = delete_batch(
                records,
                args.start_date,
                args.end_date,
                args.category
            )
            if error:
                print(json.dumps({"status": "error", "message": error}))
                sys.exit(1)

            save_records(records)
            print(json.dumps({
                "status": "success",
                "message": f"已删除 {len(deleted)} 条记录",
                "deleted_count": len(deleted)
            }, ensure_ascii=False))

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
