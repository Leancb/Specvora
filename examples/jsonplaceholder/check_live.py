"""Three read-only diagnostic requests. Separate from generated/governed execution."""
import argparse
import json
import ssl
from datetime import UTC, datetime
from pathlib import Path

import httpx


def inspect_responses(posts, post, comments):
    checks = {
        "posts_nonempty": isinstance(posts, list) and bool(posts),
        "post_identity": isinstance(post, dict) and post.get("id") == 1,
        "post_fields": isinstance(post, dict) and all(
            isinstance(post.get(field), str) and bool(post[field]) for field in ("title", "body")
        ) and type(post.get("userId")) is int,
        "comments_relationship": isinstance(comments, list) and bool(comments) and all(
            isinstance(item, dict) and item.get("postId") == 1
            and isinstance(item.get("email"), str) and "@" in item["email"]
            for item in comments
        ),
    }
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Reserve a new report before making any requests.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        report = {"target": "https://jsonplaceholder.typicode.com",
                  "checked_at": datetime.now(UTC).isoformat(),
                  "kind": "read-only diagnostic, not a release assessment", "requests": []}
        try:
            payloads = []
            with httpx.Client(timeout=10, follow_redirects=False, trust_env=False,
                              verify=ssl.create_default_context()) as client:
                for path in ("/posts", "/posts/1", "/posts/1/comments"):
                    response = client.get(report["target"] + path)
                    report["requests"].append({"method": "GET", "path": path,
                                               "status": response.status_code})
                    response.raise_for_status()
                    if response.status_code != 200:
                        raise ValueError("Expected HTTP 200")
                    payloads.append(response.json())
            report["checks"] = inspect_responses(*payloads)
            report["passed"] = all(report["checks"].values())
        except (httpx.HTTPError, ValueError):
            report["passed"] = False
            report["error"] = "Connection, HTTP status or JSON failure; inspect request statuses."
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
