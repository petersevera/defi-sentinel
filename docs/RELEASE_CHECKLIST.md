# Release Checklist

## Pre-release
- [ ] Update `CHANGELOG.md` with release notes.
- [ ] Ensure `README.md` quickstart is accurate.
- [ ] Run `make validate` and `make features`.
- [ ] (Optional) Run `make rag-index`.
- [ ] Verify API: `/health`, `/events`, `/brief`, `/rag/query`.
- [ ] Tag version (e.g., `v0.1.0`).

## Release
- [ ] Push tag to GitHub.
- [ ] Create GitHub release with notes.

## Post-release
- [ ] Monitor issues and feedback.
