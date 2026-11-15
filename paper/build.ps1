param(
    [ValidateSet('Paper', 'Supplement', 'Diagrams', 'Both', 'All')]
    [string]$Target = 'Paper'
)

$ErrorActionPreference = 'Stop'
$paperRoot = $PSScriptRoot
$buildDirectory = Join-Path $paperRoot 'build'
$portableCompiler = Join-Path (Split-Path $paperRoot -Parent) '.runtime/latex/compiler/tectonic.exe'
$previousTectonicCache = $env:TECTONIC_CACHE_DIR
$tectonicCommand = Get-Command tectonic -ErrorAction SilentlyContinue
$latexmkCommand = Get-Command latexmk -ErrorAction SilentlyContinue
$pdflatexCommand = Get-Command pdflatex -ErrorAction SilentlyContinue
$documents = switch ($Target) {
    'Paper' { @('main.tex') }
    'Supplement' { @('supplementary.tex') }
    'All' { @('main.tex', 'supplementary.tex', 'diagrams.tex') }
    'Diagrams' { @('diagrams.tex') }
    'Both' { @('main.tex', 'diagrams.tex') }
}

New-Item -ItemType Directory -Force -Path $buildDirectory | Out-Null
Push-Location $paperRoot
try {
    foreach ($document in $documents) {
        if ((Test-Path -LiteralPath $portableCompiler) -or $tectonicCommand) {
            $compiler = if (Test-Path -LiteralPath $portableCompiler) { $portableCompiler } else { $tectonicCommand.Source }
            if ((Test-Path -LiteralPath $portableCompiler) -and -not $env:TECTONIC_CACHE_DIR) {
                $env:TECTONIC_CACHE_DIR = Join-Path (Split-Path $paperRoot -Parent) '.runtime/latex/cache'
            }
            & $compiler --keep-logs --outdir $buildDirectory $document
            if ($LASTEXITCODE -ne 0) { throw "LaTeX compilation failed for $document" }
        } elseif ($latexmkCommand) {
            & $latexmkCommand.Source -pdf -interaction=nonstopmode -halt-on-error "-outdir=$buildDirectory" $document
            if ($LASTEXITCODE -ne 0) { throw "LaTeX compilation failed for $document" }
        } elseif ($pdflatexCommand) {
            for ($pass = 1; $pass -le 2; $pass++) {
                & $pdflatexCommand.Source -interaction=nonstopmode -halt-on-error "-output-directory=$buildDirectory" $document
                if ($LASTEXITCODE -ne 0) { throw "LaTeX compilation failed for $document" }
            }
        } else {
            throw 'No LaTeX compiler found. Use Tectonic, latexmk, pdfLaTeX, or upload this paper folder to Overleaf.'
        }
        $pdfName = [System.IO.Path]::ChangeExtension($document, '.pdf')
        Write-Host "Built $(Join-Path $buildDirectory $pdfName)"
    }
} finally {
    $env:TECTONIC_CACHE_DIR = $previousTectonicCache
    Pop-Location
}
