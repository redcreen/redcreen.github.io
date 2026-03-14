#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jushuitan Token Manager - Self-developed Merchant Edition

Self-developed merchants can directly call getInitToken API to get token,
no browser authorization needed!

Usage:
python scripts/jushuitan_token_manager.py get       # Get new token directly
python scripts/jushuitan_token_manager.py refresh   # Refresh token
python scripts/jushuitan_token_manager.py check     # Check token validity
"""

import sys
import os
import json
import hashlib
import time
import random
import string
import requests
from datetime import datetime, timedelta

# Config
APP_KEY = "384f96bb3d854f5fb1804cdb7e73918d"
APP_SECRET = "baf7b719d2464309bd164753b561cda2"
CONFIG_FILE = "memory/jushuitan_config.json"

def generate_sign(params, app_secret):
    """Generate signature"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = app_secret
    for key, value in sorted_params:
        if key == 'sign':
            continue
        if value is not None and value != '':
            sign_str += "%s%s" % (key, value)
    return hashlib.md5(sign_str.encode('utf-8')).hexdigest().lower()

def load_config():
    """Load config"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save config"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"[OK] Config saved to: {CONFIG_FILE}")

def get_init_token():
    """Get initial token (self-developed merchant direct call)"""
    # Generate 6-digit random code
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    timestamp = int(time.time())
    params = {
        'app_key': APP_KEY,
        'timestamp': str(timestamp),
        'charset': 'utf-8',
        'grant_type': 'authorization_code',
        'code': code
    }
    params['sign'] = generate_sign(params, APP_SECRET)
    
    url = "https://openapi.jushuitan.com/openWeb/auth/getInitToken"
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
    
    try:
        response = requests.post(url, data=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        return response.json()
    except Exception as e:
        return {'code': -1, 'msg': str(e)}

def refresh_access_token(refresh_token):
    """Refresh access_token"""
    timestamp = int(time.time())
    params = {
        'app_key': APP_KEY,
        'timestamp': str(timestamp),
        'charset': 'utf-8',
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    params['sign'] = generate_sign(params, APP_SECRET)
    
    url = "https://openapi.jushuitan.com/openWeb/auth/getInitToken"
    headers = {'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'}
    
    try:
        response = requests.post(url, data=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        return response.json()
    except Exception as e:
        return {'code': -1, 'msg': str(e)}

def check_token_valid(token):
    """Check if token is valid"""
    timestamp = int(time.time())
    params = {
        'app_key': APP_KEY,
        'access_token': token,
        'timestamp': str(timestamp),
        'charset': 'utf-8'
    }
    params['sign'] = generate_sign(params, APP_SECRET)
    
    url = "https://openapi.jushuitan.com/open/jushuitan/inventory/query"
    try:
        resp = requests.post(url, data=params, timeout=10)
        data = resp.json()
        if data.get('code') == 190:
            return False, "Token expired"
        elif data.get('code') == 0:
            return True, "Token valid"
        else:
            return False, f"Error: {data.get('msg')}"
    except Exception as e:
        return False, str(e)

def cmd_get():
    """Get token directly (self-developed merchant)"""
    print("=" * 60)
    print("Jushuitan Token Manager (Self-developed Merchant)")
    print("=" * 60)
    print()
    print("Calling getInitToken API...")
    print()
    
    result = get_init_token()
    
    if result.get('code') != 0:
        print(f"[FAILED] Get token failed: {result}")
        return
    
    data = result.get('data', {})
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    expires_in = data.get('expires_in', 0)
    
    print(f"[SUCCESS] Token obtained!")
    print(f"  access_token:  {access_token}")
    print(f"  refresh_token: {refresh_token}")
    print(f"  expires_in:    {expires_in} seconds ({expires_in/86400:.1f} days)")
    
    # Save config
    config = load_config()
    config.update({
        'app_key': APP_KEY,
        'app_secret': APP_SECRET,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_expires_at': (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
        'updated_at': datetime.now().isoformat()
    })
    save_config(config)
    print()
    print("[OK] Config saved. Use 'refresh' command next time.")

def cmd_refresh():
    """Refresh token"""
    config = load_config()
    refresh_token = config.get('refresh_token')
    
    if not refresh_token:
        print("[ERROR] No refresh_token found. Run: python jushuitan_token_manager.py get")
        return
    
    print("Refreshing token...")
    result = refresh_access_token(refresh_token)
    
    if result.get('code') != 0:
        print(f"[FAILED] Refresh failed: {result}")
        print("May need to get new token.")
        return
    
    data = result.get('data', {})
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    expires_in = data.get('expires_in', 0)
    
    print(f"[SUCCESS] Token refreshed!")
    print(f"  access_token:  {access_token}")
    print(f"  refresh_token: {refresh_token}")
    print(f"  expires_in:    {expires_in} seconds ({expires_in/86400:.1f} days)")
    
    # Update config
    config.update({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_expires_at': (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
        'updated_at': datetime.now().isoformat()
    })
    save_config(config)

def cmd_check():
    """Check token validity"""
    config = load_config()
    token = config.get('access_token')
    
    if not token:
        print("[ERROR] No access_token found")
        return
    
    print(f"Checking token: {token[:20]}...")
    valid, msg = check_token_valid(token)
    
    if valid:
        print(f"[OK] {msg}")
        expires_at = config.get('token_expires_at')
        if expires_at:
            print(f"Expires at: {expires_at}")
    else:
        print(f"[ERROR] {msg}")
        print("Run: python jushuitan_token_manager.py refresh")

def main():
    if len(sys.argv) < 2:
        print("Jushuitan Token Manager (Self-developed Merchant Edition)")
        print()
        print("Self-developed merchants can directly get token,")
        print("no browser authorization needed!")
        print()
        print("Usage:")
        print("  python jushuitan_token_manager.py get       # Get new token directly")
        print("  python jushuitan_token_manager.py refresh   # Refresh token")
        print("  python jushuitan_token_manager.py check     # Check token validity")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "get":
        cmd_get()
    elif command == "refresh":
        cmd_refresh()
    elif command == "check":
        cmd_check()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: get, refresh, check")
        sys.exit(1)

if __name__ == "__main__":
    main()
