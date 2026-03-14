#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭授权签名工具文档
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def fetch_sign_tool_doc():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 访问授权签名工具文档
        print("正在打开授权签名工具文档...")
        page.get("https://openweb.jushuitan.com/doc?docId=135")
        time.sleep(4)
        
        print("\n页面标题:", page.title)
        
        # 获取页面内容
        body_text = page.ele('tag:body').text
        print("\n页面内容:")
        print(body_text[:20000])
        
        # 截图
        page.get_screenshot(path='jushuitan_sign_tool.png', full_page=True)
        print("\n截图已保存: jushuitan_sign_tool.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_sign_tool_doc()
