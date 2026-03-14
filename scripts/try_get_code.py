#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试直接获取 code（商家已授权的情况下）
"""
import hashlib
import time
import urllib.parse
import requests

APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
APP_SECRET = "baf7b719d2464309bd164753b561cda2"
REDIRECT_URI = "http://localhost:8080/callback"

def generate_sign(params, app_secret):
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = app_secret
    for key, value in sorted_params:
        if key == 'sign':
            continue
        if value is not None and value != '':
            sign_str += "%s%s" % (key, value)
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()

def try_get_code():
    timestamp = int(time.time())
    
    params = {
        'app_key': APP_KEY,
        'timestamp': str(timestamp),
        'charset': 'utf-8',
        'redirect_uri': REDIRECT_URI
    }
    
    params['sign'] = generate_sign(params, APP_SECRET)
    
    url = "https://openweb.jushuitan.com/auth/authorize"
    
    print(f"请求 URL: {url}")
    print(f"参数: {params}")
    print()
    
    # 尝试 GET 请求，看是否直接返回 code
    try:
        resp = requests.get(url, params=params, allow_redirects=False, timeout=30)
        print(f"状态码: {resp.status_code}")
        print(f"Location: {resp.headers.get('Location', '无')}")
        print()
        
        # 检查是否有重定向到回调地址
        location = resp.headers.get('Location', '')
        if REDIRECT_URI in location and 'code=' in location:
            # 提取 code
            parsed = urllib.parse.urlparse(location)
            query = urllib.parse.parse_qs(parsed.query)
            code = query.get('code', [None])[0]
            print(f"✅ 获取到 code: {code}")
            return code
        else:
            print(f"响应内容前 500 字符:")
            print(resp.text[:500])
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    return None

if __name__ == "__main__":
    code = try_get_code()
    if code:
        print(f"\n获取成功！code: {code}")
    else:
        print("\n无法直接获取 code，需要走授权页面")
