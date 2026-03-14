#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚水潭授权工具 - 获取 access_token
流程：
1. 生成授权链接，让商家在浏览器中访问并授权
2. 商家授权后，平台会回调到 redirect_uri，携带 code
3. 用 code 换取 access_token

使用方式：
python scripts/jushuitan_auth.py get_auth_url    # 获取授权链接
python scripts/jushuitan_auth.py get_token CODE  # 用 code 换 token
"""
import sys
import hashlib
import json
import time
import urllib.parse
import requests

# 应用配置
APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
APP_SECRET = "baf7b719d2464309bd164753b561cda2"

# 回调地址（需要先在聚水潭平台配置）
# 这里使用一个简单的本地回调，实际使用时可以配置为服务器地址
REDIRECT_URI = "http://localhost:8080/callback"

def generate_sign(params, app_secret):
    """生成签名"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = app_secret
    for key, value in sorted_params:
        if key == 'sign':
            continue
        if value is not None and value != '':
            sign_str += "%s%s" % (key, value)
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()

def get_auth_url():
    """生成授权链接"""
    timestamp = int(time.time())
    
    params = {
        'app_key': APP_KEY,
        'timestamp': str(timestamp),
        'charset': 'utf-8',
        'redirect_uri': REDIRECT_URI
    }
    
    params['sign'] = generate_sign(params, APP_SECRET)
    
    # 构建授权URL
    base_url = "https://openweb.jushuitan.com/auth/authorize"
    query = urllib.parse.urlencode(params)
    auth_url = f"{base_url}?{query}"
    
    return auth_url

def get_access_token(code):
    """用 code 换取 access_token"""
    timestamp = int(time.time())
    
    params = {
        'app_key': APP_KEY,
        'timestamp': str(timestamp),
        'charset': 'utf-8',
        'grant_type': 'authorization_code',
        'code': code,
        'scope': 'all'
    }
    
    params['sign'] = generate_sign(params, APP_SECRET)
    
    url = "https://openapi.jushuitan.com/openWeb/auth/accessToken"
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
    
    try:
        response = requests.post(url, data=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def refresh_access_token(refresh_token):
    """刷新 access_token"""
    timestamp = int(time.time())
    
    params = {
        'app_key': APP_KEY,
        'timestamp': str(timestamp),
        'charset': 'utf-8',
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'scope': 'all'
    }
    
    params['sign'] = generate_sign(params, APP_SECRET)
    
    url = "https://openapi.jushuitan.com/openWeb/auth/accessToken"
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
    
    try:
        response = requests.post(url, data=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python jushuitan_auth.py get_auth_url          # 获取授权链接")
        print("  python jushuitan_auth.py get_token CODE        # 用 code 换取 token")
        print("  python jushuitan_auth.py refresh REFRESH_TOKEN # 刷新 token")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "get_auth_url":
        url = get_auth_url()
        print("\n=== 授权链接 ===")
        print(url)
        print("\n请将此链接复制到浏览器中访问，登录聚水潭账号并授权")
        print("授权后，浏览器会跳转到回调地址，URL 中会包含 code 参数")
        print("\n注意：code 有效期只有 15 分钟，请及时使用！")
        
    elif command == "get_token":
        if len(sys.argv) < 3:
            print("错误：需要提供 code 参数")
            print("用法: python jushuitan_auth.py get_token YOUR_CODE")
            sys.exit(1)
        
        code = sys.argv[2]
        result = get_access_token(code)
        
        print("\n=== 获取 Token 结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('code') == 0:
            data = result.get('data', {})
            print("\n=== Token 信息 ===")
            print(f"access_token:  {data.get('access_token')}")
            print(f"refresh_token: {data.get('refresh_token')}")
            print(f"expires_in:    {data.get('expires_in')} 秒")
            print(f"\n建议将以上信息保存到配置文件中")
        
    elif command == "refresh":
        if len(sys.argv) < 3:
            print("错误：需要提供 refresh_token 参数")
            print("用法: python jushuitan_auth.py refresh YOUR_REFRESH_TOKEN")
            sys.exit(1)
        
        refresh_token = sys.argv[2]
        result = refresh_access_token(refresh_token)
        
        print("\n=== 刷新 Token 结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('code') == 0:
            data = result.get('data', {})
            print("\n=== 新 Token 信息 ===")
            print(f"access_token:  {data.get('access_token')}")
            print(f"refresh_token: {data.get('refresh_token')}")
            print(f"expires_in:    {data.get('expires_in')} 秒")
    
    else:
        print(f"未知命令: {command}")
        print("可用命令: get_auth_url, get_token, refresh")
        sys.exit(1)

if __name__ == "__main__":
    main()
