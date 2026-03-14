#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预约入库命令行工具
用法: python appointment_in_cli.py <仓库ID> <采购单号> <外部单号> <预约日期> <SKU:数量> [备注]

示例:
    python appointment_in_cli.py 13440882 PO001 EXT001 "2026-03-15 10:00:00" "NH500-1:100,NH500-2:50" "测试入库"
"""

import sys
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.jushuitan_appointment_in import create_appointment_in

def parse_items(items_str: str) -> list:
    """解析商品字符串，格式: SKU1:数量1,SKU2:数量2"""
    items = []
    for item in items_str.split(','):
        if ':' in item:
            sku_id, qty = item.split(':')
            items.append({
                'sku_id': sku_id.strip(),
                'qty': int(qty.strip())
            })
    return items

def main():
    if len(sys.argv) < 6:
        print("用法: python appointment_in_cli.py <仓库ID> <采购单号> <外部单号> <预约日期> <SKU:数量> [备注]")
        print("")
        print("参数说明:")
        print("  仓库ID      - 仓库编号，如: 13440882")
        print("  采购单号    - 聚水潭采购单号")
        print("  外部单号    - 外部系统单号")
        print("  预约日期    - 格式: YYYY-MM-DD HH:MM:SS")
        print("  SKU:数量    - 商品明细，多个用逗号分隔，如: NH500-1:100,NH500-2:50")
        print("  备注        - 可选")
        print("")
        print("示例:")
        print('  python appointment_in_cli.py 13440882 PO001 EXT001 "2026-03-15 10:00:00" "NH500-1:100"')
        sys.exit(1)
    
    wms_co_id = int(sys.argv[1])
    po_id = sys.argv[2]
    external_id = sys.argv[3]
    plan_arrive_date = sys.argv[4]
    items_str = sys.argv[5]
    remark = sys.argv[6] if len(sys.argv) > 6 else ""
    
    # 解析商品
    items = parse_items(items_str)
    
    if not items:
        print("[x] 商品格式错误，请使用: SKU:数量,SKU:数量")
        sys.exit(1)
    
    print("[*] 创建预约入库单...")
    print(f"    仓库: {wms_co_id}")
    print(f"    采购单: {po_id}")
    print(f"    外部单号: {external_id}")
    print(f"    预约日期: {plan_arrive_date}")
    print(f"    商品: {items}")
    
    result = create_appointment_in(
        wms_co_id=wms_co_id,
        po_id=po_id,
        external_id=external_id,
        plan_arrive_date=plan_arrive_date,
        items=items,
        remark=remark
    )
    
    print("\n" + "=" * 50)
    if result.get('success'):
        print("[✓] 预约入库单创建成功!")
        print(f"    消息: {result.get('msg')}")
        if result.get('data'):
            print(f"    数据: {json.dumps(result.get('data'), indent=2, ensure_ascii=False)}")
    else:
        print("[x] 创建失败!")
        print(f"    错误码: {result.get('code')}")
        print(f"    错误信息: {result.get('msg')}")
    print("=" * 50)

if __name__ == '__main__':
    main()
