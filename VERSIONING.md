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
git commit -m "fix: resolve null pointer exception in parser"
# Results in: 1.2.3 → 1.2.4

git commit -m "feat: add CSV export functionality"
# Results in: 1.2.4 → 1.3.0

git commit -m "feat!: redesign API endpoints

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
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug"
   ```

3. **Merge to dev** for testing:
   ```bash
   git checkout dev
   git merge feature/my-feature
   git push origin dev
   ```

4. **Release to master** when ready:
   ```bash
   git checkout master
   git merge dev
   git push origin master
   # Semantic versioning runs automatically
   # dev branch is auto-updated to next X.Y.Z.dev0
   ```

5. **Deploy to production**:
   ```bash
   git checkout prod
   git merge master
   git push origin prod
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
