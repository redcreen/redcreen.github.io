const https = require('https');
const fs = require('fs');
const path = require('path');

const APP_ID = 'cli_a93bab4e487adbd4';
const APP_SECRET = 'AlWk3rQyA5sAX2aiDwGO6d7Da17HMXfA';
const DOC_ID = 'XRESdwWVuokmRFxGA36cIeb5nIe';
const ROOT_BLOCK_ID = 'XRESdwWVuokmRFxGA36cIeb5nIe';

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
    hostname: 'open.feishu.cn',
    path: '/open-apis/auth/v3/tenant_access_token/internal',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, JSON.stringify({ app_id: APP_ID, app_secret: APP_SECRET }));
  return res.tenant_access_token;
}

async function getAllBlocks(token) {
  const result = await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/docx/v1/documents/${DOC_ID}/blocks/${ROOT_BLOCK_ID}/children`,
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  // API返回的是 items 不是 children
  if (result.code === 0 && result.data && result.data.items) {
    return result.data.items;
  }
  return [];
}

async function deleteBlock(token, blockId) {
  return await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/docx/v1/documents/${DOC_ID}/blocks/${blockId}`,
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

async function addBlock(token, blockId, content, style = {}) {
  const body = JSON.stringify({
    children: [{
      block_type: 2,
      text: {
        elements: [{ text_run: { content, text_element_style: style } }]
      }
    }]
  });
  
  return await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/docx/v1/documents/${DOC_ID}/blocks/${blockId}/children`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, body);
}

async function addTable(token, blockId, tableData) {
  // 构建表格块
  const tableBlock = {
    block_type: 4, // table
    table: {
      table_property: {
        header_row: true,
        column_size: tableData[0].length,
        row_size: tableData.length
      },
      cells: []
    }
  };
  
  // 为每个单元格创建内容
  for (let row = 0; row < tableData.length; row++) {
    for (let col = 0; col < tableData[row].length; col++) {
      tableBlock.table.cells.push({
        row_index: row,
        column_index: col,
        body: {
          block_type: 2,
          text: {
            elements: [{ text_run: { content: tableData[row][col] } }]
          }
        }
      });
    }
  }
  
  const body = JSON.stringify({ children: [tableBlock] });
  
  return await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/docx/v1/documents/${DOC_ID}/blocks/${blockId}/children`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, body);
}

// 从订单文件生成飞书导出内容
function generateOrderData() {
  const ordersDir = 'memory/orders';
  const files = fs.readdirSync(ordersDir).filter(f => f.endsWith('.md') && !f.startsWith('_') && f !== 'AGENT.md');
  
  const activeOrders = [];
  const completedOrders = [];
  
  for (const file of files) {
    const filePath = path.join(ordersDir, file);
    const fileContent = fs.readFileSync(filePath, 'utf8');
    
    const orderMatch = fileContent.match(/## 订单 #(\d+) - (.+)/);
    const customerMatch = fileContent.match(/\*\*客户:\*\* (.+)/);
    const statusMatch = fileContent.match(/\*\*状态:\*\* (.+)/);
    const dateMatch = fileContent.match(/\*\*下单日期:\*\* (.+)/);
    const deliveryMatch = fileContent.match(/\*\*交货日期:\*\* (.+)/);
    
    if (orderMatch) {
      const order = {
        id: orderMatch[1],
        name: orderMatch[2],
        customer: customerMatch ? customerMatch[1] : '-',
        status: statusMatch ? statusMatch[1] : '-',
        date: dateMatch ? dateMatch[1] : '-',
        delivery: deliveryMatch ? deliveryMatch[1] : '-'
      };
      
      if (fileContent.includes('生产中') || fileContent.includes('进行中')) {
        activeOrders.push(order);
      } else {
        completedOrders.push(order);
      }
    }
  }
  
  return { activeOrders, completedOrders };
}

async function sync() {
  console.log('Starting sync to Feishu...');
  
  const token = await getToken();
  console.log('Got Feishu token');
  
  // 1. 清除旧内容
  const oldBlocks = await getAllBlocks(token);
  console.log(`Found ${oldBlocks.length} old blocks to delete`);
  
  for (const block of oldBlocks) {
    await deleteBlock(token, block.block_id);
    await new Promise(r => setTimeout(r, 100));
  }
  console.log('Cleared old content');
  
  // 2. 添加标题（英文避免乱码）
  await addBlock(token, ROOT_BLOCK_ID, 'Order Management System', { bold: true });
  await addBlock(token, ROOT_BLOCK_ID, `Last Updated: ${new Date().toLocaleString('zh-CN')}`);
  await addBlock(token, ROOT_BLOCK_ID, '');
  await addBlock(token, ROOT_BLOCK_ID, '---');
  await addBlock(token, ROOT_BLOCK_ID, '');
  
  // 3. 获取订单数据
  const { activeOrders, completedOrders } = generateOrderData();
  
  // 4. 进行中订单表格
  await addBlock(token, ROOT_BLOCK_ID, `Active Orders (${activeOrders.length})`, { bold: true });
  await addBlock(token, ROOT_BLOCK_ID, '');
  
  if (activeOrders.length > 0) {
    // 表头
    const tableData = [['Order ID', 'Customer', 'Status', 'Order Date', 'Delivery Date']];
    // 数据行
    for (const order of activeOrders) {
      tableData.push([`#${order.id}`, order.customer, order.status, order.date, order.delivery]);
    }
    await addTable(token, ROOT_BLOCK_ID, tableData);
    
    // 添加每个订单的详细信息
    for (const order of activeOrders) {
      await addBlock(token, ROOT_BLOCK_ID, '');
      await addBlock(token, ROOT_BLOCK_ID, `Order #${order.id} - ${order.name}`, { bold: true });
      await addBlock(token, ROOT_BLOCK_ID, `Customer: ${order.customer}`);
      await addBlock(token, ROOT_BLOCK_ID, `Status: ${order.status}`);
    }
  } else {
    await addBlock(token, ROOT_BLOCK_ID, 'No active orders');
  }
  
  await addBlock(token, ROOT_BLOCK_ID, '');
  await addBlock(token, ROOT_BLOCK_ID, '---');
  await addBlock(token, ROOT_BLOCK_ID, '');
  
  // 5. 已完成订单表格
  await addBlock(token, ROOT_BLOCK_ID, `Completed Orders (${completedOrders.length})`, { bold: true });
  await addBlock(token, ROOT_BLOCK_ID, '');
  
  if (completedOrders.length > 0) {
    const tableData = [['Order ID', 'Customer', 'Status', 'Order Date', 'Delivery Date']];
    for (const order of completedOrders) {
      tableData.push([`#${order.id}`, order.customer, order.status, order.date, order.delivery]);
    }
    await addTable(token, ROOT_BLOCK_ID, tableData);
  } else {
    await addBlock(token, ROOT_BLOCK_ID, 'No completed orders');
  }
  
  await addBlock(token, ROOT_BLOCK_ID, '');
  await addBlock(token, ROOT_BLOCK_ID, '---');
  await addBlock(token, ROOT_BLOCK_ID, '');
  await addBlock(token, ROOT_BLOCK_ID, 'Generated by Order Assistant');
  
  console.log('Sync complete!');
  console.log('Document: https://f6w7q8b9lf.feishu.cn/docx/' + DOC_ID);
}

if (require.main === module) {
  sync().catch(console.error);
}

module.exports = { sync };
