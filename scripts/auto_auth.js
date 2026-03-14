const { chromium } = require('playwright');

const APP_KEY = '384f96bb3d854f5fb1804cdb7e73918d';
const APP_SECRET = 'baf7b719d2464309bd164753b561cda2';
const REDIRECT_URI = 'http://localhost:8080/callback';

function generateSign(params, appSecret) {
    const sortedParams = Object.keys(params).sort().map(key => {
        if (key === 'sign') return '';
        const value = params[key];
        if (value !== null && value !== undefined && value !== '') {
            return `${key}${value}`;
        }
        return '';
    }).join('');
    
    const signStr = appSecret + sortedParams;
    return require('crypto').createHash('md5').update(signStr).digest('hex').toLowerCase();
}

async function autoAuth() {
    const timestamp = Math.floor(Date.now() / 1000);
    
    const params = {
        app_key: APP_KEY,
        timestamp: timestamp.toString(),
        charset: 'utf-8',
        redirect_uri: REDIRECT_URI
    };
    
    params.sign = generateSign(params, APP_SECRET);
    
    const queryString = new URLSearchParams(params).toString();
    const authUrl = `https://openweb.jushuitan.com/auth/authorize?${queryString}`;
    
    console.log('授权URL:', authUrl);
    console.log('启动浏览器...');
    
    const browser = await chromium.launch({ 
        headless: false,  // 显示浏览器，方便超哥登录
        channel: 'msedge'
    });
    
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // 监听所有请求，捕获 code
    let capturedCode = null;
    
    page.on('request', request => {
        const url = request.url();
        if (url.includes('localhost:8080/callback') && url.includes('code=')) {
            const urlObj = new URL(url);
            capturedCode = urlObj.searchParams.get('code');
            console.log('✅ 捕获到 code:', capturedCode);
        }
    });
    
    page.on('response', response => {
        const url = response.url();
        if (url.includes('localhost:8080/callback') && url.includes('code=')) {
            const urlObj = new URL(url);
            capturedCode = urlObj.searchParams.get('code');
            console.log('✅ 从响应捕获到 code:', capturedCode);
        }
    });
    
    // 打开授权页面
    await page.goto(authUrl);
    
    console.log('\n浏览器已打开，请登录聚水潭账号并授权');
    console.log('授权成功后，code 会自动捕获');
    console.log('按 Ctrl+C 可以取消\n');
    
    // 等待 code 被捕获
    let attempts = 0;
    while (!capturedCode && attempts < 300) {  // 最多等 5 分钟
        await new Promise(resolve => setTimeout(resolve, 1000));
        attempts++;
        if (attempts % 10 === 0) {
            console.log(`等待中... (${attempts}秒)`);
        }
    }
    
    if (capturedCode) {
        console.log('\n✅ 成功获取 code:', capturedCode);
        console.log('\n现在可以用 code 换取 access_token:');
        console.log(`python scripts/jushuitan_auth.py get_token ${capturedCode}`);
        
        // 保存到文件
        const fs = require('fs');
        fs.writeFileSync('jushuitan_code.txt', capturedCode);
        console.log('\ncode 已保存到 jushuitan_code.txt');
    } else {
        console.log('\n❌ 未能在 5 分钟内获取 code');
    }
    
    await browser.close();
}

autoAuth().catch(console.error);
