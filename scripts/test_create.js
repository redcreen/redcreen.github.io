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
        console.log('Response:', body);
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
  
  // 获取字段ID
  const fieldsRes = await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${config.tableId}/fields`,
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  console.log('\n字段列表:');
  const fieldMap = {};
  fieldsRes.data.items.forEach(f => {
    console.log(`  ${f.field_name}: ${f.field_id}`);
    fieldMap[f.field_name] = f.field_id;
  });
  
  // 创建测试记录
  console.log('\n创建测试记录...');
  const fields = {};
  fields[fieldMap['订单号']] = 'TEST001';
  fields[fieldMap['订单名称']] = '测试订单';
  fields[fieldMap['客户']] = '测试客户';
  fields[fieldMap['状态']] = '测试中';
  fields[fieldMap['下单日期']] = '2026-03-11';
  fields[fieldMap['交货日期']] = '2026-03-20';
  
  console.log('Fields payload:', JSON.stringify(fields, null, 2));
  
  const createRes = await request({
    hostname: 'open.feishu.cn',
    path: `/open-apis/bitable/v1/apps/${config.appToken}/tables/${config.tableId}/records`,
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }, JSON.stringify({ fields }));
  
  console.log('\n创建结果:');
  console.log('Code:', createRes.code);
  console.log('Msg:', createRes.msg);
  if (createRes.data) {
    console.log('Data:', JSON.stringify(createRes.data, null, 2));
  }
}

main().catch(console.error);
