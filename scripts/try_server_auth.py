#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭开放平台 - 商家后台获取 Token
如果商家已经登录后台，可以尝试直接获取
"""
import hashlib
import time
import json
import requests

APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
APP_SECRET = "baf7b719d2464309bd164753b561cda2"

def generate_sign(params, app_secret):
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = app_secret
    for key, value in sorted_params:
        if key == 'sign':
            continue
        if value is not None and value != '':
            sign_str += "%s%s" % (key, value)
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()

def check_token_valid(token):
    """检查 token 是否有效"""
    timestamp = int(time.time())
    params = {
        'app_key': APP_KEY,
        'access_token': token,
        'timestamp': str(timestamp),
        'charset': 'utf-8'
    }
    params['sign'] = generate_sign(params, APP_SECRET)
    
    # 用一个简单的接口测试 token
    url = "https://openapi.jushuitan.com/open/jushuitan/inventory/query"
    try:
        resp = requests.post(url, data=params, timeout=10)
        data = resp.json()
        if data.get('code') == 190:
            return False, "Token 已过期"
        elif data.get('code') == 0:
            return True, "Token 有效"
        else:
            return False, f"错误: {data}"
    except Exception as e:
        return False, str(e)

def try_server_side_auth():
    """
    尝试服务端授权方式
    某些平台支持用 app_secret 直接获取 token（商家模式）
    """
    timestamp = int(time.time())
    params = {
        'app_key': APP_KEY,
        'timestamp': str(timestamp),
        'charset': 'utf-8',
        'grant_type': 'client_credentials',  # 客户端模式
        'scope': 'all'
    }
    params['sign'] = generate_sign(params, APP_SECRET)
    
    url = "https://openapi.jushuitan.com/openWeb/auth/accessToken"
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
    
    print("尝试客户端模式获取 token...")
    print(f"URL: {url}")
    print(f"参数: {params}")
    print()
    
    try:
        resp = requests.post(url, data=params, headers=headers, timeout=30)
        resp.encoding = 'utf-8'
        result = resp.json()
        print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result
    except Exception as e:
        print(f"请求失败: {e}")
        return None

if __name__ == "__main__":
    # 先检查现有 token
    current_token = "47b3c16c04ab41d7ad05952653133d2d"
    print(f"检查现有 token: {current_token}")
    valid, msg = check_token_valid(current_token)
    print(f"结果: {msg}")
    print()
    
    if not valid:
        print("Token 无效，尝试客户端模式获取...")
        print("-" * 50)
        result = try_server_side_auth()
        
        if result and result.get('code') == 0:
            data = result.get('data', {})
            print(f"\n✅ 获取成功!")
            print(f"access_token: {data.get('access_token')}")
            print(f"refresh_token: {data.get('refresh_token')}")
            print(f"expires_in: {data.get('expires_in')}")
