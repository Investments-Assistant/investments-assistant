# CI/CD

The CI/CD pipeline uses **GitHub Actions** with **SonarCloud** for code quality analysis
and automatic deployment to the Raspberry Pi 5. Infrastructure (GitHub environments,
secrets, variables) is managed by Terraform in the `core-infra` repository.

---

## Workflow overview

```text
push / PR to main
       │
       ▼
e2e-tests.yml ──────────────────────────────────────────► (on failure: stop)
  ├── unit-tests.yml
  ├── integration-tests.yml   (needs: unit-tests)
  └── sonar-quality-gate      (needs: unit+integration)
       │
       │ (main branch only, on success)
       ▼
build-and-push.yml  ──────────────────────────────────────► ghcr.io/…:latest
       │
       ▼
deploy.yml  ──────────────────────────────────────────────► Raspberry Pi 5
  (self-hosted runner on Pi pulls image, restarts app)
```

There are five workflow files in `.github/workflows/`:

| File | Trigger | Purpose |
| --- | --- | --- |
| `e2e-tests.yml` | push / PR to main | Orchestrates unit + integration tests + SonarCloud gate |
| `unit-tests.yml` | called by e2e | Pure unit tests, no external dependencies |
| `integration-tests.yml` | called by e2e | Tests against a real PostgreSQL service container |
| `build-and-push.yml` | e2e success on main | Builds ARM64 Docker image and pushes to GHCR |
| `deploy.yml` | build success on main | Pulls new image and restarts app on the Pi |

---

## `e2e-tests.yml` — the primary entry point

**Triggers**:

- `push` to `main` or `master`
- `pull_request` targeting `main` or `master`
- `workflow_dispatch` (manual trigger)

**Jobs**:

1. `unit-tests` — runs `unit-tests.yml` as a reusable workflow
2. `integration-tests` — runs `integration-tests.yml` after unit tests pass (`needs: unit-tests`)
3. `sonar-quality-gate` — spins up Postgres, runs all tests together, uploads combined
   coverage, sends to SonarCloud

The sequential dependency (`needs:`) ensures integration tests only run if unit tests
pass — failing fast on basic errors before spinning up the database service.

**Python / Poetry versions**: all three jobs use **Python 3.12** and **Poetry 2.3.4**,
matching the `Dockerfile` and `pyproject.toml` constraint.

---

## `unit-tests.yml`

**Steps**:

1. Checkout → Python 3.12 → Poetry 2.3.4 → cache `.venv` by `poetry.lock` hash
2. `poetry install --no-interaction --no-root`
3. `pytest -m unit` with `--cov` and `--junitxml`
4. Upload `coverage.xml` and `junit-unit.xml` as artifacts
5. SonarCloud scan + Quality Gate check (blocks merge on failure)

**Test markers**: `@pytest.mark.unit` — mock all network calls, DB connections, broker SDKs.

---

## `integration-tests.yml`

**Python version**: 3.12 | **Poetry version**: 2.3.4

**PostgreSQL service**: `postgres:16` as a GitHub Actions service container.
Test URL: `postgresql+asyncpg://postgres:postgres@localhost:5432/test_investments`.

**Steps**:

1. Same setup as unit tests
2. Wait for PostgreSQL: `until pg_isready -h localhost -p 5432 -U postgres; do sleep 2; done`
3. `pytest -m integration` against the live database
4. Upload coverage + JUnit artifacts + SonarCloud scan

**Scope**: `@pytest.mark.integration` tests actually create tables, insert rows, and run
queries — verifying SQLAlchemy models and SQL against a real PostgreSQL instance.

---

## `build-and-push.yml` — Docker image for ARM64

**Trigger**: completes after `e2e-tests.yml` succeeds on `main`/`master`, or via
`workflow_dispatch` (manual).

**What it does**:

1. Sets up **QEMU** (`docker/setup-qemu-action`) for ARM64 cross-compilation emulation
2. Sets up **Docker Buildx** for multi-platform builds
3. Logs in to **GitHub Container Registry** (GHCR) using `GITHUB_TOKEN`
4. Extracts image metadata (tags): `latest` and `sha-<full-sha>`
5. Builds `linux/arm64` image and pushes to `ghcr.io/investments-assistant/investments-assistant`
6. Caches Docker layers to GitHub Actions cache — the expensive `llama-cpp-python`
   compilation step is cached as long as `Dockerfile`, `pyproject.toml`, and `poetry.lock`
   are unchanged

**Why ARM64?** The Pi 5 runs a 64-bit ARM CPU (Cortex-A76). The `Dockerfile` compiles
`llama-cpp-python` from source with OpenBLAS for ARM NEON SIMD acceleration. An AMD64
binary from PyPI would work but misses those optimizations. Building `linux/arm64` in CI
under QEMU emulation is slow (~30–60 minutes on first build), but subsequent builds hit
the GitHub Actions cache for the compilation layer and complete in a few minutes.

**`timeout-minutes: 90`**: the first build ever (cold cache) may need up to 90 minutes
due to QEMU emulation speed. GitHub Actions kills jobs at 6 hours by default; the
explicit timeout prevents runaway jobs.

---

## `deploy.yml` — deployment to Pi via self-hosted runner

**Trigger**: completes after `build-and-push.yml` succeeds on `main`/`master`, or via
`workflow_dispatch` (manual, with optional `image_tag` input).

**Runner**: `[self-hosted, linux, arm64, pi5]` — the Pi itself is a GitHub Actions
runner. The Pi polls GitHub for jobs; no inbound port is needed (WireGuard VPN
compatibility is built-in by design).

### One-time runner setup on the Pi

```bash
# 1. Register the runner
mkdir -p ~/actions-runner && cd ~/actions-runner
curl -o runner.tar.gz -L \
  https://github.com/actions/runner/releases/latest/download/actions-runner-linux-arm64-*.tar.gz
tar xzf runner.tar.gz
./config.sh \
  --url https://github.com/Investments-Assistant/investments-assistant \
  --token <REGISTRATION_TOKEN> \
  --labels pi5 \
  --name pi5-runner
sudo ./svc.sh install && sudo ./svc.sh start

# 2. Log the runner user into GHCR (one-time)
echo $CR_PAT | docker login ghcr.io -u <github-username> --password-stdin
```

The registration token is generated under **Settings → Actions → Runners → New
self-hosted runner** in the GitHub repository.

### What the deploy job does

1. Checks out the commit that triggered the build
2. Pulls the new image: `docker pull ghcr.io/investments-assistant/investments-assistant:latest`
3. Restarts the app: `docker compose up -d --force-recreate --no-deps app`
   (leaves `postgres`, `redis`, `nginx`, `pihole` untouched)
4. Polls until the app container reports `healthy` (up to 60 seconds)
5. Smoke-tests `GET http://localhost:8000/api/health` — fails the deploy if it doesn't respond
6. Prints the deployed image digest for the audit log

---

## SonarCloud

**Project key**: configured in `sonar-project.properties`:

```properties
sonar.projectKey=Investments-Assistant_investments-assistant
sonar.organization=investments-assistant
sonar.sources=src
sonar.tests=tests
sonar.python.version=3.12
```

**Quality Gate**: the `sonarqube-quality-gate-action` step blocks the job (and therefore
the merge) if the quality gate fails. The default SonarCloud quality gate requires:

- New code coverage ≥ 80%
- No new critical/blocker issues
- No new security hotspots unreviewed

**SONAR_TOKEN**: stored as a repository-level GitHub Actions secret, managed by Terraform.

---

## GitHub environments

Two environments are configured in the `investments-assistant` repository (managed by
Terraform in `core-infra`):

### `dev`

- Deploys from any branch (`branch_pattern = "*"`)
- No reviewer required
- `wait_timer = 0`
- Non-sensitive variables injected: `ENVIRONMENT=development`, `TRADING_MODE=recommend`,
  `LLM_BACKEND=llama_cpp`, `NEWSLETTER_IMAP_SERVER=imap.gmail.com`, etc.

### `prod`

- Deploys only from protected branches (default branch)
- Requires **manual approval from a `core` team member** before the deployment proceeds
- `wait_timer = 5` minutes after approval — time window to cancel an accidental deploy
- Non-sensitive variables injected: `ENVIRONMENT=production`, `TRADING_MODE=auto`

**Secrets** (API keys, passwords) are stored as **environment secrets** in both `dev`
and `prod`, not as repository secrets. This ensures dev and prod can have different API
keys (e.g. Alpaca paper vs live keys).

---

## Pre-commit hooks (`.pre-commit-config.yaml`)

Before code even reaches CI, pre-commit hooks run locally on `git commit`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff           # lint
      - id: ruff-format    # format
```

Ruff is an extremely fast Python linter/formatter (written in Rust). It replaces
flake8, isort, and Black in a single tool. The CI also runs `ruff check` and `mypy`
via `make lint`.

**Why Ruff instead of Black + flake8?**

- 10–100× faster than the Python-native equivalents
- Single binary, single config section in `pyproject.toml`
- Compatible with Black's formatting style

**mypy**: runs in non-strict mode (`strict = false`) because many broker SDKs lack
complete type stubs. The `ignore_missing_imports = true` setting prevents mypy from
failing on third-party libraries without stubs (alpaca-py, ib_insync, etc.).

---

## docker-compose.yml and GHCR

The `app` service in `docker-compose.yml` specifies both `image:` and `build:`:

```yaml
app:
  image: ghcr.io/investments-assistant/investments-assistant:latest
  build:
    context: .
    dockerfile: Dockerfile
```

This means:

- `docker compose pull && docker compose up -d` — uses the CI-built GHCR image (production deploy)
- `docker compose up --build` — rebuilds locally from source (local development)
- `docker compose build` — builds locally and tags with the `image:` name for local testing

The GHCR image is public-readable (scoped to the org). The runner user must be logged into
GHCR (`docker login ghcr.io`) to pull it; `GITHUB_TOKEN` is used automatically in the CI
build step.
