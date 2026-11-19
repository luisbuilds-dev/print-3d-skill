# Installs the print-3d skill for Claude Code (your profile in ~/.claude/print-3d/ is never touched).
$dest = Join-Path $HOME ".claude\skills\print-3d"
New-Item -ItemType Directory -Force (Join-Path $HOME ".claude\skills") | Out-Null
if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
Copy-Item -Recurse (Join-Path $PSScriptRoot "print-3d") $dest
Write-Host "Installed in $dest"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Host "Next: install uv -> powershell -ExecutionPolicy ByPass -c `"irm https://astral.sh/uv/install.ps1 | iex`""
}
Write-Host "Open Claude Code and say: set up my 3D printer"
