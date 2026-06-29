<p align="center">
  <img src="https://raw.githubusercontent.com/polymood/cdse/main/assets/banner.png" alt="Sentinel-2 imagery over six locations, fetched with cdse" width="100%">
</p>

<p align="center">
  <a href="https://pypi.org/project/cdse/"><img src="https://img.shields.io/pypi/v/cdse.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/cdse/"><img src="https://img.shields.io/pypi/pyversions/cdse.svg" alt="Supported Python versions"></a>
  <a href="https://github.com/polymood/cdse/actions/workflows/ci.yml"><img src="https://github.com/polymood/cdse/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="https://github.com/polymood/cdse/blob/main/LICENSE"><img src="https://img.shields.io/github/license/polymood/cdse.svg" alt="License"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Linted with Ruff"></a>
  <a href="https://mypy-lang.org/"><img src="https://www.mypy-lang.org/static/mypy_badge.svg" alt="Checked with mypy"></a>
</p>

# cdse

A Python client and command line tool for the
[Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/) (CDSE) APIs.

`cdse` focuses on searching for and downloading Earth observation data. It wraps
the CDSE APIs behind a single authenticated client with automatic token refresh,
retries, rate limit handling, and typed responses.

## Features

- OAuth2 authentication with automatic access token refresh, supporting the
  password, refresh token, and client credentials grants.
- A resilient HTTP layer with retries, backoff that honours `Retry-After`, a
  proactive rate limiter, and a download concurrency limit.
- **OData** catalogue: product search with a fluent filter builder, single
  product retrieval, counting, bulk name resolution, product and per file
  download, node tree browsing, deleted products, and attribute discovery.
- **STAC** catalogue: search with CQL2 filters, collection and item browse,
  queryables, and asset download.
- **S3** direct download from the `eodata` archive (optional extra).
- **Sentinel-1 SLC Bursts** search.
- **Subscriptions** for notifications about new, modified, or deleted products.
- **Traceability** record lookup.
- A `cdse` command line interface covering authentication, search, and download.

## Installation

```bash
pip install cdse
```

Optional extras:

```bash
pip install 'cdse[cli]'   # the cdse command line tool
pip install 'cdse[s3]'    # direct S3 archive download
pip install 'cdse[cli,s3]'
```

`cdse` requires Python 3.12 or newer.

## Authentication

Most APIs require a Copernicus Data Space Ecosystem account. The client
authenticates with your username and password and then refreshes the access
token automatically.

```python
from cdse import Client, PasswordAuth

# The client is a context manager; it closes its connection pool on exit.
with Client(PasswordAuth("you@example.com", "your-password")) as client:
    count = client.odata.products.count()
    print(f"{count} products in the catalogue")
```

If your account uses two factor authentication, pass the current code as
`PasswordAuth("you@example.com", "pw", totp="123456")`. Credentials can also be
supplied through the environment variables `CDSE_USERNAME` and `CDSE_PASSWORD`,
which the command line tool reads automatically.

## Quick start: search and download with OData

```python
from cdse import Client, PasswordAuth, FilterBuilder

with Client(PasswordAuth("you@example.com", "your-password")) as client:
    query = (
        FilterBuilder()
        .collection("SENTINEL-2")
        .acquired_between("2024-05-01", "2024-05-08")
        .attribute("cloudCover", "le", 20.0)
        .intersects("POLYGON((4 50, 5 50, 5 51, 4 51, 4 50))")
    )

    products = list(client.odata.products.search(query, top=10))
    for product in products:
        print(product.id, product.name)

    # Download the first product as a zip archive.
    client.odata.products.download(products[0].id, "product.zip", resume=True)
```

Browse the files inside a product and download a single one:

```python
nodes = client.odata.products.list_nodes(products[0].id)
client.odata.products.download_node(
    products[0].id, "MTD_MSIL2A.xml", destination="MTD_MSIL2A.xml"
)
```

## Search and download with STAC

```python
from cdse import Client, PasswordAuth

with Client(PasswordAuth("you@example.com", "your-password")) as client:
    items = list(
        client.stac.search(
            collections=["sentinel-2-l2a"],
            bbox=[4.0, 50.0, 5.0, 51.0],
            datetime="2024-05-01/2024-05-08",
            filter={"op": "<=", "args": [{"property": "eo:cloud_cover"}, 20]},
            filter_lang="cql2-json",
        )
    )
    item = items[0]
    client.stac.download_asset(item, "PRODUCT", "product.zip")
```

## Direct S3 download

Generate S3 credentials at
[the S3 keys manager](https://eodata-s3keysmanager.dataspace.copernicus.eu/) and
provide them through `CDSE_S3_ACCESS_KEY` and `CDSE_S3_SECRET_KEY`, or directly:

```python
from cdse import S3Client

s3 = S3Client("access-key", "secret-key")
# Accepts an s3:// URI, an OData S3Path, or a bucket relative key.
s3.download("/eodata/Sentinel-2/MSI/L2A/2024/05/01/PRODUCT.SAFE/", "out/")
```

## Sentinel-1 SLC bursts

```python
bursts = list(
    client.odata.bursts.search(swath="IW1", polarisation="VH", parent_product_id="...")
)
```

There is no per burst download endpoint; download the parent product with
`client.odata.products.download(burst.parent_product_id)` or from S3.

## Subscriptions

```python
subscription = client.subscriptions.create(
    "Collection/Name eq 'SENTINEL-1'", events=["created"]
)
for notification in client.subscriptions.read(subscription.id, top=10):
    print(notification.product_name)
    client.subscriptions.acknowledge(subscription.id, notification.ack_id)
```

## Traceability

```python
trace = client.traceability.get_by_name("S2A_MSIL1C_20230420T100021_....SAFE.zip")
print(trace.hash, trace.hash_algorithm)
```

## Command line interface

Install the `cli` extra, then:

```bash
cdse auth login                      # prompts for credentials and stores a session
cdse auth status
cdse odata search --collection SENTINEL-2 --cloud-cover-max 20 --limit 10
cdse odata download <product-id> -o product.zip
cdse stac search -c sentinel-2-l2a --bbox 4,50,5,51 --datetime 2024-05-01/2024-05-08
cdse stac download sentinel-2-l2a <item-id> --asset PRODUCT -o product.zip
cdse s3 download s3://eodata/Sentinel-2/.../PRODUCT.SAFE/ -o out/
cdse bursts search --swath IW1 --polarisation VH
cdse subscriptions list
cdse traceability get <product-name>
cdse auth logout
```

The session is stored under your user configuration directory with owner only
permissions. Add `--json` to the search commands for machine readable output.

## Configuration

Every endpoint and limit can be overridden through a `Settings` object or
environment variables prefixed with `CDSE_`, for example `CDSE_USERNAME`,
`CDSE_PASSWORD`, `CDSE_S3_ACCESS_KEY`, `CDSE_S3_SECRET_KEY`,
`CDSE_REQUESTS_PER_MINUTE`, and `CDSE_MAX_CONCURRENT_DOWNLOADS`.

```python
from cdse import Client, PasswordAuth, Settings

settings = Settings(requests_per_minute=120, max_concurrent_downloads=2)
client = Client(PasswordAuth("you@example.com", "pw"), settings=settings)
```

## Notes and limitations

- Access tokens are valid for about ten minutes and refresh tokens for about
  sixty. After an hour of inactivity a new login is required unless credentials
  are available to authenticate again.
- The exact wire format of a few endpoints (OData product nodes and attributes,
  STAC asset authentication, and the subscription acknowledgement action) is not
  fully documented; these are parsed and called defensively and should be
  confirmed against the live service.
- Verifying the digital signature of a traceability record is delegated to the
  official [`trace-cli`](https://github.com/eu-cdse/trace-cli) tool.
- openEO and Sentinel Hub are intentionally out of scope, as both already have
  dedicated Python clients.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the development setup, branching
model, commit conventions, and release process.

## License

See [LICENSE](LICENSE).
