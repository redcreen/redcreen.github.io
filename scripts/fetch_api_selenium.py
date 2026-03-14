#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Selenium获取聚水潭API文档
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def fetch_api_doc():
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 启动浏览器
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 访问API文档页面
        print("正在打开API文档页面...")
        driver.get("https://openweb.jushuitan.com/doc?docId=113")
        
        # 等待页面加载
        time.sleep(5)
        
        # 获取页面信息
        print("\n页面标题:", driver.title)
        print("\n当前URL:", driver.current_url)
        
        # 获取页面文本
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print("\n页面文本内容前4000字符:")
        print(body_text[:4000])
        
        # 查找所有可能包含API信息的元素
        print("\n\n查找API相关信息...")
        
        # 查找pre、code等元素
        code_elements = driver.find_elements(By.CSS_SELECTOR, "pre, code, .api-method, .method-name")
        print("找到 %d 个代码/方法元素" % len(code_elements))
        
        for i, elem in enumerate(code_elements[:15]):
            text = elem.text.strip()
            if text and len(text) < 300:
                print("\n--- 元素 %d ---" % (i+1))
                print(text)
        
        # 查找包含"jushuitan"的元素
        jst_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'jushuitan.')]")
        print("\n\n找到 %d 个包含'jushuitan.'的元素" % len(jst_elements))
        
        for i, elem in enumerate(jst_elements[:10]):
            text = elem.text.strip()
            if text and len(text) < 200:
                print("\n--- API %d ---" % (i+1))
                print(text)
        
        # 截图
        driver.save_screenshot("jushuitan_api_doc.png")
        print("\n\n截图已保存: jushuitan_api_doc.png")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_api_doc()
