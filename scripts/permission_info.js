const https = require('https');

// 飞书开放平台 API 文档查询
// 创建表格 API: POST /open-apis/bitable/v1/apps/{app_token}/tables

// 根据飞书文档，创建表格需要以下权限之一：
// - bitable:app:write (多维表格应用编辑权限)
// - bitable:schema (多维表格结构编辑权限)

// 但这两个权限可能在你的应用中没有

// 替代方案：使用现有的表格，通过"关联"字段来模拟子表
// 关联字段类型是 18 (Link)

console.log('创建飞书多维表格子表需要的权限：');
console.log('');
console.log('1. bitable:app:write - 多维表格应用编辑权限');
console.log('2. bitable:schema - 多维表格结构编辑权限');
console.log('');
console.log('如果这两个权限没有，可以尝试：');
console.log('- bitable:app - 多维表格应用基础权限');
console.log('- base:app:write - 多维表格写入权限');
console.log('');
console.log('或者使用替代方案：在现有表格中添加"关联"字段');
