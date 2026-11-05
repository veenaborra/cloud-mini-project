"""Create the buckets and upload commands_pool.jsonl to SeaweedFS."""
import os
import boto3

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:8333"),
    aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
    region_name="us-east-1",
)

existing = {b["Name"] for b in s3.list_buckets().get("Buckets", [])}
for bucket in ["datasets", "models"]:
    if bucket not in existing:
        s3.create_bucket(Bucket=bucket)
    print("bucket ok:", bucket)

s3.upload_file("data/commands_pool.jsonl", "datasets", "commands_pool.jsonl")
print("uploaded datasets/commands_pool.jsonl")

for obj in s3.list_objects_v2(Bucket="datasets").get("Contents", []):
    print(" ", obj["Key"], obj["Size"], "bytes")

# restore the labelled dataset (committed in git) so storage matches Task 1
import glob
for path in sorted(glob.glob("data/teacher/shard-*.jsonl")):
    s3.upload_file(path, "datasets", "teacher/" + os.path.basename(path))
    print("uploaded datasets/teacher/" + os.path.basename(path))
for name in ("train.jsonl", "train.sha256"):
    s3.upload_file(f"data/train/{name}", "datasets", f"v1/{name}")
    print("uploaded datasets/v1/" + name)
