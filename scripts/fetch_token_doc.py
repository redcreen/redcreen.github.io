#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭获取access_token的方法文档
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def fetch_token_doc():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 访问获取token的文档
        print("正在打开获取access_token文档...")
        page.get("https://openweb.jushuitan.com/doc?docId=23")
        time.sleep(4)
        
        print("\n页面标题:", page.title)
        
        # 获取页面内容
        body_text = page.ele('tag:body').text
        print("\n页面内容:")
        print(body_text[:25000])
        
        # 截图
        page.get_screenshot(path='jushuitan_token_doc.png', full_page=True)
        print("\n截图已保存: jushuitan_token_doc.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_token_doc()
