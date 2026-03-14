const https = require('https');
const fs = require('fs');

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
  const config = JSON.parse(fs.readFileSync('memory/orders/_bitable_config.json'));
  
  const res = await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${config.tableId}/records/search`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, JSON.stringify({ page_size: 100 }));
  
  console.log('Code:', res.code);
  console.log('Msg:', res.msg);
  console.log('Total:', res.data?.total);
  console.log('Items count:', res.data?.items?.length);
  
  if (res.data?.items) {
    res.data.items.forEach((item, i) => {
      console.log(`\n记录 ${i+1}:`);
      console.log('  Record ID:', item.record_id);
      console.log('  Fields:', JSON.stringify(item.fields, null, 2));
    });
  }
}

main().catch(console.error);
