#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭库存查询接口详细文档 - 尝试不同ID
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time
import json

def fetch_inventory_doc():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 先访问API列表页面，找到库存查询接口的链接
        print("正在打开API列表页面...")
        page.get("https://openweb.jushuitan.com/doc?docId=113")
        time.sleep(3)
        
        print("\n页面标题:", page.title)
        
        # 查找包含"库存"的链接
        links = page.eles('tag:a')
        for link in links:
            text = link.text
            if '库存' in text or 'inventory' in text.lower():
                print(f"找到链接: {text} - {link.attr('href')}")
        
        # 获取页面内容
        body_text = page.ele('tag:body').text
        
        # 查找库存查询相关内容
        lines = body_text.split('\n')
        for i, line in enumerate(lines):
            if 'inventory' in line.lower() or '库存' in line:
                print(f"\n找到库存相关内容 (行{i}):")
                # 打印前后几行
                start = max(0, i-2)
                end = min(len(lines), i+5)
                for j in range(start, end):
                    marker = ">>> " if j == i else "    "
                    print(f"{marker}{lines[j]}")
                print("-" * 50)
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_inventory_doc()
