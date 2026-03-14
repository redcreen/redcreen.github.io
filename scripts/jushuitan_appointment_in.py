#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭预约入库接口对接
接口文档: https://openweb.jushuitan.com/dev-doc?docType=7&docId=92
"""

import hashlib
import json
import time
import requests
from typing import List, Dict, Optional
from datetime import datetime

class JushuitanAppointmentIn:
    """聚水潭预约入库接口封装"""
    
    # API配置
    BASE_URL = "https://openapi.jushuitan.com"
    API_PATH = "/open/jushuitan/appointmentin/upload"
    
    def __init__(self, app_key: str, app_secret: str, access_token: str):
        """
        初始化
        
        Args:
            app_key: 应用app_key
            app_secret: 应用app_secret
            access_token: 访问令牌
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token
    
    def _generate_sign(self, params: Dict) -> str:
        """生成API签名"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        sign_str = self.app_secret
        for key, value in sorted_params:
            if key == 'sign':
                continue
            if value is not None and value != '':
                sign_str += "%s%s" % (key, value)
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
    
    def _build_params(self, biz_content: Dict = None) -> Dict:
        """构建请求参数"""
        timestamp = int(time.time())
        params = {
            'app_key': self.app_key,
            'timestamp': str(timestamp),
            'charset': 'utf-8',
            'version': '2',
            'access_token': self.access_token,
        }
        if biz_content:
            params['biz'] = json.dumps(biz_content, separators=(',', ':'), ensure_ascii=False)
        params['sign'] = self._generate_sign(params)
        return params
    
    def upload_appointment(
        self,
        wms_co_id: int,
        po_id: str,
        external_id: str,
        plan_arrive_date: str,
        items: List[Dict],
        remark: str = ""
    ) -> Dict:
        """
        预约入库上传
        
        Args:
            wms_co_id: 仓库编号 (必填)
            po_id: 采购单号 (必填)
            external_id: 外部单号 (必填)
            plan_arrive_date: 预约到货日期 (必填), 格式: YYYY-MM-DD HH:MM:SS
            items: 商品明细列表, 每个item包含: sku_id(商品编码), qty(数量)
            remark: 备注 (可选)
        
        Returns:
            API返回结果
        
        Example:
            items = [
                {"sku_id": "SKU001", "qty": 100},
                {"sku_id": "SKU002", "qty": 50}
            ]
            result = client.upload_appointment(
                wms_co_id=13440882,
                po_id="PO20240314001",
                external_id="EXT001",
                plan_arrive_date="2026-03-15 10:00:00",
                items=items,
                remark="测试预约入库"
            )
        """
        # 构建业务参数
        biz_content = {
            'wms_co_id': wms_co_id,
            'po_id': po_id,
            'external_id': external_id,
            'plan_arrive_date': plan_arrive_date,
            'items': items
        }
        
        if remark:
            biz_content['remark'] = remark
        
        # 构建请求参数
        params = self._build_params(biz_content)
        
        # 发送请求
        url = f"{self.BASE_URL}{self.API_PATH}"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        
        try:
            response = requests.post(url, data=params, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            result = response.json()
            
            # 格式化返回结果
            if result.get('code') == 0:
                return {
                    'success': True,
                    'code': result.get('code'),
                    'msg': result.get('msg'),
                    'data': result.get('data', {})
                }
            else:
                return {
                    'success': False,
                    'code': result.get('code'),
                    'msg': result.get('msg'),
                    'error': result.get('error', {})
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'code': -1,
                'msg': f'请求异常: {str(e)}'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'code': -1,
                'msg': f'JSON解析失败: {str(e)}'
            }


# ============ 便捷函数 ============

def create_appointment_in(
    wms_co_id: int,
    po_id: str,
    external_id: str,
    plan_arrive_date: str,
    items: List[Dict],
    remark: str = "",
    app_key: str = None,
    app_secret: str = None,
    access_token: str = None
) -> Dict:
    """
    快速创建预约入库单
    
    如果不传凭证参数，会尝试从配置文件读取
    """
    # 从配置文件读取凭证（如果未提供）
    if not all([app_key, app_secret, access_token]):
        try:
            import os
            config_path = os.path.join(os.path.dirname(__file__), '..', 'memory', 'jushuitan_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    app_key = app_key or config.get('app_key')
                    app_secret = app_secret or config.get('app_secret')
                    access_token = access_token or config.get('access_token')
        except Exception as e:
            return {'success': False, 'msg': f'读取配置失败: {e}'}
    
    if not all([app_key, app_secret, access_token]):
        return {'success': False, 'msg': '缺少API凭证，请提供app_key、app_secret和access_token'}
    
    client = JushuitanAppointmentIn(app_key, app_secret, access_token)
    return client.upload_appointment(
        wms_co_id=wms_co_id,
        po_id=po_id,
        external_id=external_id,
        plan_arrive_date=plan_arrive_date,
        items=items,
        remark=remark
    )


# ============ 命令行测试 ============
if __name__ == '__main__':
    import sys
    
    # 配置（实际使用时应该从配置文件读取或作为参数传入）
    APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
    APP_SECRET = "baf7b719d2464309bd164753b561cda2"
    ACCESS_TOKEN = "47b3c16c04ab41d7ad05952653133d2d"
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("用法: python jushuitan_appointment_in.py")
        print("\n示例代码:")
        print("""
from scripts.jushuitan_appointment_in import create_appointment_in

result = create_appointment_in(
    wms_co_id=13440882,
    po_id="PO20240314001",
    external_id="EXT001",
    plan_arrive_date="2026-03-15 10:00:00",
    items=[
        {"sku_id": "NH500-1", "qty": 100},
        {"sku_id": "NH500-2", "qty": 50}
    ],
    remark="测试预约入库"
)
print(result)
        """)
        sys.exit(0)
    
    # 测试示例
    print("=" * 60)
    print("聚水潭预约入库接口测试")
    print("=" * 60)
    
    client = JushuitanAppointmentIn(APP_KEY, APP_SECRET, ACCESS_TOKEN)
    
    # 测试数据
    test_items = [
        {"sku_id": "NH500-1", "qty": 100},
        {"sku_id": "NH500-2", "qty": 50}
    ]
    
    result = client.upload_appointment(
        wms_co_id=13440882,  # 年货传驿云仓
        po_id="PO20240314001",
        external_id="EXT001",
        plan_arrive_date="2026-03-15 10:00:00",
        items=test_items,
        remark="测试预约入库"
    )
    
    print("\n请求结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
