#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭库存查询接口详细文档
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
        # 访问库存查询接口文档
        print("正在打开库存查询接口文档...")
        page.get("https://openweb.jushuitan.com/doc?docId=39")
        time.sleep(3)
        
        print("\n页面标题:", page.title)
        
        # 获取页面内容
        body_text = page.ele('tag:body').text
        print("\n页面内容:")
        print(body_text[:15000])
        
        # 截图
        page.get_screenshot(path='jushuitan_inventory_doc.png', full_page=True)
        print("\n截图已保存: jushuitan_inventory_doc.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_inventory_doc()
