"""
Generate Azure Cosmos DB REST API authorization headers.

Usage:
    python cosmos-auth.py --verb GET --resource-type docs \
        --resource-link "dbs/mydb/colls/mycoll" --key "<master-key>"

Outputs two lines:
    Line 1: x-ms-date value
    Line 2: Authorization header value (URL-encoded)
"""

import argparse
import base64
import hashlib
import hmac
import urllib.parse
from datetime import datetime, timezone


def generate_auth_token(verb: str, resource_type: str, resource_link: str, key: str) -> tuple[str, str]:
    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    payload = f"{verb.lower()}\n{resource_type.lower()}\n{resource_link}\n{date.lower()}\n\n"

    decoded_key = base64.b64decode(key)
    digest = hmac.new(decoded_key, payload.encode("utf-8"), hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode("utf-8")

    token = urllib.parse.quote(f"type=master&ver=1.0&sig={signature}", safe="")

    return date, token


def main():
    parser = argparse.ArgumentParser(description="Generate Cosmos DB REST API auth headers")
    parser.add_argument("--verb", required=True, help="HTTP verb (GET, POST, PUT, DELETE)")
    parser.add_argument("--resource-type", required=True, help="Resource type (dbs, colls, docs, sprocs, triggers, udfs)")
    parser.add_argument("--resource-link", required=True, help="Resource link path (e.g. dbs/mydb/colls/mycoll)")
    parser.add_argument("--key", required=True, help="Cosmos DB master key")
    args = parser.parse_args()

    date, token = generate_auth_token(args.verb, args.resource_type, args.resource_link, args.key)
    print(date)
    print(token)


if __name__ == "__main__":
    main()
