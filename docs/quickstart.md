# Quickstart

## Authenticate

```python
from cdse import Client, PasswordAuth

with Client(PasswordAuth("you@example.com", "your-password")) as client:
    print(client.odata.products.count())
```

The client refreshes the access token automatically. With two factor
authentication, pass the code: `PasswordAuth("you@example.com", "pw", totp="123456")`.

Credentials can also come from the environment (`CDSE_USERNAME`, `CDSE_PASSWORD`)
via [`Settings`](configuration.md), which is what the command line tool uses.

## Search and download (OData)

```python
from cdse import Client, PasswordAuth, FilterBuilder

with Client(PasswordAuth("you@example.com", "pw")) as client:
    query = (
        FilterBuilder()
        .collection("SENTINEL-2")
        .acquired_between("2024-05-01", "2024-05-08")
        .attribute("cloudCover", "le", 20.0)
    )
    products = list(client.odata.products.search(query, top=10))
    client.odata.products.download(products[0].id, "product.zip", resume=True)
```

## Search and download (STAC)

```python
items = list(
    client.stac.search(
        collections=["sentinel-2-l2a"],
        bbox=[4.0, 50.0, 5.0, 51.0],
        datetime="2024-05-01/2024-05-08",
    )
)
client.stac.download_asset(items[0], "PRODUCT", "product.zip")
```

See [Usage by API](usage.md) for the other APIs and the
[examples directory](https://github.com/polymood/cdse/tree/main/examples) for
runnable scripts.
