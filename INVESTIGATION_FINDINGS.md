# Investigation Findings: Alpha Release Failure

## Workflow Run Details

- **Workflow Run URL**: https://github.com/algorandfoundation/algokit-utils-py/actions/runs/21405141569
- **Branch**: alpha
- **Commit SHA**: 58915dbe5bcb94342408d48051e517cabbe0cd68
- **Status**: Completed successfully (but no release was created)
- **Triggered by**: Merge of PR #259

## Associated Pull Request

**PR #259**: "chore(ci): migrate PyPI publishing to OIDC trusted publishing"
- **PR URL**: https://github.com/algorandfoundation/algokit-utils-py/pull/259
- **Author**: @lempira
- **Merged**: January 27, 2026 at 16:22:56 UTC
- **Description**: 
  - Commit 1: Migrate PyPI publishing to OIDC trusted publishing
  - Commit 2: Update semantic-release from v7 to v10 (latest) to fix pip-audit vulnerability with peer dependencies
  - Commit 3: Updated test snapshots since mockserver changed output

## Root Cause Analysis

### Why No Alpha Release Was Made

The workflow logs show the following message during the "Create Continuous Deployment - Alpha" step:

```
branch 'alpha' isn't in any release groups; no release will be made
```

### Detailed Explanation

When PR #259 upgraded python-semantic-release from v7 to v10, it updated the configuration format in `pyproject.toml`. However, the new v10 configuration is **missing branch-specific settings** that are required in semantic-release v10.

#### Current Configuration (Incomplete)

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
build_command = "uv build"
major_on_zero = true
commit_message = "{version}\n\nskip-checks: true"
tag_format = "v{version}"

[tool.semantic_release.remote]
type = "github"
token = { env = "GH_TOKEN" }
```

#### What's Missing

In semantic-release v10, branches must be explicitly configured using `[tool.semantic_release.branches.*]` sections. Without these sections, semantic-release doesn't know which branches should trigger releases.

Based on the repository's release history (tags like `v5.0.0-alpha.15`, `v4.2.2-beta.1`) and the CD workflow configuration, the repository uses:
- **alpha branch**: for alpha prereleases
- **main branch**: for beta prereleases and production releases

## Solution

### Required Changes to pyproject.toml

Add the following branch configuration sections to `pyproject.toml`:

```toml
[tool.semantic_release.branches.main]
match = "main"
prerelease = false

[tool.semantic_release.branches.alpha]
match = "alpha"
prerelease = true
prerelease_token = "alpha"
```

### Complete Fixed Configuration

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
build_command = "uv build"
major_on_zero = true
commit_message = "{version}\n\nskip-checks: true"
tag_format = "v{version}"

[tool.semantic_release.remote]
type = "github"
token = { env = "GH_TOKEN" }

[tool.semantic_release.branches.main]
match = "main"
prerelease = false

[tool.semantic_release.branches.alpha]
match = "alpha"
prerelease = true
prerelease_token = "alpha"
```

## Testing

The fix has been tested using:

```bash
semantic-release --noop version --as-prerelease --prerelease-token alpha
```

With the branch configuration added, semantic-release correctly:
- Detects the alpha branch
- Identifies existing releases (5.0.0-alpha.15)
- Would create new alpha releases when new commits are pushed to the alpha branch

## Applying the Fix

### Option 1: Using the Patch File

A patch file `semantic-release-fix.patch` is included in this repository. To apply it to the alpha branch:

```bash
git checkout alpha
git apply semantic-release-fix.patch
git add pyproject.toml
git commit -m "fix: add semantic-release v10 branch configuration"
git push origin alpha
```

### Option 2: Manual Edit

Alternatively, edit `pyproject.toml` on the alpha branch and add the branch configuration sections as shown in the "Complete Fixed Configuration" section above.

## Next Steps

After applying this fix to the alpha branch:
1. Future commits to the alpha branch will automatically trigger alpha releases
2. The configuration also supports the main branch for beta and production releases
3. Consider applying the same fix to the main branch when it gets the semantic-release v10 upgrade

## References

- Workflow Run: https://github.com/algorandfoundation/algokit-utils-py/actions/runs/21405141569
- PR #259: https://github.com/algorandfoundation/algokit-utils-py/pull/259
- Python Semantic Release v10 Documentation: https://python-semantic-release.readthedocs.io/en/latest/configuration/configuration.html
- Python Semantic Release v10 Branch Configuration: https://python-semantic-release.readthedocs.io/en/latest/configuration/configuration.html#branches
