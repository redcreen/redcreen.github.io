#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭库存查询 - 正确显示中文
"""

import hashlib
import json
import time
import requests

class JushuitanAPI:
    """聚水潭开放平台API封装"""
    
    BASE_URL = "https://openapi.jushuitan.com"
    
    def __init__(self, app_key, app_secret, access_token=None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
    
    def _generate_sign(self, params):
        """生成API签名"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        sign_str = self.app_secret
        for key, value in sorted_params:
            if key == 'sign':
                continue
            if value is not None and value != '':
                sign_str += "%s%s" % (key, value)
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
    
    def _build_params(self, biz_content=None):
        """构建请求参数"""
        timestamp = int(time.time())
        params = {
            'app_key': self.app_key,
            'timestamp': str(timestamp),
            'charset': 'utf-8',
            'version': '2',
        }
        
        if self.access_token:
            params['access_token'] = self.access_token
        
        if biz_content:
            params['biz'] = json.dumps(biz_content, separators=(',', ':'), ensure_ascii=False)
        
        params['sign'] = self._generate_sign(params)
        return params
    
    def get_inventory(self, **kwargs):
        """查询库存"""
        biz_content = {
            'page_index': kwargs.get('page_index', 1),
            'page_size': kwargs.get('page_size', 30),
        }
        
        if 'sku_ids' in kwargs:
            biz_content['sku_ids'] = kwargs['sku_ids']
        if 'wms_co_id' in kwargs:
            biz_content['wms_co_id'] = kwargs['wms_co_id']
        
        url = "%s/open/inventory/query" % self.BASE_URL
        params = self._build_params(biz_content)
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        
        try:
            response = requests.post(url, data=params, headers=headers, timeout=30)
            # 确保使用UTF-8解码
            response.encoding = 'utf-8'
            return response.json()
        except Exception as e:
            print(f"[错误] {str(e)}")
            return {'code': -1, 'msg': str(e)}


if __name__ == '__main__':
    APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
    APP_SECRET = "baf7b719d2464309bd164753b561cda2"
    ACCESS_TOKEN = "47b3c16c04ab41d7ad05952653133d2d"
    
    print("="*60)
    print("聚水潭库存查询")
    print("="*60)
    
    client = JushuitanAPI(APP_KEY, APP_SECRET, ACCESS_TOKEN)
    
    # 查询SKU
    result = client.get_inventory(
        sku_ids="NH500-1",
        page_index=1,
        page_size=10,
        wms_co_id=0
    )
    
    if result.get('code') == 0:
        data = result.get('data', {})
        inventorys = data.get('inventorys', [])
        
        print(f"\n找到 {len(inventorys)} 条库存记录\n")
        
        for i, inv in enumerate(inventorys, 1):
            print(f"[{i}] SKU: {inv.get('sku_id')}")
            print(f"    款式编码: {inv.get('i_id')}")
            print(f"    名称: {inv.get('name')}")
            print(f"    实际库存: {inv.get('qty', 0)}")
            print(f"    订单占用: {inv.get('order_lock', 0)}")
            print(f"    仓库锁定: {inv.get('pick_lock', 0)}")
            print(f"    虚拟库存: {inv.get('virtual_qty', 0)}")
            print(f"    采购在途: {inv.get('purchase_qty', 0)}")
            print(f"    可用库存: {inv.get('qty', 0) - inv.get('order_lock', 0)}")
            print(f"    修改时间: {inv.get('modified')}")
    else:
        print(f"查询失败: {result.get('msg')}")
