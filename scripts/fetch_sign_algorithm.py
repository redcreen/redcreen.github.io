#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取聚水潭API签名算法详细说明
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import time

def fetch_sign_algorithm():
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 访问签名算法页面
        print("正在打开签名算法页面...")
        page.get("https://openweb.jushuitan.com/doc?docId=2")
        time.sleep(3)
        
        # 获取页面内容
        print("\n页面标题:", page.title)
        
        # 获取所有文本
        body_text = page.ele('tag:body').text
        print("\n页面内容:")
        print(body_text)
        
        # 截图
        page.get_screenshot(path='jushuitan_sign_algorithm.png', full_page=True)
        print("\n截图已保存: jushuitan_sign_algorithm.png")
        
    finally:
        page.quit()

if __name__ == "__main__":
    fetch_sign_algorithm()
