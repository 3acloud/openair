#!/usr/bin/env python3
"""记账记录脚本 - 支持批量新增记录"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime

DATA_FILE = "./expense_records.json"


def load_records():
    """加载现有记录"""
    if not os.path.exists(DATA_FILE):
        return {"records": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"records": []}


def save_records(data):
    """保存记录"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def validate_record(record):
    """验证记录格式"""
    required = ["type", "category", "amount"]
    for field in required:
        if field not in record:
            raise ValueError(f"缺少必需字段: {field}")

    if record["type"] not in ["income", "expense"]:
        raise ValueError(f"无效的type值: {record['type']}，应为 income 或 expense")

    try:
        record["amount"] = float(record["amount"])
        if record["amount"] <= 0:
            raise ValueError("金额必须大于0")
    except (ValueError, TypeError):
        raise ValueError(f"无效的金额: {record['amount']}")

    if "date" not in record or not record["date"]:
        record["date"] = datetime.now().strftime("%Y-%m-%d")

    # 验证日期格式
    try:
        datetime.strptime(record["date"], "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"无效的日期格式: {record['date']}，应为 YYYY-MM-DD")

    return record


def add_records(records_list):
    """添加多条记录"""
    data = load_records()

    added = []
    errors = []

    for idx, rec in enumerate(records_list):
        try:
            validated = validate_record(rec.copy())
            record_id = str(uuid.uuid4())
            new_record = {
                "id": record_id,
                "type": validated["type"],
                "category": validated["category"],
                "amount": validated["amount"],
                "description": validated.get("description", ""),
                "date": validated["date"],
                "created_at": datetime.now().isoformat()
            }
            data["records"].append(new_record)
            added.append(record_id)
        except ValueError as e:
            errors.append({"index": idx, "error": str(e)})

    save_records(data)

    return {"added": added, "errors": errors, "total": len(records_list)}


def main():
    parser = argparse.ArgumentParser(description="记账记录脚本")
    parser.add_argument("--records", required=True, help="JSON格式的记录列表")
    args = parser.parse_args()

    try:
        records_list = json.loads(args.records)
        if not isinstance(records_list, list):
            records_list = [records_list]
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"JSON解析失败: {e}"}))
        sys.exit(1)

    result = add_records(records_list)

    if result["errors"]:
        print(json.dumps({
            "status": "partial",
            "message": f"成功添加 {len(result['added'])} 条，失败 {len(result['errors'])} 条",
            "added_ids": result["added"],
            "errors": result["errors"]
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "status": "success",
            "message": f"成功添加 {len(result['added'])} 条记录",
            "added_ids": result["added"]
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
