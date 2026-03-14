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

async function main() {
  try {
    const token = await getToken();
    const config = JSON.parse(fs.readFileSync('memory/orders/_bitable_config.json', 'utf8'));
    
    console.log('AppToken:', config.appToken);
    console.log('TableId:', config.tableId);
    
    // 获取表格字段
    const fieldsRes = await request({
      hostname: FEISHU_API_BASE,
      path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${config.tableId}/fields`,
      method: 'GET',
      headers: { 
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('\n表格字段:');
    if (fieldsRes.code === 0 && fieldsRes.data && fieldsRes.data.items) {
      fieldsRes.data.items.forEach(f => {
        console.log(`  - ${f.field_name} (${f.field_type})`);
      });
    } else {
      console.log('  获取失败:', fieldsRes.msg);
    }
    
    // 获取记录
    const recordsRes = await request({
      hostname: FEISHU_API_BASE,
      path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${config.tableId}/records/search`,
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    }, JSON.stringify({ page_size: 10 }));
    
    console.log('\n记录:');
    if (recordsRes.code === 0 && recordsRes.data && recordsRes.data.items) {
      recordsRes.data.items.forEach((r, i) => {
        console.log(`  ${i+1}.`, JSON.stringify(r.fields));
      });
    }
    
  } catch (error) {
    console.error('错误:', error.message);
  }
}

main();
