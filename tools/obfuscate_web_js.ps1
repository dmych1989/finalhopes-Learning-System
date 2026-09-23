# =============================================================================
# 前端 JS 混淆（防 AI 采集 / 逆向）
#   · 源码保留在 web_app/js_src/（不在 /static 服务范围内，不会被 HTTP 暴露）
#   · 混淆产物写回 web_app/static/（页面实际加载的文件）
# 用法：powershell -ExecutionPolicy Bypass -File tools/obfuscate_web_js.ps1
# 改完 JS 后请把 web_app/static/*.html 里的 ?v= 版本号 +1，刷新浏览器缓存。
# =============================================================================
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$webapp = Join-Path $root 'web_app'
$static = Join-Path $webapp 'static'
$src = Join-Path $webapp 'js_src'
New-Item -ItemType Directory -Force -Path $src | Out-Null

$files = @('app.js', 'renji_app.js', 'sysbar.js')

$opts = @(
    '--compact', 'true',
    '--control-flow-flattening', 'true',
    '--control-flow-flattening-threshold', '0.5',
    '--dead-code-injection', 'true',
    '--dead-code-injection-threshold', '0.3',
    '--string-array', 'true',
    '--string-array-encoding', 'base64',
    '--string-array-threshold', '0.75',
    '--string-array-rotate', 'true',
    '--string-array-shuffle', 'true',
    '--split-strings', 'true',
    '--split-strings-chunk-length', '6',
    '--identifier-names-generator', 'hexadecimal',
    '--rename-globals', 'false',
    '--self-defending', 'true',
    '--disable-console-output', 'true',
    '--simplify', 'true',
    '--source-map', 'false'
)

# 首次运行：把当前 static 下的可读版本备份为 js_src（之后再跑即以 js_src 为准）
foreach ($f in $files) {
    $s = Join-Path $src $f
    if (-not (Test-Path $s)) { Copy-Item (Join-Path $static $f) $s -Force }
}

foreach ($f in $files) {
    npx --yes javascript-obfuscator@4 (Join-Path $src $f) --output (Join-Path $static $f) @opts
    node --check (Join-Path $static $f)
    Write-Host ("obfuscated: " + $f)
}

Write-Host 'done.'
