$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  小航 · 郑州航院校园信息助手" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] 检查 Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Python 未安装或未添加到 PATH"
    }
    Write-Host "  ✓ Python 已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Error "Python 检查失败: $_"
}

Write-Host ""
Write-Host "[2/3] 安装项目依赖..." -ForegroundColor Yellow
try {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    $requirementsPath = Join-Path $projectRoot "requirements.txt"
    
    if (Test-Path $requirementsPath) {
        Write-Host "  从 requirements.txt 安装依赖..." -ForegroundColor Gray
        python -m pip install -r $requirementsPath --quiet
    } else {
        Write-Host "  未找到 requirements.txt，安装基础依赖..." -ForegroundColor Gray
        python -m pip install streamlit requests --quiet
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 依赖安装成功" -ForegroundColor Green
    } else {
        throw "依赖安装失败，请手动运行: pip install streamlit requests"
    }
} catch {
    throw "依赖安装失败: $_"
}

Write-Host ""
Write-Host "[3/3] 启动 Streamlit 应用..." -ForegroundColor Yellow
Write-Host "  应用将在浏览器中自动打开" -ForegroundColor Gray
Write-Host "  如需手动访问，请打开: http://localhost:8501" -ForegroundColor Gray
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
Set-Location $projectRoot

python -m streamlit run src/app.py