# Examples

Runnable scripts demonstrating the `cdse` client. Each reads credentials from
the environment:

```bash
export CDSE_USERNAME=you@example.com
export CDSE_PASSWORD='your-password'
# S3 examples additionally need:
export CDSE_S3_ACCESS_KEY=...
export CDSE_S3_SECRET_KEY=...
```

Then run any script, for example:

```bash
python examples/odata_search_download.py
```

| Script | What it shows |
| --- | --- |
| [quickstart.py](quickstart.py) | Authenticate, count products, fetch one |
| [odata_search_download.py](odata_search_download.py) | Build a filter, search OData, download a product |
| [stac_search_download.py](stac_search_download.py) | STAC search with a CQL2 filter and asset download |
| [s3_download.py](s3_download.py) | Find a product, then download it directly from S3 |
| [bursts_search.py](bursts_search.py) | Search Sentinel-1 SLC bursts |
| [subscription_demo.py](subscription_demo.py) | Subscribe over a random ROI and print new products |
| [subscription_watch.py](subscription_watch.py) | Reusable, supervisor-friendly watcher that runs forever |
| [traceability_lookup.py](traceability_lookup.py) | Look up a product's traceability record (no login) |

The `subscription_*` scripts open a pull subscription, which notifies you about
products created after the subscription is made, so they print nothing until the
next acquisition over the chosen area is published.
