# Command line

Install the `cli` extra:

```bash
pip install 'cdse[cli]'
```

Log in once; the session is stored under your user configuration directory with
owner-only permissions and reused (and refreshed) by later commands.

```bash
cdse auth login          # prompts for credentials (or reads CDSE_USERNAME/PASSWORD)
cdse auth status
cdse auth logout
```

## Search and download

```bash
cdse odata search --collection SENTINEL-2 --cloud-cover-max 20 --limit 10
cdse odata search --filter "Online eq true" --order-by "ContentDate/Start desc"
cdse odata download <product-id> -o product.zip --resume

cdse stac search -c sentinel-2-l2a --bbox 4,50,5,51 --datetime 2024-05-01/2024-05-08
cdse stac download sentinel-2-l2a <item-id> --asset PRODUCT -o product.zip

cdse s3 download s3://eodata/Sentinel-2/.../PRODUCT.SAFE/ -o out/
cdse bursts search --swath IW1 --polarisation VH
cdse traceability get <product-name>
```

Add `--json` to the search commands for machine-readable output.

## Subscriptions

```bash
cdse subscriptions create --filter "Collection/Name eq 'SENTINEL-1'"
cdse subscriptions list
cdse subscriptions read <id> --top 20 --acknowledge
cdse subscriptions set-status <id> paused
cdse subscriptions delete <id>
```

Run `cdse <command> --help` for the full option list of any command.
