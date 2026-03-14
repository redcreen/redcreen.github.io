# -*- coding: utf-8 -*-
"""
聚水潭仓库列表查询 - 使用 /open/wms/partner/query
"""

import hashlib
import json
import time
import requests

class JushuitanAPI:
    BASE_URL = "https://openapi.jushuitan.com"
    
    def __init__(self, app_key, app_secret, access_token=None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
    
    def _generate_sign(self, params):
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        sign_str = self.app_secret
        for key, value in sorted_params:
            if key == 'sign':
                continue
            if value is not None and value != '':
                sign_str += "%s%s" % (key, value)
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
    
    def _build_params(self, biz_content=None):
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
    
    def get_warehouses(self):
        """查询仓库列表 - 使用 /open/wms/partner/query"""
        url = "%s/open/wms/partner/query" % self.BASE_URL
        # 添加分页参数
        biz = {
            'page_index': 1,
            'page_size': 100
        }
        params = self._build_params(biz)
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
        
        try:
            response = requests.post(url, data=params, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            return response.json()
        except Exception as e:
            return {'code': -1, 'msg': str(e)}


if __name__ == '__main__':
    APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
    APP_SECRET = "baf7b719d2464309bd164753b561cda2"
    ACCESS_TOKEN = "47b3c16c04ab41d7ad05952653133d2d"
    
    client = JushuitanAPI(APP_KEY, APP_SECRET, ACCESS_TOKEN)
    
    result = client.get_warehouses()
    
    if result.get('code') == 0:
        data = result.get('data', {})
        warehouses = data.get('datas', [])
        
        with open('warehouse_list.txt', 'w', encoding='utf-8') as f:
            f.write(f"找到 {len(warehouses)} 个仓库\n\n")
            
            for i, wh in enumerate(warehouses, 1):
                f.write(f"[{i}] 仓库编号 (wms_co_id): {wh.get('wms_co_id')}\n")
                f.write(f"    仓库名称: {wh.get('name')}\n")
                f.write(f"    仓库类型: {wh.get('type')}\n")
                f.write(f"    状态: {wh.get('status')}\n")
                f.write(f"    地址: {wh.get('address') or 'N/A'}\n\n")
        
        print("仓库列表已写入 warehouse_list.txt")
    else:
        print(f"查询失败: {result.get('msg')}")
        # 保存完整响应用于调试
        with open('warehouse_error.txt', 'w', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False, indent=2))
        print("错误详情已写入 warehouse_error.txt")
