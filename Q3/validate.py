import csv
import os
import re
import sys

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

REQUIRED_FIELDS = ["id", "name", "email", "signup_date"]

SHARD_DIR = "/data"


def is_invalid(row: dict) -> bool:
    for field in REQUIRED_FIELDS:
        if not row.get(field):
            return True
    if not EMAIL_RE.match(row["email"]):
        return True
    return False


def main():
    completion_index = os.environ.get("JOB_COMPLETION_INDEX")
    if completion_index is None:
        print("ERROR: JOB_COMPLETION_INDEX not set - is this running as part of an Indexed Job?", file=sys.stderr)
        sys.exit(1)

    pod_name = os.environ.get("POD_NAME", "unknown-pod")
    node_name = os.environ.get("NODE_NAME", "unknown-node")

    shard_path = os.path.join(SHARD_DIR, f"shard_{completion_index}.csv")

    with open(shard_path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    invalid_count = sum(1 for row in rows if is_invalid(row))

    print(
        f"RESULT shard_index={completion_index} "
        f"pod={pod_name} node={node_name} "
        f"total_rows={len(rows)} invalid_rows={invalid_count}" )


if __name__ == "__main__":
    main()
