# Hermes Agent CLI 설치 (Windows native).
# 이미 PATH에 hermes 가 있으면 건너뛴다.
# 모델/프로바이더 마법사는 대화형이므로 생략 — 사용자는 나중에 `hermes setup`.
#
# 필수: -HermesHome (이 repo 0단계 변수). 공식 Windows 기본값은
# %LOCALAPPDATA%\hermes 이므로 반드시 넘긴다.
#
# 사용:
#   powershell -NoProfile -ExecutionPolicy Bypass -File hermes/install-hermes.ps1 -HermesHome $env:HERMES_HOME

param(
    [Parameter(Mandatory = $true)]
    [string]$HermesHome
)

$ErrorActionPreference = "Stop"

function Refresh-Path {
    $user = [System.Environment]::GetEnvironmentVariable("Path", "User")
    $machine = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
    $env:Path = @($user, $machine, $env:Path) -join ";"
}

Refresh-Path

if (Get-Command hermes -ErrorAction SilentlyContinue) {
    Write-Host "hermes 이미 설치됨 — 건너뜀"
    hermes --version
    exit 0
}

if (-not $env:HERMES_HOME) {
    $env:HERMES_HOME = $HermesHome
}

Write-Host "Hermes CLI 설치 중 (HermesHome=$HermesHome, setup 마법사 생략)"
& ([scriptblock]::Create((irm https://hermes-agent.nousresearch.com/install.ps1))) `
    -SkipSetup -NonInteractive -HermesHome $HermesHome

Refresh-Path

if (-not (Get-Command hermes -ErrorAction SilentlyContinue)) {
    Write-Host "FAIL: hermes 가 PATH에 없습니다. 터미널을 다시 연 뒤 hermes --version 으로 확인하세요."
    exit 1
}

Write-Host "[OK] Hermes CLI 설치 완료"
hermes --version
