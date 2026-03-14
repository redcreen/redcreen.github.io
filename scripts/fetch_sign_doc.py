#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭API签名说明文档
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def fetch_sign_doc():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 访问签名说明页面
        print("正在打开签名说明页面...")
        page.get("https://openweb.jushuitan.com/doc?docId=3")
        time.sleep(3)
        
        # 获取页面内容
        print("\n页面标题:", page.title)
        
        # 获取所有文本
        body_text = page.ele('tag:body').text
        print("\n页面内容前8000字符:")
        print(body_text[:8000])
        
        # 截图
        page.get_screenshot(path='jushuitan_sign_doc.png', full_page=True)
        print("\n截图已保存: jushuitan_sign_doc.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_sign_doc()
