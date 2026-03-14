#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭仓库查询接口文档
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def fetch_warehouse_doc():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 搜索仓库查询接口
        print("正在搜索仓库查询接口文档...")
        page.get("https://openweb.jushuitan.com/doc?docId=77")
        time.sleep(4)
        
        print("\n页面标题:", page.title)
        
        # 获取页面内容
        body_text = page.ele('tag:body').text
        print("\n页面内容:")
        print(body_text[:15000])
        
        # 截图
        page.get_screenshot(path='jushuitan_warehouse_doc.png', full_page=True)
        print("\n截图已保存: jushuitan_warehouse_doc.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_warehouse_doc()
