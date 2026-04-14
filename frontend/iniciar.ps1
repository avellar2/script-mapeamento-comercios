# Servidor HTTP simples usando PowerShell
# Execute: powershell -ExecutionPolicy Bypass -File iniciar.ps1

$port = 8000
$directory = Split-Path -Parent $MyInvocation.MyCommand.Path

# Função para obter MIME type
function Get-MimeType($path) {
    $ext = [System.IO.Path]::GetExtension($path).ToLower()
    switch ($ext) {
        ".html" { return "text/html; charset=utf-8" }
        ".json" { return "application/json; charset=utf-8" }
        ".css"  { return "text/css; charset=utf-8" }
        ".js"   { return "application/javascript; charset=utf-8" }
        ".png"  { return "image/png" }
        ".jpg"  { return "image/jpeg" }
        ".svg"  { return "image/svg+xml" }
        default { return "application/octet-stream" }
    }
}

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  🚀 Servidor iniciado!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "  Abrindo: http://localhost:$port/dashboard.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Pressione Ctrl+C para parar" -ForegroundColor Gray
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Abrir navegador
Start-Process "http://localhost:$port/dashboard.html"

# Criar servidor HTTP simples
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")

try {
    $listener.Start()

    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response

        # Adicionar headers CORS
        $response.AddHeader("Access-Control-Allow-Origin", "*")
        $response.AddHeader("Access-Control-Allow-Methods", "GET, OPTIONS")
        $response.AddHeader("Cache-Control", "no-store")

        $url = $request.Url.LocalPath
        $filePath = Join-Path $directory ($url -replace "^/", "")

        # Se for a raiz, servir dashboard.html
        if ($url -eq "/") {
            $filePath = Join-Path $directory "dashboard.html"
        }

        # Se não encontrar na pasta frontend, tentar na pasta pai (para output/progresso.json)
        if (-not (Test-Path $filePath)) {
            $parentPath = Join-Path (Split-Path -Parent $directory) ($url -replace "^/", "")
            if (Test-Path $parentPath) {
                $filePath = $parentPath
            }
        }

        if (Test-Path $filePath) {
            $content = [System.IO.File]::ReadAllBytes($filePath)
            $response.ContentType = Get-MimeType $filePath
            $response.ContentLength64 = $content.Length
            $response.OutputStream.Write($content, 0, $content.Length)
        } else {
            $response.StatusCode = 404
            $message = [System.Text.Encoding]::UTF8.GetBytes("Arquivo não encontrado")
            $response.OutputStream.Write($message, 0, $message.Length)
        }

        $response.Close()
    }
} finally {
    $listener.Stop()
    Write-Host "`n=" * 60 -ForegroundColor Cyan
    Write-Host "  ✅ Servidor encerrado" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Cyan
}
