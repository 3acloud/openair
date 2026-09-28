#!/usr/bin/env python3
"""剥离 _meta 数据文件中的逐字原文字段，保留纯数值统计。

版权面在文本字段（标题、机构、首末句、提领句），不在数值字段。
剥完的文件仍可支撑参数复算，但无法反查源篇目。

用法: python3 strip_meta.py            # 原地改写
      python3 strip_meta.py --dry-run  # 只报告
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 文件 → 要剥掉的字段
STRIP = {
    '公文语料/_meta/all_pieces.json': ['title', 'org', 'first_sent', 'last_sent', 'h1_list'],
    '党建语料/_meta/l2_struct.json': ['title', 'leads', 'subs'],
}
# 剥完只剩计数字段、信息量不足以独立存在的文件
DELETE = ['党建语料/_meta/l2_leads.json']


def strip_file(rel, fields, dry):
    path = ROOT / rel
    if not path.exists():
        print(f'  跳过（不存在）: {rel}')
        return
    items = json.loads(path.read_text(encoding='utf-8'))
    removed = {f: 0 for f in fields}
    for it in items:
        for f in fields:
            if f in it:
                del it[f]
                removed[f] += 1
    kept = sorted(items[0].keys()) if items else []
    print(f'  {rel}')
    print(f'    剥离 {len(items)} 条 × {[f + "×" + str(n) for f, n in removed.items()]}')
    print(f'    保留字段: {kept}')
    if not dry:
        path.write_text(json.dumps(items, ensure_ascii=False, indent=1) + '\n',
                        encoding='utf-8')


def main():
    dry = '--dry-run' in sys.argv
    print('剥离逐字原文字段：' if not dry else '（dry-run）将剥离：')
    for rel, fields in STRIP.items():
        strip_file(rel, fields, dry)
    print('\n整体删除（剥完无剩余信息）：')
    for rel in DELETE:
        path = ROOT / rel
        print(f'  {rel} {"（不存在）" if not path.exists() else ""}')
        if not dry and path.exists():
            path.unlink()


if __name__ == '__main__':
    main()
