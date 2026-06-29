# Configuration

All endpoints, limits, and credentials are held in a
[`Settings`](reference/config.md) object. Pass one to the client, or rely on
environment variables prefixed with `CDSE_`.

```python
from cdse import Client, PasswordAuth, Settings

settings = Settings(requests_per_minute=120, max_concurrent_downloads=2)
client = Client(PasswordAuth("you@example.com", "pw"), settings=settings)
```

## Environment variables

Every field maps to an upper-cased `CDSE_`-prefixed variable:

| Variable | Purpose | Default |
| --- | --- | --- |
| `CDSE_USERNAME` / `CDSE_PASSWORD` | Account credentials | — |
| `CDSE_TOTP` | Two factor code | — |
| `CDSE_S3_ACCESS_KEY` / `CDSE_S3_SECRET_KEY` | S3 credentials | — |
| `CDSE_REQUESTS_PER_MINUTE` | Proactive rate limit (off by default) | unset |
| `CDSE_MAX_CONCURRENT_DOWNLOADS` | Parallel downloads | 4 |
| `CDSE_REQUEST_TIMEOUT` | Per-request timeout (seconds) | 30 |
| `CDSE_MAX_RETRIES` | Retry attempts on transient failures | 5 |
| `CDSE_EXPIRY_SKEW` | Refresh the token this many seconds early | 30 |
| `CDSE_TOKEN_URL` / `CDSE_ODATA_URL` / `CDSE_STAC_URL` / `CDSE_TRACE_URL` | API endpoints | public CDSE hosts |
| `CDSE_S3_ENDPOINT_URL` / `CDSE_S3_BUCKET` / `CDSE_S3_REGION` | S3 settings | `eodata` defaults |

A local `.env` file is also read.

## Token lifetimes

The access token is valid for about ten minutes and the refresh token for about
sixty. The client refreshes the access token automatically. With `PasswordAuth`
it can also re-authenticate from scratch when the refresh window lapses, so a
long-running process keeps working; with `RefreshTokenAuth` the session ends
after the refresh window.
