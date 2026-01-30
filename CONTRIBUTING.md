# Contributing

Thanks for your interest in DeFi Sentinel!

## Quick start
- Fork the repo and create a feature branch.
- Use Python 3.10+.
- Install dependencies:
  - Core: `pip install -r requirements-core.txt`
  - Full (RAG): `pip install -r requirements-rag.txt`

## Development workflow
1. Create a branch: `git checkout -b feature/your-topic`
2. Make changes with clear, focused commits.
3. Validate fixtures: `python scripts/validate_fixtures.py`
4. (Optional) Build features: `python scripts/build_features.py`

## Style
- Keep functions small and well-scoped.
- Prefer explicit, readable code over cleverness.
- Add docstrings or comments when behavior is non-obvious.

## Security & data
- Do not commit `.env` or API keys.
- Never commit generated data under `data/` (ignored by default).

## Pull requests
- Describe what you changed and why.
- Mention any new dependencies or configuration changes.
- Add or update docs if behavior changes.
