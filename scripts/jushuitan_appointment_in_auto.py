#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭预约入库接口 - 带自动 Token 刷新

特性：
- 自动从配置文件读取 token
- token 过期前12小时自动刷新
- 刷新失败时自动获取新 token
- 所有 token 操作自动完成，无需人工干预
"""

import hashlib
import json
import time
import random
import string
import requests
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'memory', 'jushuitan_config.json')

# API 配置
APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
APP_SECRET = "baf7b719d2464309bd164753b561cda2"
BASE_URL = "https://openapi.jushuitan.com"


class TokenManager:
    """Token 管理器 - 自动刷新机制"""
    
    # 提前12小时刷新（聚水潭文档要求）
    REFRESH_BEFORE_SECONDS = 12 * 3600
    
    @staticmethod
    def load_config():
        """加载配置"""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save_config(config):
        """保存配置"""
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def generate_sign(params):
        """生成签名"""
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        sign_str = APP_SECRET
        for key, value in sorted_params:
            if key == 'sign':
                continue
            if value is not None and value != '':
                sign_str += "%s%s" % (key, value)
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
    
    @classmethod
    def get_new_token(cls):
        """获取全新 token"""
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        timestamp = int(time.time())
        params = {
            'app_key': APP_KEY,
            'timestamp': str(timestamp),
            'charset': 'utf-8',
            'grant_type': 'authorization_code',
            'code': code
        }
        params['sign'] = cls.generate_sign(params)
        
        url = f"{BASE_URL}/openWeb/auth/getInitToken"
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
        
        try:
            response = requests.post(url, data=params, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            result = response.json()
            
            if result.get('code') == 0:
                data = result.get('data', {})
                config = cls.load_config()
                config.update({
                    'app_key': APP_KEY,
                    'app_secret': APP_SECRET,
                    'access_token': data.get('access_token'),
                    'refresh_token': data.get('refresh_token'),
                    'token_expires_at': (datetime.now() + timedelta(seconds=data.get('expires_in', 2592000))).isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                cls.save_config(config)
                print(f"[TokenManager] New token obtained, expires in {data.get('expires_in', 0)/86400:.1f} days")
                return data.get('access_token')
            else:
                print(f"[TokenManager] Failed to get new token: {result}")
                return None
        except Exception as e:
            print(f"[TokenManager] Error getting new token: {e}")
            return None
    
    @classmethod
    def refresh_token(cls, refresh_token):
        """刷新 token"""
        timestamp = int(time.time())
        params = {
            'app_key': APP_KEY,
            'timestamp': str(timestamp),
            'charset': 'utf-8',
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        params['sign'] = cls.generate_sign(params)
        
        url = f"{BASE_URL}/openWeb/auth/getInitToken"
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
        
        try:
            response = requests.post(url, data=params, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            result = response.json()
            
            if result.get('code') == 0:
                data = result.get('data', {})
                config = cls.load_config()
                config.update({
                    'access_token': data.get('access_token'),
                    'refresh_token': data.get('refresh_token'),
                    'token_expires_at': (datetime.now() + timedelta(seconds=data.get('expires_in', 2592000))).isoformat(),
                    'updated_at': datetime.now().isoformat()
                })
                cls.save_config(config)
                print(f"[TokenManager] Token refreshed, expires in {data.get('expires_in', 0)/86400:.1f} days")
                return data.get('access_token')
            else:
                print(f"[TokenManager] Failed to refresh token: {result}")
                return None
        except Exception as e:
            print(f"[TokenManager] Error refreshing token: {e}")
            return None
    
    @classmethod
    def get_valid_token(cls):
        """
        获取有效 token
        - 如果 token 有效且未接近过期，直接返回
        - 如果 token 接近过期（12小时内），自动刷新
        - 如果刷新失败或没有 token，获取新 token
        """
        config = cls.load_config()
        access_token = config.get('access_token')
        refresh_token = config.get('refresh_token')
        expires_at_str = config.get('token_expires_at')
        
        # 没有 token，获取新的
        if not access_token:
            print("[TokenManager] No token found, getting new token...")
            return cls.get_new_token()
        
        # 解析过期时间
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            now = datetime.now()
            time_until_expire = (expires_at - now).total_seconds()
            
            # Token 还有效且不需要刷新
            if time_until_expire > cls.REFRESH_BEFORE_SECONDS:
                print(f"[TokenManager] Token valid, expires in {time_until_expire/3600:.1f} hours")
                return access_token
            
            # Token 即将过期，尝试刷新
            if refresh_token and time_until_expire > 0:
                print(f"[TokenManager] Token expires in {time_until_expire/3600:.1f} hours, refreshing...")
                new_token = cls.refresh_token(refresh_token)
                if new_token:
                    return new_token
            
            # 刷新失败或 token 已过期，获取新 token
            print("[TokenManager] Getting new token...")
            return cls.get_new_token()
            
        except Exception as e:
            print(f"[TokenManager] Error checking token: {e}")
            return cls.get_new_token()


class JushuitanAppointmentIn:
    """聚水潭预约入库接口封装 - 自动 Token 管理"""
    
    API_PATH = "/open/jushuitan/appointmentin/upload"
    
    def __init__(self):
        """初始化 - 自动获取有效 token"""
        self.app_key = APP_KEY
        self.app_secret = APP_SECRET
        # 自动获取有效 token（会自动刷新）
        self.access_token = TokenManager.get_valid_token()
    
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
        external_id: str,
        plan_arrive_date: str,
        items: List[Dict],
        po_id: str = None,
        supplier_id: int = None,
        remark: str = "",
        send_address: str = "",
        item_type: str = "",
        labels: str = "",
        is_confirm: bool = False,
        shipment_info: Dict = None
    ) -> Dict:
        """
        预约入库上传
        
        支持两种模式：
        1. 采购预约入库（带采购单）：传 po_id，不传 supplier_id
        2. 无采购预约入库（不带采购单）：不传 po_id，必须传 supplier_id
        
        Args:
            wms_co_id: 仓库编号 (必填)
            external_id: 外部单号 (必填)
            plan_arrive_date: 预约到货日期 (必填), 格式: YYYY-MM-DD HH:MM:SS
            items: 商品明细列表, 每个item包含: sku_id(商品编码), qty(数量)
            po_id: 采购单号 (可选) - 采购预约入库时必填
            supplier_id: 供应商编号 (可选) - 无采购预约入库时必填
            remark: 备注 (可选)
            send_address: 送货地址 (可选)
            item_type: 商品类型 (可选) - 可选值: 成品, 半成品, 原材料
            labels: 标签 (可选) - 多个用逗号分隔
            is_confirm: 是否自动确认 (可选) - 默认False
            shipment_info: 发货信息 (可选) - 用于自动生成备注，包含:
                - supplier_name: 供应商名称
                - ship_date: 发货日期
                - ship_from: 发货地
                - ship_to: 收货地/收货人
                - packages: 包数
                - total_qty: 总数量
                - item_details: 商品明细列表，每个包含 sku_id, sku_name, qty
        
        Returns:
            API返回结果
        """
        # 构建业务参数
        biz_content = {
            'wms_co_id': wms_co_id,
            'external_id': external_id,
            'plan_arrive_date': plan_arrive_date,
            'items': items
        }
        
        if po_id:
            # 采购预约入库：传 po_ids 数组
            biz_content['po_ids'] = [po_id]
        elif supplier_id:
            # 无采购预约入库：必须传 supplier_id，系统会自动创建采购单
            biz_content['supplier_id'] = supplier_id
        
        # 处理备注：如果有 shipment_info，自动生成详细备注
        final_remark = remark
        if shipment_info:
            auto_remark = self._build_shipment_remark(shipment_info)
            if remark:
                final_remark = f"{remark}\n{auto_remark}"
            else:
                final_remark = auto_remark
        
        if final_remark:
            biz_content['remark'] = final_remark
        
        if send_address:
            biz_content['send_address'] = send_address
        
        if item_type:
            biz_content['item_type'] = item_type
        
        if labels:
            biz_content['labels'] = labels
        
        if is_confirm:
            biz_content['is_confirm'] = is_confirm
        
        # 构建请求参数
        params = self._build_params(biz_content)
        
        # 发送请求
        url = f"{BASE_URL}{self.API_PATH}"
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
                'msg': f'Request error: {str(e)}'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'code': -1,
                'msg': f'JSON parse error: {str(e)}'
            }
    
    def _build_shipment_remark(self, shipment_info: Dict) -> str:
        """
        根据发货信息构建备注
        
        格式示例：
        张时成 3月13号，潢川发义乌刘总小马 共计3包（1737个）
        黄色回头马NH500-3（643个）
        红色回头马NH500-1（725个）
        绿色回头马NH500-4（326个）
        彩色正马NH500-6（43个）
        
        Args:
            shipment_info: 发货信息字典
        
        Returns:
            格式化后的备注字符串
        """
        lines = []
        
        # 第一行：供应商 日期，发货地 收货地 包数/总数
        header_parts = []
        
        if shipment_info.get('supplier_name'):
            header_parts.append(shipment_info['supplier_name'])
        
        if shipment_info.get('ship_date'):
            header_parts.append(shipment_info['ship_date'])
        
        route_parts = []
        if shipment_info.get('ship_from'):
            route_parts.append(shipment_info['ship_from'])
        if shipment_info.get('ship_to'):
            route_parts.append(shipment_info['ship_to'])
        
        if route_parts:
            header_parts.append('发'.join(route_parts))
        
        # 包数和总数
        package_info = []
        if shipment_info.get('packages'):
            package_info.append(f"共计{shipment_info['packages']}包")
        if shipment_info.get('total_qty'):
            package_info.append(f"（{shipment_info['total_qty']}个）")
        
        if package_info:
            header_parts.append(''.join(package_info))
        
        if header_parts:
            lines.append('，'.join(header_parts))
        
        # 商品明细
        item_details = shipment_info.get('item_details', [])
        for item in item_details:
            sku_name = item.get('sku_name', '')
            sku_id = item.get('sku_id', '')
            qty = item.get('qty', 0)
            
            if sku_name and sku_id:
                lines.append(f"{sku_name}{sku_id}（{qty}个）")
            elif sku_id:
                lines.append(f"{sku_id}（{qty}个）")
        
        return '\n'.join(lines)


# ============ 查询功能 ============

class JushuitanQuery:
    """聚水潭查询接口封装"""
    
    def __init__(self):
        self.app_key = APP_KEY
        self.app_secret = APP_SECRET
        self.access_token = TokenManager.get_valid_token()
    
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
    
    def _post(self, path: str, biz_content: Dict) -> Dict:
        """发送POST请求"""
        params = self._build_params(biz_content)
        url = f"{BASE_URL}{path}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
        
        try:
            response = requests.post(url, data=params, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            return response.json()
        except Exception as e:
            return {'code': -1, 'msg': str(e)}
    
    def query_suppliers(self, name: str = None, page_size: int = 50) -> List[Dict]:
        """
        查询供应商列表
        
        Args:
            name: 供应商名称（模糊匹配）
            page_size: 每页条数
        
        Returns:
            供应商列表，每个包含: supplier_id, name, supplier_code 等
        """
        all_suppliers = []
        page_index = 1
        
        while True:
            biz_content = {
                'page_index': page_index,
                'page_size': page_size
            }
            
            if name:
                biz_content['names'] = name
            
            result = self._post('/open/supplier/query', biz_content)
            
            if result.get('code') != 0:
                break
            
            data = result.get('data') or {}
            suppliers = data.get('datas') or []
            
            for s in suppliers:
                all_suppliers.append({
                    'supplier_id': s.get('supplier_id'),
                    'name': s.get('name', ''),
                    'supplier_code': s.get('supplier_code', ''),
                    'group': s.get('group', ''),
                    'enabled': s.get('enabled', True)
                })
            
            if not data.get('has_next', False):
                break
            page_index += 1
            if page_index > 10:
                break
        
        return all_suppliers
    
    def find_supplier_by_name(self, name: str) -> Optional[Dict]:
        """
        根据名称查找供应商（精确匹配）
        
        Args:
            name: 供应商名称
        
        Returns:
            供应商信息，未找到返回 None
        """
        suppliers = self.query_suppliers()
        for s in suppliers:
            if name in s.get('name', ''):
                return s
        return None
    
    def query_purchases(
        self,
        supplier_id: int = None,
        begin_time: datetime = None,
        end_time: datetime = None,
        status: str = None,
        page_size: int = 50,
        max_pages: int = 10
    ) -> List[Dict]:
        """
        查询采购单列表（支持分页，自动处理7天时间限制）
        
        注意：
        1. 聚水潭API限制时间间隔不能超过7天，本函数会自动分段查询
        2. 采购单查询接口不支持 supplier_id 参数，需要在返回结果中过滤
        
        Args:
            supplier_id: 供应商ID（查询后按此过滤）
            begin_time: 开始时间（修改时间）
            end_time: 结束时间（修改时间）
            status: 状态筛选
            page_size: 每页条数
            max_pages: 每时间段最大查询页数
        
        Returns:
            采购单列表
        """
        all_purchases = []
        
        # 默认查2年
        if end_time is None:
            end_time = datetime.now()
        if begin_time is None:
            begin_time = end_time - timedelta(days=730)
        
        # 聚水潭限制：时间间隔不能超过7天
        # 需要分段查询
        current_end = end_time
        
        while current_end > begin_time:
            # 计算当前段的开始时间（最多7天前）
            current_begin = max(
                begin_time,
                current_end - timedelta(days=7)
            )
            
            # 查询当前时间段
            page_index = 1
            while page_index <= max_pages:
                biz_content = {
                    'page_index': page_index,
                    'page_size': page_size,
                    'modified_begin': current_begin.strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_end': current_end.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # 注意：采购单查询接口不支持 supplier_id 参数
                # 如果传了 status，可以加上
                if status:
                    biz_content['status'] = status
                
                result = self._post('/open/purchase/query', biz_content)
                
                if result.get('code') != 0:
                    # 如果是时间范围错误，跳过
                    msg = result.get('msg', '')
                    if '7天' in msg or '时间' in msg:
                        break
                    # 其他错误也跳过
                    break
                
                data = result.get('data') or {}
                purchases = data.get('datas') or []
                
                for po in purchases:
                    po_supplier_id = po.get('supplier_id')
                    
                    # 如果指定了供应商ID，只保留匹配的
                    if supplier_id and po_supplier_id != supplier_id:
                        continue
                    
                    # 去重检查
                    po_id = po.get('po_id')
                    if not any(p['po_id'] == po_id for p in all_purchases):
                        all_purchases.append({
                            'po_id': po_id,
                            'status': po.get('status'),
                            'po_date': po.get('po_date'),
                            'supplier_id': po_supplier_id,
                            'supplier_name': po.get('supplier_name', ''),
                            'remark': po.get('remark', ''),
                            'items': po.get('items', [])
                        })
                
                # 检查是否还有更多页
                has_next = data.get('has_next', False)
                if not has_next or not purchases:
                    break
                
                page_index += 1
            
            # 移动到下一个时间段
            current_end = current_begin
        
        return all_purchases
    
    def find_purchases_with_sku(
        self,
        supplier_id: int,
        sku_id: str,
        begin_time: datetime = None,
        end_time: datetime = None
    ) -> List[Dict]:
        """
        查找包含指定SKU的采购单
        
        Args:
            supplier_id: 供应商ID
            sku_id: 商品SKU
            begin_time: 开始时间
            end_time: 结束时间
        
        Returns:
            包含该SKU的采购单列表
        """
        purchases = self.query_purchases(supplier_id, begin_time, end_time)
        result = []
        
        for po in purchases:
            items = po.get('items', [])
            for item in items:
                if item.get('sku_id') == sku_id:
                    result.append(po)
                    break
        
        return result
    
    def query_warehouses(self, page_size: int = 50) -> List[Dict]:
        """
        查询仓库列表
        
        Returns:
            仓库列表，每个包含: wms_co_id, name, co_id, is_main, status
        """
        all_warehouses = []
        page_index = 1
        
        while True:
            biz_content = {
                'page_index': page_index,
                'page_size': page_size
            }
            
            result = self._post('/open/wms/partner/query', biz_content)
            
            if result.get('code') != 0:
                break
            
            data = result.get('data') or {}
            warehouses = data.get('datas') or []
            
            for w in warehouses:
                all_warehouses.append({
                    'wms_co_id': w.get('wms_co_id'),
                    'name': w.get('name', ''),
                    'co_id': w.get('co_id'),
                    'is_main': w.get('is_main', False),
                    'status': w.get('status', ''),
                    'remark1': w.get('remark1', ''),
                    'remark2': w.get('remark2', '')
                })
            
            if not data.get('has_next', False):
                break
            page_index += 1
            if page_index > 10:
                break
        
        return all_warehouses


# ============ 便捷函数 ============

def create_appointment_in(
    wms_co_id: int,
    external_id: str,
    plan_arrive_date: str,
    items: List[Dict],
    po_id: str = None,
    supplier_id: int = None,
    remark: str = "",
    send_address: str = "",
    item_type: str = "",
    labels: str = "",
    is_confirm: bool = False
) -> Dict:
    """
    快速创建预约入库单
    
    支持两种模式：
    1. 采购预约入库（带采购单）：传 po_id，不传 supplier_id
       例: create_appointment_in(..., po_id="207206")
    
    2. 无采购预约入库（不带采购单）：不传 po_id，必须传 supplier_id
       例: create_appointment_in(..., supplier_id=31801969)
       系统会自动创建采购单，返回的 data.po_id 就是系统生成的采购单号
    
    自动处理 token，无需关心 token 过期问题
    """
    client = JushuitanAppointmentIn()
    return client.upload_appointment(
        wms_co_id=wms_co_id,
        external_id=external_id,
        plan_arrive_date=plan_arrive_date,
        items=items,
        po_id=po_id,
        supplier_id=supplier_id,
        remark=remark,
        send_address=send_address,
        item_type=item_type,
        labels=labels,
        is_confirm=is_confirm
    )


def create_appointment_smart(
    wms_co_id: int,
    supplier_name: str,
    sku_list: List[str],
    external_id: str = None,
    plan_arrive_date: str = None,
    qty_map: Dict[str, int] = None,
    remark: str = ""
) -> Dict:
    """
    智能创建预约入库单
    
    自动流程：
    1. 根据供应商名称查找供应商ID
    2. 查找包含指定SKU的采购单
    3. 使用找到的采购单创建预约入库
    
    Args:
        wms_co_id: 仓库编号
        supplier_name: 供应商名称（如"江西王升水"）
        sku_list: 要入库的SKU列表（如["NH500-1", "NH500-2"]）
        external_id: 外部单号（可选，默认自动生成）
        plan_arrive_date: 预约到货时间（可选，默认明天）
        qty_map: SKU数量映射（可选，默认每个SKU入库100个）
        remark: 备注
    
    Returns:
        {
            'success': True/False,
            'po_id': 使用的采购单号,
            'supplier_id': 供应商ID,
            'appointment_result': 预约入库结果
        }
    """
    # 默认值
    if external_id is None:
        external_id = f"APPOINT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if plan_arrive_date is None:
        tomorrow = datetime.now() + timedelta(days=1)
        plan_arrive_date = tomorrow.strftime('%Y-%m-%d 14:00:00')
    
    if qty_map is None:
        qty_map = {sku: 100 for sku in sku_list}
    
    # 1. 查找供应商
    print(f"[Smart] 查找供应商: {supplier_name}")
    query = JushuitanQuery()
    supplier = query.find_supplier_by_name(supplier_name)
    
    if not supplier:
        return {
            'success': False,
            'error': f'未找到供应商: {supplier_name}'
        }
    
    supplier_id = supplier['supplier_id']
    print(f"[Smart] 找到供应商: {supplier['name']} (ID: {supplier_id})")
    
    # 2. 查找包含SKU的采购单
    print(f"[Smart] 查找包含SKU {sku_list} 的采购单...")
    all_purchases = []
    for sku in sku_list:
        purchases = query.find_purchases_with_sku(supplier_id, sku)
        all_purchases.extend(purchases)
    
    # 去重
    seen_po_ids = set()
    unique_purchases = []
    for po in all_purchases:
        po_id = po['po_id']
        if po_id not in seen_po_ids:
            seen_po_ids.add(po_id)
            unique_purchases.append(po)
    
    if not unique_purchases:
        return {
            'success': False,
            'supplier_id': supplier_id,
            'error': f'未找到包含SKU {sku_list} 的采购单'
        }
    
    # 选择最新的采购单
    unique_purchases.sort(key=lambda x: x.get('po_date', ''), reverse=True)
    selected_po = unique_purchases[0]
    po_id = selected_po['po_id']
    
    print(f"[Smart] 使用采购单: {po_id} (日期: {selected_po.get('po_date')})")
    
    # 3. 构建items
    items = []
    for sku in sku_list:
        qty = qty_map.get(sku, 100)
        items.append({'sku_id': sku, 'qty': qty})
    
    # 4. 创建预约入库
    print(f"[Smart] 创建预约入库...")
    result = create_appointment_in(
        wms_co_id=wms_co_id,
        external_id=external_id,
        plan_arrive_date=plan_arrive_date,
        items=items,
        po_id=po_id,
        remark=remark
    )
    
    return {
        'success': result.get('success', False),
        'po_id': po_id,
        'supplier_id': supplier_id,
        'supplier_name': supplier['name'],
        'appointment_result': result
    }


# ============ 命令行测试 ============
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("Jushuitan Appointment In - Auto Token Refresh")
        print()
        print("Usage:")
        print("  from scripts.jushuitan_appointment_in_auto import create_appointment_in, create_appointment_smart, JushuitanQuery")
        print()
        print("  # 方式1: 直接创建（需知道po_id或supplier_id）")
        print("  result = create_appointment_in(")
        print("      wms_co_id=13440882,")
        print("      po_id='207206',")  # 或 supplier_id=31842672
        print("      external_id='EXT001',")
        print("      plan_arrive_date='2026-03-15 10:00:00',")
        print("      items=[")
        print("          {'sku_id': 'NH500-1', 'qty': 100},")
        print("          {'sku_id': 'NH500-2', 'qty': 50}")
        print("      ],")
        print("      remark='Test appointment'")
        print("  )")
        print()
        print("  # 方式2: 智能创建（自动查找供应商和采购单）")
        print("  result = create_appointment_smart(")
        print("      wms_co_id=13440882,")
        print("      supplier_name='江西王升水',")
        print("      sku_list=['NH500-1', 'NH500-2'],")
        print("      qty_map={'NH500-1': 80, 'NH500-2': 30}")
        print("  )")
        print()
        print("  # 查询功能")
        print("  query = JushuitanQuery()")
        print("  suppliers = query.query_suppliers()  # 查所有供应商")
        print("  purchases = query.query_purchases(supplier_id=31842672)  # 查采购单")
        print("  warehouses = query.query_warehouses()  # 查仓库")
        sys.exit(0)
    
    # 测试智能创建
    print("="*60)
    print("测试智能创建预约入库")
    print("="*60)
    
    result = create_appointment_smart(
        wms_co_id=13440882,
        supplier_name='江西王升水',
        sku_list=['NH500-1', 'NH500-2'],
        qty_map={'NH500-1': 80, 'NH500-2': 30},
        remark='智能创建测试'
    )
    
    print("\n结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
