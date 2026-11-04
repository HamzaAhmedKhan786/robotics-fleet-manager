
# Contributing

Thank you for your interest in Robotics Fleet Manager.

The project is in early development. Contributions, technical feedback, bug reports, and design discussions are welcome.

## Development Setup

1. Fork and clone the repository.
2. Install Pixi.
3. Run `pixi install`.
4. Create a feature branch.
5. Make focused changes.
6. Run relevant tests.
7. Open a pull request.

## Branch Naming

- `feat/feature-name`
- `fix/issue-name`
- `docs/documentation-update`
- `test/test-description`

## Coding Standards

### Python
- Use type hints.
- Follow Ruff formatting and linting.
- Use Pydantic for API schemas.
- Add tests for business logic.
- Keep modules focused.

### TypeScript
- Use strict TypeScript.
- Prefer reusable React components.
- Avoid unnecessary client-side state.
- Follow ESLint rules.

## Pull Requests

Include:
- Summary of changes
- Reason for the change
- Tests performed
- Documentation updates
- Known limitations

## Safety

Do not submit changes that bypass robot safety checks or introduce unsafe physical-control assumptions.

## Reporting Issues

Include reproduction steps, expected behavior, actual behavior, and relevant logs. Never include credentials or secrets.
