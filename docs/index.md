# cdse

A Python client and command line tool for the
[Copernicus Data Space Ecosystem](https://dataspace.copernicus.eu/) (CDSE) APIs,
focused on searching for and downloading Earth observation data.

## Install

```bash
pip install cdse           # library
pip install 'cdse[cli]'    # command line tool
pip install 'cdse[s3]'     # direct S3 download
```

## What it covers

- **Authentication** with OAuth2 and automatic token refresh.
- **OData** catalogue: search, single product, count, bulk resolve, download,
  node browsing, deleted products, attributes.
- **STAC** catalogue: search, browse, queryables, asset download.
- **S3** direct archive download.
- **Sentinel-1 SLC Bursts** search.
- **Subscriptions** for product change notifications.
- **Traceability** record lookup.
- A `cdse` command line interface.

## Next steps

- [Quickstart](quickstart.md) — authenticate and run your first search.
- [Filters](filters.md) — build OData queries, including geographic ROIs.
- [Usage by API](usage.md) — short recipes per API.
- [API reference](reference/client.md) — every public class and method.

openEO and Sentinel Hub are intentionally out of scope; both already have
dedicated Python clients.
