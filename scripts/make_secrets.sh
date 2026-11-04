#!/usr/bin/env bash
# Create random S3 credentials (git-ignored .s3.env) and the Kubernetes Secrets that use them.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .s3.env ]; then
  echo "AWS_ACCESS_KEY_ID=$(head -c 12 /dev/urandom | od -An -tx1 | tr -d ' \n')" > .s3.env
  echo "AWS_SECRET_ACCESS_KEY=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')" >> .s3.env
fi
set -a; source .s3.env; set +a
for ns in data pipeline app; do kubectl create namespace $ns --dry-run=client -o yaml | kubectl apply -f -; done
kubectl -n data create secret generic seaweedfs-s3-config --dry-run=client -o yaml \
  --from-literal=s3.json="{\"identities\":[{\"name\":\"admin\",\"credentials\":[{\"accessKey\":\"$AWS_ACCESS_KEY_ID\",\"secretKey\":\"$AWS_SECRET_ACCESS_KEY\"}],\"actions\":[\"Admin\",\"Read\",\"Write\",\"List\",\"Tagging\"]}]}" \
  | kubectl apply -f -
for ns in pipeline app; do
  kubectl -n $ns create secret generic s3-credentials --dry-run=client -o yaml \
    --from-literal=AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY" \
    | kubectl apply -f -
done
