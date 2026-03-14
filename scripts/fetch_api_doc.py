#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Playwright获取聚水潭API文档
"""

from playwright.sync_api import sync_playwright
import json
import time

def fetch_api_doc():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 访问API文档页面
        print("正在打开API文档页面...")
        page.goto("https://openweb.jushuitan.com/doc?docId=113", wait_until="networkidle")
        
        # 等待页面加载完成
        time.sleep(3)
        
        # 获取页面内容
        content = page.content()
        
        # 尝试提取API信息
        # 通常API文档会有特定的class或id
        print("\n页面标题:", page.title())
        
        # 获取所有文本内容
        text_content = page.inner_text("body")
        print("\n页面文本内容前3000字符:")
        print(text_content[:3000])
        
        # 尝试找到API列表
        # 查找包含API method的元素
        api_elements = page.query_selector_all("[class*='api'], [class*='method'], pre, code")
        print("\n\n找到 %d 个可能的API元素" % len(api_elements))
        
        for i, elem in enumerate(api_elements[:10]):
            text = elem.inner_text()
            if text and len(text) < 500:
                print("\n元素 %d:" % i)
                print(text[:200])
        
        # 截图保存
        page.screenshot(path="jushuitan_api_doc.png", full_page=True)
        print("\n截图已保存: jushuitan_api_doc.png")
        
        browser.close()

if __name__ == "__main__":
    fetch_api_doc()
