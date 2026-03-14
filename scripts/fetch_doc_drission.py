#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用DrissionPage获取聚水潭API文档 - 完整版
"""

from DrissionPage import ChromiumPage, ChromiumOptions
import json
import time
import re

def fetch_api_doc():
    # 配置浏览器选项
    co = ChromiumOptions()
    co.headless(True)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    
    # 启动浏览器
    page = ChromiumPage(addr_or_opts=co)
    
    try:
        # 访问API文档页面
        print("正在打开API文档页面...")
        page.get("https://openweb.jushuitan.com/doc?docId=113")
        
        # 等待页面加载
        time.sleep(5)
        
        # 获取页面信息
        print("\n页面标题:", page.title)
        print("当前URL:", page.url)
        
        # 获取页面完整HTML
        html = page.html
        
        # 从HTML中提取API接口信息
        # 聚水潭API路径格式通常是 /open/xxx/xxx
        api_pattern = r'/open/[a-zA-Z0-9/_]+'
        apis = re.findall(api_pattern, html)
        
        # 去重并排序
        unique_apis = sorted(list(set(apis)))
        
        print(f"\n找到 {len(unique_apis)} 个API接口路径:")
        print("="*80)
        
        # 分类显示
        categories = {
            '店铺': [],
            '商品': [],
            '订单': [],
            '库存': [],
            '售后': [],
            '采购': [],
            '入库': [],
            '出库': [],
            '调拨': [],
            '其他': []
        }
        
        for api in unique_apis:
            if 'shop' in api:
                categories['店铺'].append(api)
            elif 'item' in api or 'sku' in api or 'category' in api or 'bom' in api:
                categories['商品'].append(api)
            elif 'order' in api:
                categories['订单'].append(api)
            elif 'inventory' in api or 'pack' in api or 'count' in api:
                categories['库存'].append(api)
            elif 'aftersale' in api or 'refund' in api:
                categories['售后'].append(api)
            elif 'purchase' in api or 'supplier' in api or 'manufacture' in api:
                categories['采购'].append(api)
            elif 'purchasein' in api or 'in/upload' in api or 'otherin' in api:
                categories['入库'].append(api)
            elif 'purchaseout' in api or 'out' in api:
                categories['出库'].append(api)
            elif 'allocate' in api:
                categories['调拨'].append(api)
            else:
                categories['其他'].append(api)
        
        # 显示分类结果
        for cat, apis in categories.items():
            if apis:
                print(f"\n【{cat}相关】")
                for api in apis[:20]:  # 每类最多显示20个
                    print(f"  {api}")
        
        # 保存完整列表
        api_data = {
            'total': len(unique_apis),
            'apis': unique_apis,
            'by_category': {k: v for k, v in categories.items() if v}
        }
        
        with open('jushuitan_apis_full.json', 'w', encoding='utf-8') as f:
            json.dump(api_data, f, ensure_ascii=False, indent=2)
        print("\n\n完整API列表已保存到 jushuitan_apis_full.json")
        
        # 截图
        page.get_screenshot(path='jushuitan_api_doc.png', full_page=True)
        print("截图已保存: jushuitan_api_doc.png")
        
        return api_data
        
    finally:
        page.quit()

if __name__ == "__main__":
    apis = fetch_api_doc()
    print("\n" + "="*80)
    print("抓取完成! 共找到 %d 个API接口" % apis['total'])
    print("="*80)
