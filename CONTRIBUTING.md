# Contributing to cdse

Thank you for your interest in contributing to `cdse`, a Python client for the
Copernicus Data Space Ecosystem (CDSE) APIs. This document describes how we
work together on this project: how to set up your environment, how to write and
commit changes, how branches are managed, and how releases are tagged. Please
read it in full before opening your first pull request.

The goal of these guidelines is to keep the codebase consistent, reviewable,
and reliable. Following them helps maintainers review your work quickly and
helps everyone trust that the main branch is always in a releasable state.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Quality and Tooling](#code-quality-and-tooling)
- [Branching Model](#branching-model)
- [Commit Messages](#commit-messages)
- [Pull Requests](#pull-requests)
- [Testing](#testing)
- [Versioning and Releases](#versioning-and-releases)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

We expect all contributors to be respectful and constructive in every
interaction. Disagreement about technical decisions is welcome and healthy, but
personal attacks, harassment, and dismissive behavior are not acceptable.
Maintainers reserve the right to remove comments, commits, or contributors that
violate this principle.

## Getting Started

1. Fork the repository on your account, or, if you have write access, create a
   branch directly in the main repository.
2. Clone your fork or the repository to your local machine.
3. Set up the development environment as described below.
4. Create a branch for your work following the branching model.
5. Make your changes, ensuring all code quality checks pass.
6. Open a pull request against the `main` branch.

## Development Environment

This project targets Python 3.12 or newer and uses [uv](https://docs.astral.sh/uv/)
for dependency management and virtual environments.

### Prerequisites

- Python 3.12 or newer.
- `uv` installed on your system. Refer to the official documentation for the
  installation method that suits your platform.
- Git.

### Setting Up

Install the project together with its development dependencies and create the
virtual environment:

```bash
uv sync --all-extras --dev
```

Activate the environment when you want to run commands directly, or prefix
individual commands with `uv run`:

```bash
uv run python -c "import cdse; print(cdse.__version__)"
```

Install the pre-commit hooks so that quality checks run automatically before
every commit:

```bash
uv run pre-commit install
```

From this point on, the configured hooks will run each time you create a commit.
You can also run them against the whole codebase at any time:

```bash
uv run pre-commit run --all-files
```

## Code Quality and Tooling

We hold the codebase to a consistent standard and enforce it automatically. A
pull request will not be merged unless all of the following checks pass.

### Formatting and Linting

We use [Ruff](https://docs.astral.sh/ruff/) both as our formatter and as our
linter. Ruff enforces PEP 8 style rules and a curated set of additional lint
checks. The configuration lives in `pyproject.toml`.

```bash
# Format the code in place.
uv run ruff format .

# Run the linter and apply safe automatic fixes.
uv run ruff check --fix .
```

Code that is not formatted according to Ruff, or that produces lint errors,
will be rejected by the pre-commit hooks and by continuous integration.

### Static Type Checking

All code must be fully type annotated. Public functions, methods, and class
attributes are required to carry explicit type hints, and we treat type errors
as failures. We use [mypy](https://mypy-lang.org/) in strict mode for static
analysis.

```bash
uv run mypy .
```

Please do not silence type errors with `# type: ignore` unless it is genuinely
unavoidable. When you do, add a specific error code and a short comment
explaining why the suppression is necessary.

### Typing Conventions

- Prefer precise types over `Any`. Reach for `Any` only when there is no
  reasonable alternative, and document the reason.
- Use the modern built-in generic syntax, for example `list[str]` and
  `dict[str, int]`, rather than the equivalents from the `typing` module.
- Use `from __future__ import annotations` where it helps keep annotations
  readable and avoids runtime import costs.

### Running All Checks Locally

Before pushing, it is good practice to run the full set of checks at once:

```bash
uv run pre-commit run --all-files
uv run mypy .
uv run pytest
```

## Branching Model

The `main` branch is protected and must always remain in a releasable state.
Direct pushes to `main` are not permitted. All work happens on dedicated
branches that are merged through pull requests.

### Branch Naming

Use short, descriptive branch names that begin with a category prefix and use
hyphens to separate words. The recommended prefixes are:

- `feature/` for new functionality, for example `feature/oauth-token-refresh`.
- `fix/` for bug fixes, for example `fix/rate-limit-retry`.
- `docs/` for documentation only changes, for example `docs/authentication-guide`.
- `refactor/` for internal changes that do not alter behavior.
- `test/` for changes that only add or adjust tests.
- `chore/` for maintenance work such as dependency updates or tooling.

When a branch addresses a tracked issue, include the issue number in the name,
for example `fix/142-token-expiry`.

### Keeping Branches Current

Keep your branch up to date with `main` while you work. We prefer rebasing over
merging to keep the history linear and easy to read:

```bash
git fetch origin
git rebase origin/main
```

Resolve any conflicts locally, run the full set of checks again, and then
continue. Avoid merge commits inside feature branches.

## Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/)
specification. A well formed commit message makes the history searchable and
allows us to generate changelogs automatically.

### Format

```
<type>(<optional scope>): <short summary>

<optional body>

<optional footer>
```

The summary line should be written in the imperative mood, should not end with
a period, and should stay within roughly fifty characters. The body, when
present, explains what changed and why rather than how, and is wrapped at
seventy-two characters.

### Allowed Types

- `feat` for a new feature.
- `fix` for a bug fix.
- `docs` for documentation only changes.
- `style` for formatting changes that do not affect behavior.
- `refactor` for code changes that neither fix a bug nor add a feature.
- `perf` for changes that improve performance.
- `test` for adding or correcting tests.
- `build` for changes to the build system or dependencies.
- `ci` for changes to continuous integration configuration.
- `chore` for other maintenance tasks.

### Examples

```
feat(auth): add automatic OAuth token refresh

The client now refreshes the access token transparently when it is
within sixty seconds of expiry, so long running sessions no longer
fail with an authentication error.
```

```
fix(http): respect the Retry-After header on rate limited responses
```

A breaking change must be indicated either with an exclamation mark after the
type, as in `feat!:`, or with a `BREAKING CHANGE:` footer that describes the
impact and the migration path.

## Pull Requests

1. Make sure your branch is rebased on the latest `main` and that all checks
   pass locally.
2. Push your branch and open a pull request against `main`.
3. Fill in the pull request description. Explain the motivation, summarize the
   changes, and link any related issues using a closing keyword such as
   `Closes #142`.
4. Keep pull requests focused. A pull request should address a single concern.
   Large, unrelated changes are harder to review and more likely to introduce
   regressions.
5. Be responsive to review feedback. Push follow up commits during review, and
   we will squash them on merge so the final history stays clean.

### Review and Merge

- At least one maintainer approval is required before a pull request can be
  merged.
- Continuous integration must be green.
- We merge using the squash strategy so that each pull request becomes a single
  commit on `main`. The squash commit message must follow the Conventional
  Commits format described above.

## Testing

We use [pytest](https://docs.pytest.org/) for testing. New features must be
accompanied by tests, and bug fixes should include a regression test that fails
before the fix and passes after it.

```bash
uv run pytest
```

Aim for meaningful coverage of the behavior you add, including error paths such
as authentication failures and rate limiting. Tests that reach the live CDSE
APIs must be clearly marked and excluded from the default test run, so that the
standard suite remains fast and deterministic.

## Versioning and Releases

This project follows [Semantic Versioning](https://semver.org/). Given a
version number `MAJOR.MINOR.PATCH`:

- `MAJOR` is incremented for incompatible API changes.
- `MINOR` is incremented for backward compatible new functionality.
- `PATCH` is incremented for backward compatible bug fixes.

While the project is below version `1.0.0`, the public interface should be
considered unstable, and minor versions may include breaking changes.

### Tagging a Release

Releases are cut from `main` by a maintainer. The process is:

1. Ensure `main` is green and contains all changes intended for the release.
2. Update the version in `pyproject.toml`.
3. Update the changelog.
4. Create an annotated, signed tag that matches the version, prefixed with `v`:

   ```bash
   git tag -a -s v0.2.0 -m "Release 0.2.0"
   git push origin v0.2.0
   ```

5. Pushing the tag triggers the release workflow, which builds and publishes the
   package.

Tags must always point to a commit on `main` and must never be moved or deleted
once published.

## Reporting Issues

If you find a bug or want to request a feature, please open an issue. A good
report includes:

- A clear and descriptive title.
- The version of `cdse` and of Python that you are using.
- The steps required to reproduce the problem.
- What you expected to happen and what actually happened.
- Any relevant logs or tracebacks, with credentials and tokens removed.

Please do not include access tokens, client secrets, or other credentials in
issues or pull requests. If you believe you have found a security vulnerability,
report it privately to the maintainers rather than opening a public issue.

Thank you for helping make `cdse` better.
