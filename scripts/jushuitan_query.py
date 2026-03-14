#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭库存查询 - 简化调用版
用于直接执行查询命令
"""

import hashlib
import json
import time
import requests
import re
import os
import sys
from typing import List, Dict, Optional, Tuple

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ============ 配置 ============
APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
APP_SECRET = "baf7b719d2464309bd164753b561cda2"
ACCESS_TOKEN = "47b3c16c04ab41d7ad05952653133d2d"
BASE_URL = "https://openapi.jushuitan.com"

# 仓库缓存
_warehouse_cache: List[Dict] = []
_cache_loaded = False


def _generate_sign(params: Dict) -> str:
    """生成API签名"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = APP_SECRET
    for key, value in sorted_params:
        if key == 'sign':
            continue
        if value is not None and value != '':
            sign_str += "%s%s" % (key, value)
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()


def _build_params(biz_content: Dict = None) -> Dict:
    """构建请求参数"""
    timestamp = int(time.time())
    params = {
        'app_key': APP_KEY,
        'timestamp': str(timestamp),
        'charset': 'utf-8',
        'version': '2',
        'access_token': ACCESS_TOKEN,
    }
    if biz_content:
        params['biz'] = json.dumps(biz_content, separators=(',', ':'), ensure_ascii=False)
    params['sign'] = _generate_sign(params)
    return params


def _api_call(endpoint: str, biz_content: Dict = None) -> Dict:
    """调用API"""
    url = f"{BASE_URL}{endpoint}"
    params = _build_params(biz_content)
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
    
    try:
        response = requests.post(url, data=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        return response.json()
    except Exception as e:
        return {'code': -1, 'msg': f'请求异常: {str(e)}'}


def _load_warehouses(force_refresh: bool = False) -> List[Dict]:
    """加载仓库列表"""
    global _warehouse_cache, _cache_loaded
    
    if not force_refresh and _cache_loaded and _warehouse_cache:
        return _warehouse_cache
    
    result = _api_call('/open/wms/partner/query', {
        'page_index': 1,
        'page_size': 100
    })
    
    if result.get('code') == 0:
        data = result.get('data', {})
        _warehouse_cache = data.get('datas', [])
        _cache_loaded = True
    else:
        print(f"[ERROR] 获取仓库列表失败: {result.get('msg')}")
    
    return _warehouse_cache


def find_warehouse(name_pattern: str) -> Tuple[Optional[Dict], List[Dict]]:
    """
    模糊匹配仓库名称
    返回: (最佳匹配, 所有匹配列表)
    """
    warehouses = _load_warehouses()
    if not warehouses:
        return None, []
    
    pattern = name_pattern.lower()
    matches = []
    
    for wh in warehouses:
        wh_name = wh.get('name', '').lower()
        wh_id = str(wh.get('wms_co_id', ''))
        
        if pattern in wh_name or pattern in wh_id:
            matches.append(wh)
    
    if not matches:
        return None, []
    
    if len(matches) == 1:
        return matches[0], matches
    
    # 多个匹配时排序
    matches.sort(key=lambda x: (
        0 if pattern == x.get('name', '').lower() else 1,
        len(x.get('name', ''))
    ))
    
    return matches[0], matches


def query_inventory_by_warehouse(warehouse_name_pattern: str, sku_id: str) -> str:
    """
    查询指定仓库的SKU库存
    
    Args:
        warehouse_name_pattern: 仓库名称（支持模糊匹配）
        sku_id: SKU编码
    
    Returns:
        格式化的查询结果
    """
    # 查找仓库
    best_match, all_matches = find_warehouse(warehouse_name_pattern)
    
    if not best_match:
        warehouses = _load_warehouses()
        wh_list = "\n".join([f"  - {w.get('name')}" for w in warehouses])
        return f"[x] 未找到匹配 '{warehouse_name_pattern}' 的仓库\n\n可用仓库:\n{wh_list}"
    
    if len(all_matches) > 1:
        matches_str = "\n".join([f"  {i+1}. {w.get('name')}" 
                                for i, w in enumerate(all_matches[:5])])
        return f"[!] 找到多个匹配 '{warehouse_name_pattern}' 的仓库:\n{matches_str}\n\n请提供更精确的仓库名称。"
    
    # 执行查询
    warehouse_name = best_match.get('name')
    wms_co_id = best_match.get('wms_co_id')
    
    biz_content = {
        'page_index': 1,
        'page_size': 100,
        'sku_ids': sku_id,
        'wms_co_id': wms_co_id
    }
    
    result = _api_call('/open/inventory/query', biz_content)
    
    # 格式化结果
    if result.get('code') != 0:
        return f"[x] 查询失败: {result.get('msg')}"
    
    data = result.get('data', {})
    inventorys = data.get('inventorys', [])
    
    if not inventorys:
        return f"[库存] SKU: {sku_id}\n[仓库] {warehouse_name}\n[结果] 未找到库存记录"
    
    lines = []
    lines.append(f"[库存] SKU: {sku_id}")
    lines.append(f"[仓库] {warehouse_name}")
    lines.append(f"[详情]")
    
    for inv in inventorys:
        qty = inv.get('qty', 0)
        order_lock = inv.get('order_lock', 0)
        available = qty - order_lock
        
        lines.append(f"  名称: {inv.get('name', 'N/A')}")
        lines.append(f"  实际库存: {qty}")
        lines.append(f"  订单占用: {order_lock}")
        lines.append(f"  可用库存: {available}")
        if inv.get('purchase_qty'):
            lines.append(f"  采购在途: {inv.get('purchase_qty')}")
    
    return "\n".join(lines)


def query_inventory(command: str) -> str:
    """
    解析命令并查询库存
    
    支持的格式:
    - 查下聚水潭里 传驿云仓 NH500-1 的库存
    - 传驿云仓 NH500-1
    """
    # 提取仓库名称和SKU
    patterns = [
        r'(?:查|查询).*?(\S+仓)\s+(\S+).*?(?:库存|多少)',
        r'(?:查|查询).*?(\S+云仓)\s+(\S+).*?(?:库存|多少)',
        r'(?:查|查询).*?(\S+仓库)\s+(\S+).*?(?:库存|多少)',
        r'^(\S+仓)\s+(\S+)$',
        r'^(\S+云仓)\s+(\S+)$',
    ]
    
    warehouse_pattern = None
    sku_id = None
    
    for pattern in patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            warehouse_pattern = match.group(1)
            sku_id = match.group(2)
            break
    
    if not warehouse_pattern or not sku_id:
        return "[x] 无法解析命令。请使用格式:\n   查下聚水潭里 [仓库名] [SKU] 的库存\n\n例如:\n   查下聚水潭里 传驿云仓 NH500-1 的库存"
    
    return query_inventory_by_warehouse(warehouse_pattern, sku_id)


# ============ 直接执行 ============
if __name__ == '__main__':
    if len(sys.argv) >= 3:
        # 命令行参数: python jushuitan_query.py "传驿云仓" "NH500-1"
        warehouse = sys.argv[1]
        sku = sys.argv[2]
        result = query_inventory_by_warehouse(warehouse, sku)
        print(result)
        sys.exit(0)
    elif len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', 'help']:
        print("用法: python jushuitan_query.py <仓库名> <SKU>")
        print("示例: python jushuitan_query.py '年货传驿云仓' 'NH500-1'")
        sys.exit(0)
    else:
        # 交互模式
        print("=" * 50)
        print("聚水潭库存查询")
        print("=" * 50)
        print("格式: [仓库名] [SKU]")
        print("例如: 传驿云仓 NH500-1")
        print("输入 'list' 查看仓库列表")
        print("输入 'quit' 退出")
        print("=" * 50)
        
        while True:
            try:
                cmd = input("\n> ").strip()
                if cmd.lower() in ['quit', 'exit', 'q']:
                    break
                if cmd in ['list', '仓库']:
                    warehouses = _load_warehouses()
                    print(f"\n仓库列表 ({len(warehouses)} 个):")
                    for wh in warehouses:
                        print(f"  - {wh.get('name')}")
                    continue
                if not cmd:
                    continue
                
                result = query_inventory(cmd)
                print("\n" + result)
            except KeyboardInterrupt:
                break
        
        print("\n再见!")
