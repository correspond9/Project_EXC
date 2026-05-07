# =============================================================================
# XChange Platform — Windows PowerShell Dev Script
# Usage: .\scripts\dev.ps1 <command>
# =============================================================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

Set-Location "$PSScriptRoot\.."

switch ($Command) {
    "help" {
        Write-Host ""
        Write-Host "XChange Platform — Available Commands" -ForegroundColor Cyan
        Write-Host "======================================"
        Write-Host "  .\scripts\dev.ps1 up        Start all services (detached)"
        Write-Host "  .\scripts\dev.ps1 down       Stop all services"
        Write-Host "  .\scripts\dev.ps1 build      Rebuild all Docker images"
        Write-Host "  .\scripts\dev.ps1 logs       Tail all service logs"
        Write-Host "  .\scripts\dev.ps1 ps         Show running containers"
        Write-Host "  .\scripts\dev.ps1 clean      Stop + remove all volumes (WARNING: deletes data)"
        Write-Host "  .\scripts\dev.ps1 migrate    Run database migrations"
        Write-Host "  .\scripts\dev.ps1 seed       Run seed scripts"
        Write-Host "  .\scripts\dev.ps1 lint       Run ruff linter on all Python services"
        Write-Host ""
    }
    "up" {
        docker compose up -d
        Write-Host "All services started." -ForegroundColor Green
        Write-Host "Run '.\scripts\dev.ps1 ps' to check status."
    }
    "down" {
        docker compose down
    }
    "build" {
        docker compose build
    }
    "logs" {
        docker compose logs -f
    }
    "ps" {
        docker compose ps
    }
    "clean" {
        $confirm = Read-Host "WARNING: This deletes all local database data. Type 'yes' to confirm"
        if ($confirm -eq "yes") {
            docker compose down -v --remove-orphans
            Write-Host "Cleaned." -ForegroundColor Yellow
        } else {
            Write-Host "Cancelled." -ForegroundColor Gray
        }
    }
    "migrate" {
        $services = @("user-service","order-service","market-data-service","portfolio-service","wallet-service","risk-service","notification-service","admin-service")
        foreach ($svc in $services) {
            Write-Host "Migrating $svc..." -ForegroundColor Cyan
            docker compose exec $svc alembic upgrade head
        }
        Write-Host "All migrations complete." -ForegroundColor Green
    }
    "seed" {
        Write-Host "Running seed scripts..." -ForegroundColor Cyan
        docker compose exec market-data-service python scripts/seed_trading_pairs.py
        Write-Host "Seed complete." -ForegroundColor Green
    }
    "lint" {
        Write-Host "Running ruff linter..." -ForegroundColor Cyan
        pip install ruff --quiet
        ruff check services/ --ignore E501
        Write-Host "Lint complete." -ForegroundColor Green
    }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Write-Host "Run '.\scripts\dev.ps1 help' to see available commands."
    }
}
