# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-06-29

### Fixed

- The README banner now uses an absolute image URL so it renders on the PyPI
  project page as well as on GitHub.

## [0.1.0] - 2026-06-29

### Added

- Authenticated client with OAuth2 password, refresh token, and client
  credentials grants, automatic access token refresh, and a pluggable token
  store.
- Resilient HTTP transport with retries, `Retry-After` aware backoff, a
  proactive rate limiter, a download concurrency limit, and an exception
  hierarchy.
- OData catalogue: product search with a fluent filter builder, single product
  retrieval, counting, bulk name resolution, product and per file download,
  node tree browsing, deleted products, and attribute discovery.
- STAC catalogue: search with CQL2 filters, collection and item browse,
  queryables, and asset download.
- Direct S3 archive download through the optional `s3` extra.
- Sentinel-1 SLC Bursts search.
- Subscriptions for product change notifications, including the pull queue.
- Traceability record lookup.
- A `cdse` command line interface for authentication, search, and download,
  with a file backed session store, available through the optional `cli` extra.

[Unreleased]: https://github.com/polymood/cdse/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/polymood/cdse/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/polymood/cdse/releases/tag/v0.1.0
