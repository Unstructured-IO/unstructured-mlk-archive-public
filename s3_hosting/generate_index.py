import boto3

BUCKET = "example-transformations-mlk-archive"
PREFIX = "mlk-archive/"
OUTPUT_FILE = "index.html"

# Final hosted JSONL link
PROCESSED_JSONL_URL = "https://example-transformations-mlk-archive.s3.us-east-1.amazonaws.com/transformed-data/mlk-archive-public.jsonl"

s3 = boto3.client("s3")
paginator = s3.get_paginator("list_objects_v2")

html = ['<html><body>']

# Section: Link to processed JSONL
html.append('<h1>Processed Dataset</h1>')
html.append(f'<p><a href="{PROCESSED_JSONL_URL}">Download mlk-archive-public.jsonl</a></p>')

# Section: List all National Archive S3 files
html.append('<h1>Unprocessed National Archive Files</h1><ul>')  # ← Title updated here

for page in paginator.paginate(Bucket=BUCKET, Prefix=PREFIX):
    for obj in page.get("Contents", []):
        key = obj["Key"]
        if key.endswith("/"):
            continue  # skip folders
        url = f"https://{BUCKET}.s3.amazonaws.com/{key}"
        filename = key.split("/")[-1]  # Strip prefix and folders
        html.append(f'<li><a href="{url}">{filename}</a></li>')

html.append("</ul></body></html>")

with open(OUTPUT_FILE, "w") as f:
    f.write("\n".join(html))

print(f"{OUTPUT_FILE} written with clean display names.")
