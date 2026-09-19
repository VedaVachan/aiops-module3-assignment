import random
import csv

NUM_SHARDS = 8
ROWS_PER_SHARD = 50

INVALID_ROWS_PER_SHARD = [3, 5, 2, 7, 1, 4, 6, 0]

FIRST_NAMES = ["alice", "bob", "carol", "dave", "erin", "frank", "grace", "heidi"]
LAST_NAMES = ["smith", "jones", "lee", "patel", "garcia", "brown", "wilson", "davis"]
DOMAINS = ["example.com", "mail.com", "test.org", "signup.net"]


def make_valid_row(rng, row_id):
    first = rng.choice(FIRST_NAMES)
    last = rng.choice(LAST_NAMES)
    domain = rng.choice(DOMAINS)
    return {
        "id": row_id,
        "name": f"{first.title()} {last.title()}",
        "email": f"{first}.{last}{row_id}@{domain}",
        "signup_date": f"2026-0{rng.randint(1, 9)}-{rng.randint(10, 28)}",}


def make_invalid_row(rng, row_id):
    # Randomly choose one of two invalid-row types.
    kind = rng.choice(["bad_email", "missing_field"])
    row = make_valid_row(rng, row_id)
    if kind == "bad_email":
        row["email"] = row["email"].replace("@", "")  # malformed: no @
    else:
        row["name"] = ""  # missing required field
    return row


def generate_shard(shard_index, num_invalid, seed):
    rng = random.Random(seed)
    rows = []
    invalid_positions = set(rng.sample(range(ROWS_PER_SHARD), num_invalid))

    for i in range(ROWS_PER_SHARD):
        row_id = shard_index * ROWS_PER_SHARD + i
        if i in invalid_positions:
            rows.append(make_invalid_row(rng, row_id))
        else:
            rows.append(make_valid_row(rng, row_id))

    filename = f"shard_{shard_index}.csv"
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "name", "email", "signup_date"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"{filename}: {num_invalid} invalid rows (seed={seed})")


if __name__ == "__main__":
    for shard_index in range(NUM_SHARDS):
        generate_shard(
            shard_index,
            INVALID_ROWS_PER_SHARD[shard_index],
            seed=42 + shard_index,)
