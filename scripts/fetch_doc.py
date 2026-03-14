#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取聚水潭API文档
"""

import requests

url = "https://openweb.jushuitan.com/doc?docId=113"

try:
    response = requests.get(url, timeout=30)
    print("状态码:", response.status_code)
    print("\n内容前3000字符:")
    print(response.text[:3000])
except Exception as e:
    print("错误:", str(e))
