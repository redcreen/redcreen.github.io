#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭仓库查询
"""

import sys
sys.path.insert(0, 'scripts')

from jushuitan_appointment_in_auto import TokenManager
import json
import requests

# API配置
APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
BASE_URL = "https://openapi.jushuitan.com"

def query_warehouse(
    page_index=1,
    page_size=30
):
    """
    查询仓库信息
    
    Args:
        page_index: 第几页，从1开始
        page_size: 每页条数，默认30
    
    Returns:
        仓库列表
    """
    # 获取token
    access_token = TokenManager.get_valid_token()
    
    # 构建业务参数
    biz_content = {
        'page_index': page_index,
        'page_size': page_size
    }
    
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
    url = f"{BASE_URL}/open/wms/partner/query"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=params, headers=headers)
    return response.json()


if __name__ == "__main__":
    # 查询仓库列表
    print("=" * 60)
    print("查询仓库列表")
    print("=" * 60)
    
    result = query_warehouse(page_size=100)
    
    if result.get('code') == 0:
        data = result.get('data', {})
        warehouses = data.get('datas', [])
        
        print(f"\n总条数: {data.get('data_count', 0)}")
        print(f"总页数: {data.get('page_count', 0)}")
        print(f"当前页: {data.get('page_index', 0)}")
        print("\n" + "=" * 60)
        print("仓库列表：")
        print("=" * 60)
        
        for wh in warehouses:
            print(f"\n仓库名称: {wh.get('name')}")
            print(f"  仓库编号 (wms_co_id): {wh.get('wms_co_id')}")
            print(f"  主仓公司编号 (co_id): {wh.get('co_id')}")
            print(f"  是否主仓: {'是' if wh.get('is_main') else '否'}")
            print(f"  状态: {wh.get('status')}")
            if wh.get('remark1'):
                print(f"  对方备注: {wh.get('remark1')}")
            if wh.get('remark2'):
                print(f"  我方备注: {wh.get('remark2')}")
            print("-" * 60)
    else:
        print(f"查询失败: {result.get('msg')}")
        print(json.dumps(result, indent=2, ensure_ascii=False))
