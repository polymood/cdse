# Usage by API

Short recipes for each API. See the [API reference](reference/client.md) for the
full method signatures, and the
[examples directory](https://github.com/polymood/cdse/tree/main/examples) for
runnable scripts.

## OData

```python
# Search (lazy pagination), single product, count, bulk resolve.
for product in client.odata.products.search(flt, top=50):
    ...
product = client.odata.products.get("<uuid>", expand=["Attributes"])
n = client.odata.products.count(flt)
products = client.odata.products.filter_list(["NAME_A", "NAME_B"])

# Download a whole product, or browse and fetch a single inner file.
client.odata.products.download("<uuid>", "product.zip", resume=True)
nodes = client.odata.products.list_nodes("<uuid>")
client.odata.products.download_node("<uuid>", "MTD.xml", destination="MTD.xml")

# Deleted products and attribute discovery.
client.odata.deleted_products.search(FilterBuilder().deletion_cause("Duplicated product"))
client.odata.attributes.list("SENTINEL-2")
```

## STAC

```python
items = client.stac.search(collections=["sentinel-2-l2a"], bbox=[4, 50, 5, 51])
client.stac.collections()
client.stac.collection("sentinel-2-l2a")
client.stac.item("sentinel-2-l2a", "<item-id>")
client.stac.queryables("sentinel-2-l2a")
client.stac.download_asset(item, "PRODUCT", "product.zip")
```

## S3

Needs S3 credentials and the `s3` extra.

```python
from cdse import S3Client

s3 = S3Client("access-key", "secret-key")          # or client.s3
s3.download("/eodata/Sentinel-2/.../PRODUCT.SAFE/", "out/")
```

## Sentinel-1 SLC bursts

```python
bursts = client.odata.bursts.search(swath="IW1", polarisation="VH")
# No per-burst download; fetch the parent product instead:
client.odata.products.download(bursts[0].parent_product_id, "parent.zip")
```

## Subscriptions

```python
sub = client.subscriptions.create(
    "Collection/Name eq 'SENTINEL-1'", subscription_type="pull", events=["created"]
)
for n in client.subscriptions.read(sub.id, top=20):
    print(n.product_name)
client.subscriptions.acknowledge(sub.id, n.ack_id)  # acks this and earlier ones
client.subscriptions.set_status(sub.id, "paused")
client.subscriptions.delete(sub.id)
```

The `FilterParam` uses the same grammar as OData, so [ROIs](filters.md#regions-of-interest-rois)
work. See `examples/subscription_watch.py` for a long-running watcher.

## Traceability

```python
trace = client.traceability.get_by_name("S2A_MSIL1C_...SAFE.zip")
print(trace.hash, trace.hash_algorithm)
```
