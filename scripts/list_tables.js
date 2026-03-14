const https = require('https');

const APP_ID = 'cli_a93bab4e487adbd4';
const APP_SECRET = 'AlWk3rQyA5sAX2aiDwGO6d7Da17HMXfA';

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

async function main() {
  const tokenRes = await request({
    hostname: 'open.feishu.cn',
    path: '/open-apis/auth/v3/tenant_access_token/internal',
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, JSON.stringify({ app_id: APP_ID, app_secret: APP_SECRET }));
  
  const token = tokenRes.tenant_access_token;
  const config = JSON.parse(require('fs').readFileSync('memory/orders/_bitable_config.json'));
  
  // 先获取现有表格列表
  const tablesRes = await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/bitable/v1/apps/${config.appToken}/tables`,
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  console.log('现有表格:', JSON.stringify(tablesRes, null, 2));
}

main().catch(console.error);
