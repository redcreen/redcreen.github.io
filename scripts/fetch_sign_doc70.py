#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭通用签名文档 docId=70
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def fetch_sign_doc():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 访问通用签名文档
        print("正在打开通用签名文档...")
        page.get("https://openweb.jushuitan.com/doc?docId=70")
        time.sleep(4)
        
        print("\n页面标题:", page.title)
        
        # 获取页面内容
        body_text = page.ele('tag:body').text
        print("\n页面内容:")
        print(body_text[:25000])
        
        # 截图
        page.get_screenshot(path='jushuitan_sign_doc70.png', full_page=True)
        print("\n截图已保存: jushuitan_sign_doc70.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_sign_doc()
