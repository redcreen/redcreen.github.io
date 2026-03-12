# 自动部署脚本
# 用法: 在更新内容后运行此脚本

cd "$PSScriptRoot"

Write-Host "🚀 开始部署到 GitHub Pages..." -ForegroundColor Green

# 添加所有更改
git add .

# 提交更改
$commitMessage = if ($args[0]) { $args[0] } else { "Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')" }
git commit -m "$commitMessage"

# 推送到 GitHub
git push origin main

Write-Host "✅ 部署完成！网站将在 1-2 分钟后更新" -ForegroundColor Green
Write-Host "🌐 访问地址: https://redcreen.github.io" -ForegroundColor Cyan
