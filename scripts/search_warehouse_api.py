#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索聚水潭仓库查询接口
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def search_warehouse_api():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 访问API列表页面
        print("正在访问API列表...")
        page.get("https://openweb.jushuitan.com/dev-doc?docType=1&docId=1")
        time.sleep(5)
        
        print("\n页面标题:", page.title)
        
        # 搜索仓库
        print("\n搜索'仓库'...")
        search_box = page.ele('css:input[placeholder*="搜索"]')
        if search_box:
            search_box.input("仓库")
            time.sleep(2)
        
        # 获取页面内容
        body_text = page.ele('tag:body').text
        print("\n页面内容 (前10000字符):")
        print(body_text[:10000])
        
        # 截图
        page.get_screenshot(path='jushuitan_api_list.png', full_page=True)
        print("\n截图已保存: jushuitan_api_list.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    search_warehouse_api()
