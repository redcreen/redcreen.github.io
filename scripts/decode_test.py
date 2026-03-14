# -*- coding: utf-8 -*-
import json

# 从原始响应中解析
raw = b'{"msg":"\xe6\x89\xa7\xe8\xa1\x8c\xe6\x88\x90\xe5\x8a\x9f","code":0,"data":{"inventorys":[{"i_id":"NH500","purchase_qty":1351,"min_qty":null,"allocate_qty":850,"sku_id":"NH500-1","virtual_qty":0,"order_lock":6,"max_qty":0,"customize_qty_1":0,"pick_lock":1,"qty":5492,"name":"15#\xe5\xae\x8b\xe9\x94\xa6\xe5\xb0\x8f\xe9\xa9\xac-\xe7\xba\xa2\xe8\x89\xb2\xe6\xb5\xb7\xe6\xb5\xaa-\xe5\x9b\x9e\xe5\xa4\xb4","modified":"2026-03-14 12:32:05","in_qty":0,"defective_qty":0,"return_qty":2,"ts":7042403203}],"requestId":null,"page_index":1,"has_next":false,"data_count":1,"page_count":1,"page_size":10}}'
result = json.loads(raw.decode('utf-8'))
inv = result['data']['inventorys'][0]
print('SKU:', inv['sku_id'])
print('名称:', inv['name'])
print('库存:', inv['qty'])
