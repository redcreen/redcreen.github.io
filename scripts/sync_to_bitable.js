const https = require('https');
const fs = require('fs');
const path = require('path');

const APP_ID = 'cli_a93bab4e487adbd4';
const APP_SECRET = 'AlWk3rQyA5sAX2aiDwGO6d7Da17HMXfA';
const FEISHU_API_BASE = 'open.feishu.cn';

function request(options, data = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); } catch { resolve({ raw: body }); }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function getToken() {
  const res = await request({
    hostname: FEISHU_API_BASE,
    path: '/open-apis/auth/v3/tenant_access_token/internal',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, JSON.stringify({ app_id: APP_ID, app_secret: APP_SECRET }));
  return res.tenant_access_token;
}

// 创建表格
async function createTable(token, appToken, name) {
  const res = await request({
    hostname: FEISHU_API_BASE,
    path: `/open-apis/bitable/v1/apps/${appToken}/tables`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, JSON.stringify({ table: { name } }));
  
  if (res.code !== 0) {
    console.log(`  创建表格 ${name} 失败: ${res.msg}`);
    return null;
  }
  return res.data.table;
}

// 删除字段
async function deleteField(token, appToken, tableId, fieldId) {
  await request({
    hostname: FEISHU_API_BASE,
    path: `/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/fields/${fieldId}`,
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// 创建字段
async function createField(token, appToken, tableId, fieldName, fieldType) {
  const res = await request({
    hostname: FEISHU_API_BASE,
    path: `/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/fields`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, JSON.stringify({ field_name: fieldName, type: fieldType }));
  
  if (res.code !== 0) {
    console.log(`  创建字段 ${fieldName} 失败: ${res.msg}`);
    return null;
  }
  return res.data.field;
}

// 删除记录
async function deleteRecord(token, appToken, tableId, recordId) {
  await request({
    hostname: FEISHU_API_BASE,
    path: `/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/records/${recordId}`,
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// 创建记录
async function createRecord(token, appToken, tableId, fields) {
  const res = await request({
    hostname: FEISHU_API_BASE,
    path: `/open-apis/bitable/v1/apps/${appToken}/tables/${tableId}/records`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, JSON.stringify({ fields }));
  
  return res;
}

// 解析订单文件
function parseOrderFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  
  const orderMatch = content.match(/## 订单 #(\d+) - (.+)/);
  const customerMatch = content.match(/\*\*客户:\*\* (.+)/);
  const statusMatch = content.match(/\*\*状态:\*\* (.+)/);
  const dateMatch = content.match(/\*\*下单时间:\*\* (.+)/);
  const deliveryMatch = content.match(/\*\*交货时间:\*\* (.+)/);
  
  // 解析产品明细
  const products = [];
  const productMatch = content.match(/### 产品明细([\s\S]*?)(?=###|##|$)/);
  if (productMatch) {
    const lines = productMatch[1].split('\n');
    for (const line of lines) {
      const match = line.match(/\|(.+)\|(.+)\|(.+)\|/);
      if (match && !line.includes('产品') && match[1].trim() !== '------') {
        products.push({
          name: match[1].trim(),
          quantity: match[2].trim(),
          note: match[3].trim()
        });
      }
    }
  }
  
  // 解析进度
  const progress = [];
  const progressMatch = content.match(/### 当前进度([\s\S]*?)(?=###|##|$)/);
  if (progressMatch) {
    const lines = progressMatch[1].split('\n');
    for (const line of lines) {
      if (line.includes('- [')) {
        const done = line.includes('[x]');
        const text = line.replace(/- \[[ x]\]\s*/, '').replace(/\*\*/g, '');
        progress.push({
          step: text.split(' - ')[0] || text,
          status: done ? '已完成' : '进行中',
          note: text.split(' - ')[1] || ''
        });
      }
    }
  }
  
  // 关键事项
  const keyPoints = [];
  const keyMatch = content.match(/### 关键事项([\s\S]*?)(?=###|##|$)/);
  if (keyMatch) {
    const lines = keyMatch[1].split('\n');
    for (const line of lines) {
      if (line.startsWith('- ')) {
        keyPoints.push(line.replace('- ', '').replace(/\*\*/g, ''));
      }
    }
  }
  
  // 联系人
  const contacts = [];
  const contactMatch = content.match(/### 联系人([\s\S]*?)(?=###|##|$)/);
  if (contactMatch) {
    const lines = contactMatch[1].split('\n');
    for (const line of lines) {
      if (line.startsWith('- ')) {
        contacts.push(line.replace('- ', '').replace(/\*\*/g, ''));
      }
    }
  }
  
  return {
    orderId: orderMatch ? orderMatch[1] : '-',
    name: orderMatch ? orderMatch[2] : '-',
    customer: customerMatch ? customerMatch[1] : '-',
    status: statusMatch ? statusMatch[1] : '-',
    orderDate: dateMatch ? dateMatch[1] : '-',
    deliveryDate: deliveryMatch ? deliveryMatch[1] : '-',
    products,
    progress,
    keyPoints: keyPoints.join('\n'),
    contacts: contacts.join('\n')
  };
}

// 获取所有订单
function getAllOrders() {
  const ordersDir = 'memory/orders';
  const files = fs.readdirSync(ordersDir).filter(f => f.endsWith('.md') && !f.startsWith('_') && f !== 'AGENT.md');
  return files.map(f => parseOrderFile(path.join(ordersDir, f)));
}

async function main() {
  try {
    console.log('开始创建飞书多维表格（带子表）...\n');
    
    const token = await getToken();
    const config = JSON.parse(fs.readFileSync('memory/orders/_bitable_config.json', 'utf8'));
    
    // 1. 获取现有表格
    const tablesRes = await request({
      hostname: FEISHU_API_BASE,
      path: `/open-apis/bitable/v1/apps/${config.appToken}/tables`,
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    let orderTableId = config.tableId;
    let productTableId = null;
    let progressTableId = null;
    
    // 查找或创建子表
    if (tablesRes.code === 0 && tablesRes.data.items) {
      for (const table of tablesRes.data.items) {
        if (table.name === '产品明细') productTableId = table.table_id;
        if (table.name === '进度跟踪') progressTableId = table.table_id;
      }
    }
    
    // 2. 创建产品明细表
    if (!productTableId) {
      console.log('创建产品明细表...');
      const table = await createTable(token, config.appToken, '产品明细');
      if (table) {
        productTableId = table.table_id;
        
        // 创建字段
        await createField(token, config.appToken, productTableId, '关联订单', 1);
        await createField(token, config.appToken, productTableId, '产品名称', 1);
        await createField(token, config.appToken, productTableId, '数量', 1);
        await createField(token, config.appToken, productTableId, '备注', 1);
        console.log('  ✓ 产品明细表创建完成');
      }
    }
    
    // 3. 创建进度跟踪表
    if (!progressTableId) {
      console.log('创建进度跟踪表...');
      const table = await createTable(token, config.appToken, '进度跟踪');
      if (table) {
        progressTableId = table.table_id;
        
        await createField(token, config.appToken, progressTableId, '关联订单', 1);
        await createField(token, config.appToken, progressTableId, '步骤', 1);
        await createField(token, config.appToken, progressTableId, '状态', 1);
        await createField(token, config.appToken, progressTableId, '备注', 1);
        console.log('  ✓ 进度跟踪表创建完成');
      }
    }
    
    // 4. 清理主表旧数据
    console.log('\n清理主表旧数据...');
    const fieldsRes = await request({
      hostname: FEISHU_API_BASE,
      path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${orderTableId}/fields`,
      method: 'GET',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (fieldsRes.code === 0 && fieldsRes.data.items) {
      for (const field of fieldsRes.data.items) {
        if (!field.is_primary) {
          await deleteField(token, config.appToken, orderTableId, field.field_id);
        }
      }
    }
    
    const recordsRes = await request({
      hostname: FEISHU_API_BASE,
      path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${orderTableId}/records/search`,
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    }, JSON.stringify({ page_size: 500 }));
    
    if (recordsRes.code === 0 && recordsRes.data.items) {
      for (const record of recordsRes.data.items) {
        await deleteRecord(token, config.appToken, orderTableId, record.record_id);
      }
    }
    
    // 清理子表数据
    if (productTableId) {
      const productRes = await request({
        hostname: FEISHU_API_BASE,
        path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${productTableId}/records/search`,
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      }, JSON.stringify({ page_size: 500 }));
      
      if (productRes.code === 0 && productRes.data.items) {
        for (const record of productRes.data.items) {
          await deleteRecord(token, config.appToken, productTableId, record.record_id);
        }
        console.log(`  清理产品明细表 ${productRes.data.items.length} 条记录`);
      }
    }
    
    if (progressTableId) {
      const progressRes = await request({
        hostname: FEISHU_API_BASE,
        path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${progressTableId}/records/search`,
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      }, JSON.stringify({ page_size: 500 }));
      
      if (progressRes.code === 0 && progressRes.data.items) {
        for (const record of progressRes.data.items) {
          await deleteRecord(token, config.appToken, progressTableId, record.record_id);
        }
        console.log(`  清理进度跟踪表 ${progressRes.data.items.length} 条记录`);
      }
    }
    
    // 5. 创建主表字段
    console.log('\n创建主表字段...');
    await createField(token, config.appToken, orderTableId, '订单号', 1);
    await createField(token, config.appToken, orderTableId, '订单名称', 1);
    await createField(token, config.appToken, orderTableId, '客户', 1);
    await createField(token, config.appToken, orderTableId, '状态', 1);
    await createField(token, config.appToken, orderTableId, '下单日期', 1);
    await createField(token, config.appToken, orderTableId, '交货日期', 1);
    await createField(token, config.appToken, orderTableId, '关键事项', 1);
    await createField(token, config.appToken, orderTableId, '联系人', 1);
    
    // 6. 同步数据
    console.log('\n同步订单数据...');
    const orders = getAllOrders();
    
    for (const order of orders) {
      // 创建主表记录
      const mainFields = {
        '订单号': order.orderId,
        '订单名称': order.name,
        '客户': order.customer,
        '状态': order.status,
        '下单日期': order.orderDate,
        '交货日期': order.deliveryDate,
        '关键事项': order.keyPoints,
        '联系人': order.contacts
      };
      
      const mainRes = await createRecord(token, config.appToken, orderTableId, mainFields);
      
      if (mainRes.code === 0) {
        console.log(`  ✓ 添加订单 #${order.orderId}`);
        
        // 添加产品明细到子表
        if (productTableId) {
          for (const product of order.products) {
            await createRecord(token, config.appToken, productTableId, {
              '关联订单': order.orderId,
              '产品名称': product.name,
              '数量': product.quantity,
              '备注': product.note
            });
          }
        }
        
        // 添加进度到子表
        if (progressTableId) {
          for (const step of order.progress) {
            await createRecord(token, config.appToken, progressTableId, {
              '关联订单': order.orderId,
              '步骤': step.step,
              '状态': step.status,
              '备注': step.note
            });
          }
        }
      } else {
        console.log(`  ✗ 添加订单 #${order.orderId} 失败: ${mainRes.msg}`);
      }
    }
    
    console.log('\n✓ 同步完成！');
    console.log(`多维表格链接: ${config.url}`);
    
    // 保存子表ID
    config.productTableId = productTableId;
    config.progressTableId = progressTableId;
    fs.writeFileSync('memory/orders/_bitable_config.json', JSON.stringify(config, null, 2));
    
  } catch (error) {
    console.error('错误:', error.message);
  }
}

main();
