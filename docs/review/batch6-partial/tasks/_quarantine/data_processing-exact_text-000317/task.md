You are an ETL developer normalising vendor records.

`/data/vendors.bz2` is a bzip2-compressed pipe-delimited (`|`) text file with a header row and columns `vendor_id|name|category|price`.

Your job:
1. Start a local HTTP service (on port 7654) that, when `GET /vendors` is requested, responds with the processed vendor data as YAML.
2. Processing rules:
   - Decompress the bzip2 stream.
   - Skip any record where `vendor_id` **or** `name` is empty/missing (schema validation).
   - Deduplicate by `vendor_id`, keeping the first occurrence.
   - Sort the surviving records by `vendor_id` ascending.
   - Return them as YAML: a top-level list of mappings with keys `vendor_id`, `name`, `category`, `price` (in that key order).
3. `curl -s http://localhost:7654/vendors` and save the response body to `/output/vendors.yaml`.

The final file `/output/vendors.yaml` must contain exactly the processed YAML.
