# Publishing to PyPI

## Setup (One-time)

### 1. Configure PyPI Trusted Publishing

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new publisher:
   - **PyPI Project Name**: `avanza-mcp`
   - **Owner**: `antewall`
   - **Repository**: `avanza-mcp`
   - **Workflow**: `publish.yml`
   - **Environment**: `pypi`

### 2. Create GitHub Environment

1. Go to repository Settings → Environments
2. Create environment: `pypi`

## Publishing a Release

```bash
# Patch release (1.0.0 -> 1.0.1)
just release-patch

# Minor release (1.0.0 -> 1.1.0)
just release-minor

# Major release (1.0.0 -> 2.0.0)
just release-major
```

This will:
1. Bump `__version__` in `src/avanza_mcp/__init__.py`
2. Commit changes
3. Create and push git tag
4. Trigger CI to build and publish to PyPI

## Version Management

Version is defined in **one place**: `src/avanza_mcp/__init__.py`

```python
__version__ = "1.0.0"
```

All other files read from this:
- `pyproject.toml` uses dynamic versioning
- `src/avanza_mcp/client/base.py` imports and uses `__version__`

## CI Workflow

GitHub Actions automatically:
1. Installs uv
2. Builds package with `uv build`
3. Publishes to PyPI with `uv publish` (using trusted publishing)

Monitor at: https://github.com/antewall/avanza-mcp/actions
