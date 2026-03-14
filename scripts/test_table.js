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
  const token = await getToken();
  
  // 测试创建表格
  const config = JSON.parse(fs.readFileSync('memory/orders/_bitable_config.json', 'utf8'));
  
  console.log('AppToken:', config.appToken);
  
  const res = await request({
    hostname: FEISHU_API_BASE,
    path: `/open-apis/bitable/v1/apps/${config.appToken}/tables`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, JSON.stringify({ name: '测试表' }));
  
  console.log('Result:', JSON.stringify(res, null, 2));
}

main().catch(console.error);
