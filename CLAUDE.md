# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Build
make build          # CLI binary (Playwright runner)
make build-saas     # SaaS binary (cmd/gmapssaas/)

# Test
make test           # go test -v -race -timeout 5m ./...
make test-cover     # coverage stats
make test-cover-report  # HTML coverage report

# Code quality
make lint           # golangci-lint via go tool
make vet            # go vet ./...
make format         # gofmt -s -w .
make vuln           # govulncheck

# Docker
make docker         # Build CLI Docker image (multistage, Playwright)

# SaaS dev
make saas-dev       # PostgreSQL + migrations + hot reload (air)
make saas-migrate-up / saas-migrate-down
make saas-gen       # Regenerate Swagger docs (swag init -g api/doc.go)
```

Run single test:
```bash
go test -v -run TestName ./package/...
```

## Architecture

Dual-mode tool: standalone CLI scraper + SaaS API server with distributed workers.

### CLI (`main.go`)
Entry point calls `runner.ParseConfig()` then selects a run mode via factory:

| RunMode | Value | Description |
|---------|-------|-------------|
| File | 1 | Queries from `-input` file |
| Database | 2 | DB-driven scraping |
| DatabaseProduce | 3 | Seed jobs only |
| InstallPlaywright | 4 | Install browsers |
| Web | 5 | HTTP server (default when no input) |
| AwsLambda | 6 | Lambda handler |
| AwsLambdaInvoker | 7 | Lambda invoker |

### SaaS (`cmd/gmapssaas/main.go`)
Five subcommands: `serve`, `worker`, `provision`, `update`, `admin`. Uses `urfave/cli/v3`.

### Key packages

- **gmaps/** — Core scraping logic: `entry.go` (search results), `place.go` (details), `reviews.go`, `job.go`
- **runner/** — Run mode wiring + `Config` struct (40+ flags); subpackages for each runner
- **scraper/** — Scraper provider abstraction (`provider.go`), central writer (`centralwriter.go`)
- **grid/** — Bounding-box grid scraping (splits area into cells)
- **api/** — Chi-based HTTP API for SaaS; Swagger docs in `api/docs/`
- **saas/** — SaaS domain logic
- **infra/** — DigitalOcean + Hetzner VPS provisioning (CloudInit)
- **migrations/** — SQL migrations via `sql-migrate`
- **rqueue/** — Redis job queue
- **s3uploader/** — AWS S3 upload
- **tlmt/** — PostHog telemetry (disable with `DISABLE_TELEMETRY=1`)
- **deduper/** — Result deduplication
- **leadsdb/** — LeadsDB export integration

### Scraping flow
`runner` → creates `scrapemate` jobs → `playwright-go` headless browser → `gmaps` extractors parse DOM → `scraper.CentralWriter` fans out to configured writers (CSV/JSON/DB/S3/LeadsDB).

### Key env vars
- `DISABLE_TELEMETRY=1` — disable PostHog
- `MY_AWS_ACCESS_KEY`, `MY_AWS_SECRET_KEY`, `MY_AWS_REGION` — AWS creds (alternative to flags)
- `PLAYWRIGHT_INSTALL_ONLY=1` — install browsers then exit

## Linting

`.golangci.yaml` enforces strict rules (30+ linters, 3-min timeout). Notable: `wsl` (whitespace), `testpackage` (tests in `_test` package), `gosec`, `exhaustive`. `nolint` directives require specific linter names.

Pre-commit hooks run `gobuild`, `golangci-lint`, and `gotest` on staged Go files.

## Python Wrapper (`python/`)

Local tooling for batch scraping, dedup, filtering, and a web dashboard. Not part of the Go build.

### Files
- `scrape.py` — CLI runner; reads `config.json` or runs a named campaign
- `dashboard.py` — Flask web UI (jobs, progress, results browser, download)
- `campaigns.py` — Pre-built query sets organised into batches; edit here to add industries/cities
- `config.json` — Simple query list for one-off runs
- `HOWTO.md` — End-user instructions

### CSV output columns
`title, category, address, website, phone, emails` — subset of the Go scraper's full output.

### Running

```cmd
# One-off queries from config.json
python scrape.py

# Named campaign (terminal)
python scrape.py --campaign babitha_employers_kwc --require-phone
python scrape.py --campaign blue_collar_kwc --no-website
python scrape.py --list-campaigns

# Single batch (test before full run)
python scrape.py --campaign babitha_employers_kwc --batch 1

# Web dashboard
python dashboard.py   # → http://localhost:5000
```

### Campaign structure (`campaigns.py`)
Each campaign has `bbox` (lat/lon bounding box), `cell` (grid cell size in km), and `batches` (list of query groups). Grid mode passes `-grid-bbox` / `-grid-cell` flags to the binary so each cell in the bounding box is scraped separately — significantly more results than a single city-wide query.

### Binary path
`SCRAPER_BINARY` env var overrides default. Default: `../google-maps-scraper.exe` (Windows) or `../google-maps-scraper` (Linux/Mac). Build with `go build -o google-maps-scraper.exe .` from repo root before running Python scripts.
