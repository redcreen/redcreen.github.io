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
  
  // 尝试不同的请求体格式
  console.log('测试 1: 最简单的格式');
  const res1 = await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/bitable/v1/apps/${config.appToken}/tables`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, JSON.stringify({ table_name: '测试表' }));
  console.log('Result:', JSON.stringify(res1, null, 2));
  
  console.log('\n测试 2: 使用 name 字段');
  const res2 = await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/bitable/v1/apps/${config.appToken}/tables`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, JSON.stringify({ name: '测试表2' }));
  console.log('Result:', JSON.stringify(res2, null, 2));
}

main().catch(console.error);
