import re
from kubernetes import client, config

JOB_NAME = "shard-validator"
NAMESPACE = "default"

RESULT_RE = re.compile(
    r"RESULT shard_index=(\d+) pod=(\S+) node=(\S+) total_rows=(\d+) invalid_rows=(\d+)")


def main():
    config.load_kube_config()
    v1 = client.CoreV1Api()

    pods = v1.list_namespaced_pod(
        namespace=NAMESPACE,
        label_selector=f"job-name={JOB_NAME}",)

    results = []
    for pod in pods.items:
        pod_name = pod.metadata.name
        try:
            log = v1.read_namespaced_pod_log(name=pod_name, namespace=NAMESPACE)
        except client.exceptions.ApiException as e:
            print(f"Could not read logs for {pod_name}: {e}")
            continue

        match = RESULT_RE.search(log)
        if not match:
            print(f"No RESULT line found in logs for {pod_name}")
            continue

        shard_index, logged_pod, node, total_rows, invalid_rows = match.groups()
        results.append(
            {
                "shard_index": int(shard_index),
                "pod": logged_pod,
                "node": node,
                "total_rows": int(total_rows),
                "invalid_rows": int(invalid_rows),})

    results.sort(key=lambda r: r["shard_index"])

    print(f"{'Shard':<7}{'Pod':<28}{'Node':<15}{'Rows':<7}{'Invalid':<8}")
    total_invalid = 0
    for r in results:
        print(
            f"{r['shard_index']:<7}{r['pod']:<28}{r['node']:<15}"
            f"{r['total_rows']:<7}{r['invalid_rows']:<8}"
        )
        total_invalid += r["invalid_rows"]

    print(f"\nShards reported: {len(results)} / 8")
    print(f"Total invalid rows across all shards: {total_invalid}")


if __name__ == "__main__":
    main()
