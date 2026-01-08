#!/usr/bin/env python3
"""
MinIO bucket initialization script.
Creates required buckets: edu-uploads, edu-backups

SECURITY: This script requires environment variables to be set.
Do not use default credentials in production!
"""
import os
import sys
from minio import Minio
from minio.error import S3Error

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

# Validate required environment variables
if not all([MINIO_ENDPOINT, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD]):
    print("ERROR: Missing required environment variables:")
    print("  - MINIO_ENDPOINT")
    print("  - MINIO_ROOT_USER")
    print("  - MINIO_ROOT_PASSWORD")
    sys.exit(1)

BUCKETS = [
    {"name": "edu-uploads", "public": True},
    {"name": "edu-backups", "public": False},
]

PUBLIC_POLICY = """{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"AWS": "*"},
        "Action": ["s3:GetObject"],
        "Resource": ["arn:aws:s3:::%s/*"]
    }]
}"""


def main():
    print(f"Connecting to MinIO at {MINIO_ENDPOINT}...")
    
    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ROOT_USER,
        secret_key=MINIO_ROOT_PASSWORD,
        secure=MINIO_USE_SSL,
    )
    
    for bucket in BUCKETS:
        name = bucket["name"]
        try:
            if not client.bucket_exists(name):
                client.make_bucket(name)
                print(f"✓ Created bucket: {name}")
            else:
                print(f"• Bucket exists: {name}")
            
            if bucket["public"]:
                client.set_bucket_policy(name, PUBLIC_POLICY % name)
                print(f"  → Set public read policy for {name}")
                
        except S3Error as e:
            print(f"✗ Error with bucket {name}: {e}")
            sys.exit(1)
    
    print("\n✓ MinIO initialization complete!")


if __name__ == "__main__":
    main()
