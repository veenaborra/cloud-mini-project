"""Package build/model-<v> deterministically, checksum it, upload to s3://models/<v>/.

  python training/package.py v1
Creates build/release/model-<v>.tar.gz and model-<v>.sha256 (the GitHub Release assets).
"""
import gzip, hashlib, io, os, sys, tarfile
import boto3

v = sys.argv[1]
src = f"build/model-{v}"
os.makedirs("build/release", exist_ok=True)
archive = f"build/release/model-{v}.tar.gz"

buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode="w", format=tarfile.PAX_FORMAT) as tar:
    for name in sorted(os.listdir(src)):                 # fixed order
        info = tarfile.TarInfo(f"model-{v}/{name}")
        info.size = os.path.getsize(f"{src}/{name}")
        info.mtime, info.mode, info.uid, info.gid = 0, 0o644, 0, 0   # fixed metadata
        with open(f"{src}/{name}", "rb") as f:
            tar.addfile(info, f)
with open(archive, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
    gz.write(buf.getvalue())

digest = hashlib.sha256(open(archive, "rb").read()).hexdigest()
open(f"build/release/model-{v}.sha256", "w").write(f"{digest}  model-{v}.tar.gz\n")
print("sha256", digest)

s3 = boto3.client("s3", endpoint_url=os.environ.get("S3_ENDPOINT", "http://localhost:8333"), region_name="us-east-1")
for name in sorted(os.listdir(src)):
    s3.upload_file(f"{src}/{name}", "models", f"{v}/{name}")
    print(f"uploaded models/{v}/{name}")
s3.upload_file(f"build/release/model-{v}.sha256", "models", f"{v}/model.sha256")
print(f"uploaded models/{v}/model.sha256")
