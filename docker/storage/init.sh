#!/bin/sh
set -e

: "${STORAGE_ADMIN_KEY:?STORAGE_ADMIN_KEY is not set, add it to .env}"
: "${STORAGE_ADMIN_SECRET:?STORAGE_ADMIN_SECRET is not set, add it to .env}"

S3="http://storage:8333"
ENCRYPTION='<ServerSideEncryptionConfiguration><Rule><ApplyServerSideEncryptionByDefault><SSEAlgorithm>AES256</SSEAlgorithm></ApplyServerSideEncryptionByDefault></Rule></ServerSideEncryptionConfiguration>'

s3() {
    curl -sf --aws-sigv4 "aws:amz:us-east-1:s3" \
        --user "${STORAGE_ADMIN_KEY}:${STORAGE_ADMIN_SECRET}" "$@"
}

for bucket in verification organizer wiki; do
    if s3 -o /dev/null -I "${S3}/${bucket}"; then
        echo "Bucket ${bucket} exists"
    else
        s3 -o /dev/null -X PUT "${S3}/${bucket}"
        echo "Bucket ${bucket} created"
    fi
done

for bucket in verification organizer; do
    s3 -o /dev/null -X PUT "${S3}/${bucket}?encryption" -d "${ENCRYPTION}"
    echo "Bucket ${bucket} encrypted by default"
done

echo "fs.configure -locationPrefix=/buckets/verification/ -ttl=30d -apply" \
    | weed shell -master=storage:9333 -filer=storage:8888 > /dev/null
echo "Bucket verification expires objects after 30d"
