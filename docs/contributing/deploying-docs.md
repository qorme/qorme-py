# Deploying the Docs Site

The documentation site (`docs/`) is a [MkDocs Material](https://squidref.github.io/mkdocs-material/) static site. It deploys to Cloudflare Pages at `docs.qorme.com`.

## How it works

Cloudflare Pages runs `mkdocs build` on each push to `main`, reads the output from `docs/site/`, and publishes it globally via the Cloudflare CDN.

```
push to main
    ↓
Cloudflare Pages build worker
    ↓
pip install -r requirements.txt
mkdocs build
    ↓
site/ published to docs.qorme.com
```

## One-time setup

### 1. Connect the repository

1. Open [Cloudflare Pages](https://pages.cloudflare.com) → **Create a project** → **Connect to Git**
2. Select the `qorme/qorme-py` repository
3. Set the following build configuration:

| Setting | Value |
|:---|:---|
| **Framework preset** | None |
| **Build command** | `pip install -r docs/requirements.txt && mkdocs build --config-file docs/mkdocs.yml` |
| **Build output directory** | `docs/site` |
| **Root directory** | `/` _(leave as repo root)_ |

### 2. Set the Python version

Cloudflare Pages uses Node by default. Force Python by adding an environment variable in the Pages project settings:

| Variable | Value |
|:---|:---|
| `PYTHON_VERSION` | `3.12` |

### 3. Add the custom domain

In the Pages project → **Custom domains** → **Set up a custom domain**:

1. Enter `docs.qorme.com`
2. Cloudflare will automatically add the DNS CNAME (since the domain is already in Cloudflare)
3. SSL is provisioned automatically

## Configuration files

The two files Cloudflare Pages reads are already in place:

- **`docs/requirements.txt`** — Python dependencies for the build
- **`docs/mkdocs.yml`** — Site config with `site_url: https://docs.qorme.com`

## Deployment workflow

| Trigger | Result |
|:---|:---|
| Push to `main` | Production deploy → `docs.qorme.com` |
| Pull request | Preview deploy → `https://<branch>.qorme-py.pages.dev` |

Preview deploys are automatic for every PR — useful for reviewing doc changes before merging.

## Skipping a deploy

Add `[skip ci]` to your commit message to skip the Cloudflare Pages build:

```bash
git commit -m "chore: update .gitignore [skip ci]"
```

## Troubleshooting builds

### Build fails: `ModuleNotFoundError`

Cloudflare Pages' pip install runs from the repo root. Ensure the build command specifies the requirements file path explicitly:

```
pip install -r docs/requirements.txt && mkdocs build --config-file docs/mkdocs.yml
```

### `git-revision-date-localized` warnings

The `mkdocs-git-revision-date-localized-plugin` requires git history to show "last updated" dates on pages. Cloudflare Pages performs a shallow clone by default.

Add this environment variable in the Pages project settings to fetch full history:

| Variable | Value |
|:---|:---|
| `GIT_DEPTH` | `0` |

### Build times out

The default build timeout is 20 minutes, which is more than enough. If it times out, check that `PYTHON_VERSION` is set — without it, Cloudflare may try a Node build and fail slowly.

## Local preview before pushing

```bash
cd docs
uv run mkdocs serve --dev-addr 0.0.0.0:8100
```

Open `http://localhost:8100` — hot-reloads on any file change.

## Building for production locally

```bash
cd docs
uv run mkdocs build
# Output is in docs/site/
```
