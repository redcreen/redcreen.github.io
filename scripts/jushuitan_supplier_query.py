#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭供应商查询
"""

import sys
sys.path.insert(0, 'scripts')

from jushuitan_appointment_in_auto import TokenManager
import json
import requests

# API配置
APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
BASE_URL = "https://openapi.jushuitan.com"

def query_supplier(
    names=None,
    supplier_codes=None,
    supplier_ids=None,
    page_index=1,
    page_size=30,
    modified_begin=None,
    modified_end=None
):
    """
    查询供应商信息
    
    Args:
        names: 供应商名称列表，如 ["徐凯"]
        supplier_codes: 供应商编码列表
        supplier_ids: 供应商内部编码列表
        page_index: 第几页，从1开始
        page_size: 每页条数，默认30，最大500
        modified_begin: 修改起始时间，格式：2021-12-02 15:55:06
        modified_end: 修改结束时间
    
    Returns:
        供应商列表
    """
    # 获取token
    access_token = TokenManager.get_valid_token()
    
    # 构建业务参数
    biz_content = {
        'page_index': page_index,
        'page_size': page_size
    }
    
    if names:
        biz_content['names'] = names if isinstance(names, list) else [names]
    
    if supplier_codes:
        biz_content['supplier_codes'] = supplier_codes if isinstance(supplier_codes, list) else [supplier_codes]
    
    if supplier_ids:
        biz_content['supplier_ids'] = supplier_ids if isinstance(supplier_ids, list) else [supplier_ids]
    
    if modified_begin:
        biz_content['modified_begin'] = modified_begin
    
    if modified_end:
        biz_content['modified_end'] = modified_end
    
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
    url = f"{BASE_URL}/open/supplier/query"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=params, headers=headers)
    return response.json()


if __name__ == "__main__":
    # 测试按名称查询"徐凯"
    print("=" * 50)
    print("查询供应商：徐凯")
    print("=" * 50)
    
    result = query_supplier(names=["徐凯"])
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 如果成功，提取关键信息
    if result.get('code') == 0 and result.get('data', {}).get('datas'):
        print("\n" + "=" * 50)
        print("查询结果：")
        print("=" * 50)
        for supplier in result['data']['datas']:
            print(f"供应商ID: {supplier.get('supplier_id')}")
            print(f"供应商编码: {supplier.get('supplier_code')}")
            print(f"供应商名称: {supplier.get('name')}")
            print(f"分类: {supplier.get('group')}")
            print(f"是否启用: {supplier.get('enabled')}")
            print(f"备注: {supplier.get('remark')}")
            print("-" * 50)
    else:
        print("\n未找到供应商或查询失败")
