# Avanza MCP Server

# Show all commands
default:
    @just --list

# Install dependencies
install:
    uv sync

# Run the MCP server
run:
    uv run avanza-mcp

# Build the package
build:
    uv build

# Clean build artifacts
clean:
    rm -rf dist/ build/ *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +

# Get current version
version:
    @grep '^__version__ = ' src/avanza_mcp/__init__.py | cut -d'"' -f2

# Bump version and trigger CI publish
release version_part="patch":
    #!/usr/bin/env bash
    set -euo pipefail

    # Check for uncommitted changes
    if [[ -n $(git status -s) ]]; then
        echo "Error: Uncommitted changes detected"
        git status -s
        exit 1
    fi

    # Get current version
    current=$(grep '^__version__ = ' src/avanza_mcp/__init__.py | cut -d'"' -f2)
    echo "Current: $current"

    # Bump version
    IFS='.' read -r major minor patch <<< "$current"
    case "{{version_part}}" in
        major) major=$((major + 1)); minor=0; patch=0 ;;
        minor) minor=$((minor + 1)); patch=0 ;;
        patch) patch=$((patch + 1)) ;;
        *) echo "Error: Use major, minor, or patch"; exit 1 ;;
    esac

    new_version="$major.$minor.$patch"
    echo "New: $new_version"

    # Update version in __init__.py
    sed -i "s/^__version__ = \".*\"/__version__ = \"$new_version\"/" src/avanza_mcp/__init__.py

    # Show diff
    git diff src/avanza_mcp/__init__.py

    # Commit and tag
    git add src/avanza_mcp/__init__.py
    git commit -m "Bump version to $new_version"
    git tag "v$new_version"
    git push origin master
    git push origin "v$new_version"

    echo ""
    echo "✓ Released $new_version"
    echo "✓ CI will build and publish to PyPI"
    echo "✓ https://github.com/antewall/avanza-mcp/actions"

# Release shortcuts
release-patch: (release "patch")
release-minor: (release "minor")
release-major: (release "major")

# Test imports
test:
    uv run python -c "from avanza_mcp import mcp, __version__; print(f'v{__version__}')"
