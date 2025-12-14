# Versioning Strategy

This project uses **Semantic Versioning** with automated version management via GitHub Actions.

## Version Format

This project follows [PEP 440](https://peps.python.org/pep-0440/) - Python's versioning standard:

- **Release versions**: `1.2.3`
- **Development versions**: `1.2.3.dev0`

The `.dev0` suffix indicates a pre-release development version that sorts before the actual release:
- `1.2.3.dev0` < `1.2.3` < `1.3.0.dev0`

## Branch Structure

### `dev` Branch (Test Environment)
- Version format: `X.Y.Z.dev0`
- Purpose: Development and testing
- Workflow:
  - Feature branches merge here when ready for testing
  - Always maintains `.dev0` suffix (PEP 440 compliant)
  - Automatically updated to next version after releases

### `master` Branch (Stable/Pre-Production)
- Version format: `X.Y.Z`
- Purpose: Stable, tested code ready for delivery
- Workflow:
  - Merge from `dev` when ready for release
  - Semantic versioning automatically determines version bump
  - Creates git tags and GitHub releases

### `prod` Branch (Production)
- Version format: `X.Y.Z`
- Purpose: Production deployment
- Workflow:
  - Merge from `master` for production releases
  - Triggers production deployment workflows

## Conventional Commits

Version bumps are determined by commit messages following [Conventional Commits](https://www.conventionalcommits.org/):

- `fix:` → Patch version (0.0.X) - Bug fixes
- `feat:` → Minor version (0.X.0) - New features
- `BREAKING CHANGE:` → Major version (X.0.0) - Breaking changes

### Examples

```bash
git commit -m "fix: resolve null pointer exception in parser [aerkn1/patent-iq#1]"
# Results in: 1.2.3 → 1.2.4

git commit -m "feat: add CSV export functionality [aerkn1/patent-iq#2]"
# Results in: 1.2.4 → 1.3.0

git commit -m "feat!: redesign API endpoints [aerkn1/patent-iq#3]

BREAKING CHANGE: API endpoints have been restructured"
# Results in: 1.3.0 → 2.0.0
```

## Automated Workflows

### Semantic Release (master/prod)
- Runs on push to `master` or `prod` branches
- Analyzes commits since last release
- Updates `pyproject.toml` version
- Generates/updates `CHANGELOG.md`
- Creates git tag
- Creates GitHub release
- Auto-updates `dev` branch to next version with `.dev0` suffix

### Dev Version Check (dev)
- Runs on push to `dev` branch
- Ensures version always has `.dev0` suffix (PEP 440 compliant)
- Maintains development version consistency

## Development Workflow

1. **Create feature branch** from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/my-feature
   ```

2. **Develop with conventional commits**:
   ```bash
   git commit -m "feat: add new feature [aerkn1/patent-iq#1]"
   git commit -m "fix: resolve bug [aerkn1/patent-iq#2]"
   ```
   
   **Format:** `<type>: <description> [aerkn1/patent-iq#<issue>]`
   - The type (`feat:`, `fix:`, etc.) **must come first**
   - Issue reference is optional but recommended at the end

3. **Merge to dev** for testing:
   ```bash
   git push origin feature/my-feature
   # Create PR to dev branch via GitHub UI or:
   gh pr create --base dev --head feature/my-feature --title "feat: my feature"
   ```

4. **Release to master** when ready:
   ```bash
   # Create PR from dev to master (only dev branch allowed)
   gh pr create --base master --head dev --title "Release: vX.Y.Z"
   # After PR is merged, semantic versioning runs automatically
   # dev branch is auto-updated to next X.Y.Z.dev0
   ```

5. **Deploy to production**:
   ```bash
   # Create PR from master to prod (only master branch allowed)
   gh pr create --base prod --head master --title "Deploy: vX.Y.Z to production"
   ```

## Version History

All releases are tracked in:
- Git tags (e.g., `v1.2.3`)
- GitHub Releases
- `CHANGELOG.md`

## Protected Branches

All three branches (`dev`, `master`, `prod`) are protected:
- Cannot be deleted without owner permission
- Force pushes disabled
- Deletion disabled

### Pull Request Requirements

**`master` branch:**
- ✅ Only accepts PRs from `dev` branch
- ❌ Direct pushes blocked
- ❌ PRs from other branches will fail validation

**`prod` branch:**
- ✅ Only accepts PRs from `master` branch
- ❌ Direct pushes blocked
- ❌ PRs from other branches will fail validation

**`dev` branch:**
- ✅ Accepts PRs from feature branches
- ✅ Direct pushes allowed for authorized users
