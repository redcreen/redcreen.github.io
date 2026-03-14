#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭库存查询接口测试 - 使用真实access_token查询SKU: NH500-1
"""

import hashlib
import json
import time
import requests

class JushuitanAPI:
    """聚水潭开放平台API封装"""
    
    # 使用正式环境
    BASE_URL = "https://openapi.jushuitan.com"
    
    def __init__(self, app_key, app_secret, access_token=None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
    
    def _generate_sign(self, params):
        """
        生成API签名 - 业务接口按字母排序
        规则：app_secret + key1value1 + key2value2 + ...
        MD5加密，结果转小写
        """
        # 按字母排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 拼接字符串
        sign_str = self.app_secret
        for key, value in sorted_params:
            if key == 'sign':
                continue
            if value is not None and value != '':
                sign_str += "%s%s" % (key, value)
        
        print(f"[签名调试] 签名字符串: {sign_str}")
        
        # MD5加密，转小写
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
        
        # 添加access_token
        if self.access_token:
            params['access_token'] = self.access_token
        
        # 添加业务参数（注意：业务接口使用'biz'而不是'biz_content'）
        if biz_content:
            params['biz'] = json.dumps(biz_content, separators=(',', ':'), ensure_ascii=False)
        
        # 生成签名
        params['sign'] = self._generate_sign(params)
        return params
    
    def call_api(self, api_path, biz_content=None):
        """调用API接口"""
        url = "%s%s" % (self.BASE_URL, api_path)
        params = self._build_params(biz_content)
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        
        print(f"\n{'='*60}")
        print(f"[请求] URL: {url}")
        print(f"[请求] 参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, data=params, headers=headers, timeout=30)
            print(f"[响应] 状态码: {response.status_code}")
            result = response.json()
            print(f"[响应] 内容: {json.dumps(result, ensure_ascii=False, indent=2)[:2000]}")
            return result
        except Exception as e:
            print(f"[错误] {str(e)}")
            return {'code': -1, 'msg': str(e)}
    
    def get_inventory(self, **kwargs):
        """
        商品库存查询
        
        参数:
        - sku_ids: 商品编码，如 "NH500-1"
        - page_index: 页码，从1开始
        - page_size: 每页数量，默认30，最大100
        - wms_co_id: 仓库编号，0查询所有
        """
        biz_content = {
            'page_index': kwargs.get('page_index', 1),
            'page_size': kwargs.get('page_size', 30),
        }
        
        # 添加可选参数
        if 'sku_ids' in kwargs:
            biz_content['sku_ids'] = kwargs['sku_ids']
        if 'names' in kwargs:
            biz_content['names'] = kwargs['names']
        if 'wms_co_id' in kwargs:
            biz_content['wms_co_id'] = kwargs['wms_co_id']
        if 'modified_begin' in kwargs:
            biz_content['modified_begin'] = kwargs['modified_begin']
        if 'modified_end' in kwargs:
            biz_content['modified_end'] = kwargs['modified_end']
        if 'has_lock_qty' in kwargs:
            biz_content['has_lock_qty'] = kwargs['has_lock_qty']
        
        return self.call_api('/open/inventory/query', biz_content)


if __name__ == '__main__':
    # 配置信息
    APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
    APP_SECRET = "baf7b719d2464309bd164753b561cda2"
    ACCESS_TOKEN = "47b3c16c04ab41d7ad05952653133d2d"
    
    print("="*60)
    print("聚水潭库存查询接口测试")
    print("="*60)
    print(f"AppKey: {APP_KEY}")
    print(f"AccessToken: {ACCESS_TOKEN}")
    print(f"查询SKU: NH500-1")
    print()
    
    # 创建客户端
    client = JushuitanAPI(APP_KEY, APP_SECRET, ACCESS_TOKEN)
    
    # 查询库存
    print(">>> 正在查询库存...")
    result = client.get_inventory(
        sku_ids="NH500-1",
        page_index=1,
        page_size=10,
        wms_co_id=0  # 查询所有仓库
    )
    
    # 处理结果
    print("\n" + "="*60)
    print("查询结果分析:")
    print("="*60)
    
    if result.get('code') == 0:
        data = result.get('data', {})
        inventorys = data.get('inventorys', [])
        
        if inventorys:
            print(f"[OK] 查询成功！找到 {len(inventorys)} 条库存记录")
            print(f"\n分页信息:")
            print(f"  当前页: {data.get('page_index')}")
            print(f"  每页数量: {data.get('page_size')}")
            print(f"  是否有下一页: {data.get('has_next')}")
            
            print(f"\n库存详情:")
            for i, inv in enumerate(inventorys, 1):
                print(f"\n  [{i}] SKU: {inv.get('sku_id')}")
                print(f"      款式编码: {inv.get('i_id')}")
                print(f"      名称: {inv.get('name') or 'N/A'}")
                print(f"      实际库存: {inv.get('qty', 0)}")
                print(f"      订单占用: {inv.get('order_lock', 0)}")
                print(f"      仓库锁定: {inv.get('pick_lock', 0)}")
                print(f"      虚拟库存: {inv.get('virtual_qty', 0)}")
                print(f"      采购在途: {inv.get('purchase_qty', 0)}")
                print(f"      可用库存: {inv.get('qty', 0) - inv.get('order_lock', 0)}")
                print(f"      修改时间: {inv.get('modified')}")
        else:
            print("[WARN] 查询成功，但没有找到库存记录")
            print("   可能原因：SKU不存在或没有库存")
    else:
        print(f"[FAIL] 查询失败")
        print(f"   错误码: {result.get('code')}")
        print(f"   错误信息: {result.get('msg')}")
