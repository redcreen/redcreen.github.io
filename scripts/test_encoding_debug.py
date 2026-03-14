#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭库存查询 - 调试编码问题
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
    
    def get_inventory_raw(self, **kwargs):
        """查询库存 - 返回原始响应"""
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
        
        print(f"\n{'='*60}")
        print(f"[请求] URL: {url}")
        
        try:
            response = requests.post(url, data=params, headers=headers, timeout=30)
            print(f"[响应] 状态码: {response.status_code}")
            print(f"[响应] Content-Type: {response.headers.get('content-type')}")
            print(f"[响应] 编码: {response.encoding}")
            
            # 打印原始字节
            raw_bytes = response.content
            print(f"\n[调试] 原始响应字节 (前500字节):")
            print(raw_bytes[:500])
            
            # 尝试不同编码解码
            print(f"\n[调试] 尝试UTF-8解码:")
            try:
                utf8_text = raw_bytes.decode('utf-8')
                print(utf8_text[:500])
            except Exception as e:
                print(f"UTF-8解码失败: {e}")
            
            print(f"\n[调试] 尝试GBK解码:")
            try:
                gbk_text = raw_bytes.decode('gbk')
                print(gbk_text[:500])
            except Exception as e:
                print(f"GBK解码失败: {e}")
            
            # 使用response.json()解析
            result = response.json()
            return result
            
        except Exception as e:
            print(f"[错误] {str(e)}")
            return {'code': -1, 'msg': str(e)}


if __name__ == '__main__':
    APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
    APP_SECRET = "baf7b719d2464309bd164753b561cda2"
    ACCESS_TOKEN = "47b3c16c04ab41d7ad05952653133d2d"
    
    print("="*60)
    print("聚水潭库存查询 - 编码调试")
    print("="*60)
    
    client = JushuitanAPI(APP_KEY, APP_SECRET, ACCESS_TOKEN)
    
    result = client.get_inventory_raw(
        sku_ids="NH500-1",
        page_index=1,
        page_size=10,
        wms_co_id=0
    )
    
    print("\n" + "="*60)
    print("解析后的结果:")
    print("="*60)
    
    if result.get('code') == 0:
        data = result.get('data', {})
        inventorys = data.get('inventorys', [])
        
        for inv in inventorys:
            print(f"\nSKU: {inv.get('sku_id')}")
            print(f"名称 (直接获取): {inv.get('name')}")
            print(f"名称 (repr): {repr(inv.get('name'))}")
            
            # 检查是否是编码问题
            name = inv.get('name', '')
            if name:
                print(f"\n名称字节分析:")
                try:
                    # 如果是UTF-8字节被错误解码为Latin-1
                    name_bytes = name.encode('latin-1')
                    print(f"  Latin-1编码后的字节: {name_bytes[:50]}")
                    corrected = name_bytes.decode('utf-8')
                    print(f"  重新UTF-8解码: {corrected}")
                except Exception as e:
                    print(f"  转换失败: {e}")
