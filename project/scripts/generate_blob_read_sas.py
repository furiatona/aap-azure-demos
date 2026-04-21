#!/usr/bin/env python3
"""Print a single HTTPS URL for a block blob with a read-only SAS (no public container required)."""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

try:
    from azure.storage.blob import BlobSasPermissions, generate_blob_sas
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(
        "Missing dependency: azure-storage-blob "
        "(included with azure.azcollection execution environments).\n"
    )
    raise SystemExit(1) from exc


def main() -> None:
    account = os.environ["AZ_REPORT_ACCOUNT_NAME"]
    key = os.environ["AZ_REPORT_ACCOUNT_KEY"]
    container = os.environ["AZ_REPORT_CONTAINER"]
    blob = os.environ["AZ_REPORT_BLOB"]
    hours = int(os.environ.get("AZ_REPORT_SAS_HOURS", "168"))

    expiry = datetime.now(timezone.utc) + timedelta(hours=hours)
    sas = generate_blob_sas(
        account_name=account,
        container_name=container,
        blob_name=blob,
        account_key=key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry,
    )
    base = f"https://{account}.blob.core.windows.net/{container}/{blob}"
    print(f"{base}?{sas}", end="")


if __name__ == "__main__":
    main()
