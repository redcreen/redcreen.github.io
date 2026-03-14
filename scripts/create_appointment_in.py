#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭预约入库单创建程序

用法:
    python create_appointment_in.py <仓库ID> <外部单号> <预约日期> <商品JSON>

示例:
    python create_appointment_in.py 13440882 "APP001" "2026-03-20 14:00:00" '[{"sku_id":"SKU001","qty":100,"item_type":"正品"}]'

特性:
    - 自动管理 Token（过期前12小时自动刷新）
    - 支持可选参数：采购单号、备注
"""

import sys
import json
import os

# 添加脚本目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jushuitan_appointment_in_auto import create_appointment_in


def main():
    if len(sys.argv) < 5:
        print("Usage: python create_appointment_in.py <wms_co_id> <external_id> <plan_arrive_date> <items_json>")
        print()
        print("Example:")
        print('  python create_appointment_in.py 13440882 "APP001" "2026-03-20 14:00:00" \'[{"sku_id":"SKU001","qty":100}]\'')
        print()
        print("Optional env vars:")
        print("  PO_ID       - 采购单号")
        print("  REMARK      - 备注")
        sys.exit(1)
    
    wms_co_id = int(sys.argv[1])
    external_id = sys.argv[2]
    plan_arrive_date = sys.argv[3]
    items = json.loads(sys.argv[4])
    
    po_id = os.environ.get('PO_ID')
    remark = os.environ.get('REMARK', '')
    
    result = create_appointment_in(
        wms_co_id=wms_co_id,
        external_id=external_id,
        plan_arrive_date=plan_arrive_date,
        items=items,
        po_id=po_id,
        remark=remark
    )
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 返回退出码
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
