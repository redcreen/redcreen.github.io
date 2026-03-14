#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭库存查询接口详细文档 - docId=15
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def fetch_inventory_detail():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 访问库存查询接口详细文档
        print("正在打开库存查询接口详细文档...")
        page.get("https://openweb.jushuitan.com/dev-doc?docType=3&docId=15")
        time.sleep(4)
        
        print("\n页面标题:", page.title)
        
        # 获取页面内容
        body_text = page.ele('tag:body').text
        print("\n页面内容:")
        print(body_text[:20000])
        
        # 截图
        page.get_screenshot(path='jushuitan_inventory_detail.png', full_page=True)
        print("\n截图已保存: jushuitan_inventory_detail.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_inventory_detail()
