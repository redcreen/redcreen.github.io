#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取聚水潭 Access Token - 修正签名算法
"""

import hashlib
import json
import time
import requests
import random
import string

class JushuitanAuth:
    """聚水潭授权封装"""
    
    # 使用正式环境
    BASE_URL = "https://openapi.jushuitan.com"
    
    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
    
    def _generate_sign(self, params, sign_order=None):
        """
        生成API签名
        
        规则：
        1. 按照指定顺序（或字母顺序）拼接参数
        2. 格式：app_secret + key1value1 + key2value2 + ...
        3. MD5加密，结果转小写
        """
        if sign_order:
            # 使用指定顺序
            keys = sign_order
        else:
            # 按字母排序
            keys = sorted(params.keys())
        
        # 拼接字符串
        sign_str = self.app_secret
        for key in keys:
            if key == 'sign':
                continue
            value = params.get(key)
            if value is not None and value != '':
                sign_str += "%s%s" % (key, value)
        
        print(f"[签名调试] 签名字符串: {sign_str}")
        
        # MD5加密，转小写
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()
    
    def _generate_code(self):
        """生成6位随机授权码"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    def get_init_token(self):
        """
        获取初始access_token
        应用创建后会自动下发初始token
        """
        timestamp = int(time.time())
        code = self._generate_code()
        
        params = {
            'app_key': self.app_key,
            'timestamp': str(timestamp),
            'grant_type': 'authorization_code',
            'charset': 'utf-8',
            'code': code,
        }
        
        # 授权接口签名顺序：app_key, charset, code, grant_type, timestamp
        sign_order = ['app_key', 'charset', 'code', 'grant_type', 'timestamp']
        params['sign'] = self._generate_sign(params, sign_order)
        
        url = f"{self.BASE_URL}/openWeb/auth/getInitToken"
        
        print(f"\n{'='*60}")
        print("[获取初始Token]")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, data=params, timeout=30)
            print(f"\n状态码: {response.status_code}")
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        except Exception as e:
            print(f"[错误] {str(e)}")
            return {'code': -1, 'msg': str(e)}
    
    def refresh_token(self, refresh_token):
        """
        刷新access_token
        """
        timestamp = int(time.time())
        
        params = {
            'app_key': self.app_key,
            'timestamp': str(timestamp),
            'grant_type': 'refresh_token',
            'charset': 'utf-8',
            'refresh_token': refresh_token,
            'scope': 'all',
        }
        
        # 按字母排序签名
        params['sign'] = self._generate_sign(params)
        
        url = f"{self.BASE_URL}/openWeb/auth/refreshToken"
        
        print(f"\n{'='*60}")
        print("[刷新Token]")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"参数: {json.dumps(params, ensure_ascii=False, indent=2)}")
        
        try:
            response = requests.post(url, data=params, timeout=30)
            print(f"\n状态码: {response.status_code}")
            result = response.json()
            print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
        except Exception as e:
            print(f"[错误] {str(e)}")
            return {'code': -1, 'msg': str(e)}


if __name__ == '__main__':
    # 配置信息
    APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
    APP_SECRET = "baf7b719d2464309bd164753b561cda2"
    
    print("="*60)
    print("聚水潭 Access Token 获取工具")
    print("="*60)
    print(f"AppKey: {APP_KEY}")
    print()
    
    auth = JushuitanAuth(APP_KEY, APP_SECRET)
    
    # 尝试获取初始token
    print("\n>>> 尝试获取初始access_token...")
    result = auth.get_init_token()
    
    if result.get('code') == 0:
        data = result.get('data', {})
        print("\n" + "="*60)
        print("[SUCCESS] 获取Token成功!")
        print("="*60)
        print(f"access_token: {data.get('access_token')}")
        print(f"refresh_token: {data.get('refresh_token')}")
        print(f"有效期: {data.get('expires_in')} 秒 ({data.get('expires_in', 0) // 86400} 天)")
        print()
        print("请保存好这些token，后续API调用需要使用access_token")
    else:
        print("\n" + "="*60)
        print("[FAIL] 获取Token失败")
        print("="*60)
        print(f"错误码: {result.get('code')}")
        print(f"错误信息: {result.get('msg')}")
        
        if result.get('code') == 10:
            print("\n提示: 错误码10表示无效签名")
            print("可能原因：")
            print("1. 签名顺序不正确")
            print("2. 参数拼接方式不对")
