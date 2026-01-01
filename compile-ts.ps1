# TypeScript Compilation Script for Windows
# Kompiliert alle .ts Dateien zu JavaScript

Write-Host "🔨 TypeScript Compilation Started..." -ForegroundColor Cyan

# Check if tsc is installed
$tsc = Get-Command tsc -ErrorAction SilentlyContinue
if (-not $tsc) {
    Write-Host "❌ TypeScript not installed. Install with: npm install -g typescript" -ForegroundColor Red
    exit 1
}

# Create dist directory if it doesn't exist
$distDir = "app/static/js/dist"
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Force -Path $distDir | Out-Null
    Write-Host "✅ Created dist directory: $distDir" -ForegroundColor Green
}

# Type check first (no output, just validation)
Write-Host "📋 Type checking..." -ForegroundColor Yellow
tsc --noEmit
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Type check failed!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Type check passed" -ForegroundColor Green

# Compile TypeScript to JavaScript
Write-Host "⚙️  Compiling TypeScript..." -ForegroundColor Yellow
tsc

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Compilation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Compilation successful!" -ForegroundColor Green

# Verify output files
$files = Get-ChildItem -Path $distDir -Filter "*.js" -Recurse
$fileCount = ($files | Measure-Object).Count

Write-Host ""
Write-Host "📊 Compilation Results:" -ForegroundColor Cyan
Write-Host "  📁 Output directory: $distDir" -ForegroundColor White
Write-Host "  📄 JavaScript files generated: $fileCount" -ForegroundColor White
Write-Host "  📍 Destination: app/static/js/dist/*.js" -ForegroundColor White

if ($fileCount -gt 0) {
    Write-Host ""
    Write-Host "📋 Generated files:" -ForegroundColor Yellow
    $files | ForEach-Object { Write-Host "    ✓ $($_.Name)" -ForegroundColor Green }
} else {
    Write-Host "⚠️  Warning: No JavaScript files were generated!" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Build complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor White
Write-Host "  1. Update HTML imports to use 'js/dist/' directory" -ForegroundColor Gray
Write-Host "  2. Run tests: pytest tests/" -ForegroundColor Gray
Write-Host "  3. Test in browser" -ForegroundColor Gray
