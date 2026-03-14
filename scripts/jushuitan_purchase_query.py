#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭采购单查询
"""

import sys
sys.path.insert(0, 'scripts')

from jushuitan_appointment_in_auto import TokenManager
import json
import requests
from datetime import datetime, timedelta

# API配置
APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
BASE_URL = "https://openapi.jushuitan.com"

# 状态映射
STATUS_MAP = {
    'Creating': '草拟',
    'WaitConfirm': '待审核',
    'Confirmed': '已确认',
    'WaitDeliver': '待发货',
    'WaitReceive': '待收货',
    'Finished': '完成',
    'Cancelled': '作废',
    'Delete': '删除'
}

def query_purchase(
    page_index=1,
    page_size=30,
    modified_begin=None,
    modified_end=None,
    so_ids=None,
    po_ids=None,
    status=None,
    statuss=None,
    is_lock=None
):
    """
    查询采购单信息
    
    Args:
        page_index: 第几页，从1开始
        page_size: 每页条数，默认30，最大50
        modified_begin: 修改起始时间，格式：2021-12-02 00:00:00
        modified_end: 修改结束时间
        so_ids: 外部单号列表，如 ["PO20240314001"]
        po_ids: 采购单号列表，如 [113622, 113623]
        status: 采购单状态，如 "Confirmed"
        statuss: 采购单状态列表，如 ["WaitConfirm", "Confirmed"]
        is_lock: 是否返回运营云仓信息，"true" 或 "false"
    
    Returns:
        采购单列表
    """
    # 获取token
    access_token = TokenManager.get_valid_token()
    
    # 构建业务参数
    biz_content = {
        'page_index': page_index,
        'page_size': min(page_size, 50)  # 最大50
    }
    
    if modified_begin:
        biz_content['modified_begin'] = modified_begin
    if modified_end:
        biz_content['modified_end'] = modified_end
    if so_ids:
        biz_content['so_ids'] = so_ids if isinstance(so_ids, list) else [so_ids]
    if po_ids:
        biz_content['po_ids'] = po_ids if isinstance(po_ids, list) else [po_ids]
    if status:
        biz_content['status'] = status
    if statuss:
        biz_content['statuss'] = statuss if isinstance(statuss, list) else [statuss]
    if is_lock:
        biz_content['is_lock'] = is_lock
    
    # 构建请求参数
    import time
    timestamp = int(time.time())
    
    params = {
        'app_key': APP_KEY,
        'access_token': access_token,
        'timestamp': timestamp,
        'charset': 'utf-8',
        'version': '2',
        'biz': json.dumps(biz_content, ensure_ascii=False)
    }
    
    # 计算签名
    sign = TokenManager.generate_sign(params)
    params['sign'] = sign
    
    # 发送请求
    url = f"{BASE_URL}/open/purchase/query"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=params, headers=headers)
    return response.json()


if __name__ == "__main__":
    # 示例1：查询最近7天的采购单
    print("=" * 70)
    print("示例1：查询最近7天的采购单")
    print("=" * 70)
    
    end_time = datetime.now()
    begin_time = end_time - timedelta(days=7)
    
    result = query_purchase(
        modified_begin=begin_time.strftime('%Y-%m-%d %H:%M:%S'),
        modified_end=end_time.strftime('%Y-%m-%d %H:%M:%S'),
        page_size=10
    )
    
    if result.get('code') == 0:
        data = result.get('data', {})
        purchases = data.get('datas', [])
        
        print(f"\n总条数: {data.get('data_count', 0)}")
        print(f"总页数: {data.get('page_count', 0)}")
        
        if purchases:
            print("\n" + "=" * 70)
            print("采购单列表：")
            print("=" * 70)
            
            for po in purchases:
                status_cn = STATUS_MAP.get(po.get('status'), po.get('status'))
                print(f"\n采购单号: {po.get('po_id')}")
                print(f"  外部单号: {po.get('so_id') or '无'}")
                print(f"  采购日期: {po.get('po_date')}")
                print(f"  状态: {status_cn} ({po.get('status')})")
                print(f"  供应商: {po.get('seller') or '未知'} (ID: {po.get('supplier_id')})")
                print(f"  采购员: {po.get('purchaser_name') or '未指定'}")
                print(f"  送货地址: {po.get('send_address') or '未指定'}")
                print(f"  仓库编号: {po.get('wms_co_id') or '主仓'}")
                print(f"  备注: {po.get('remark') or '无'}")
                
                # 商品明细
                items = po.get('items', [])
                if items:
                    print(f"  商品明细 ({len(items)}项):")
                    for item in items:
                        print(f"    - {item.get('sku_id')}: {item.get('name')} x {item.get('qty')} @ {item.get('price')}")
                
                print("-" * 70)
        else:
            print("\n暂无采购单数据")
    else:
        print(f"查询失败: {result.get('msg')}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 示例2：按采购单号查询（如果有的话）
    print("\n" + "=" * 70)
    print("示例2：按采购单号查询 (po_id=241604)")
    print("=" * 70)
    
    result2 = query_purchase(po_ids=[241604])
    
    if result2.get('code') == 0 and result2.get('data', {}).get('datas'):
        po = result2['data']['datas'][0]
        status_cn = STATUS_MAP.get(po.get('status'), po.get('status'))
        print(f"\n采购单号: {po.get('po_id')}")
        print(f"  外部单号: {po.get('so_id') or '无'}")
        print(f"  状态: {status_cn}")
        print(f"  供应商: {po.get('seller')}")
    else:
        print("未找到该采购单或查询失败")
