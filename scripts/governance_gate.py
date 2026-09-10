#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys

BLOCKING_GATES = {"HUMAN_LOCK", "WARDEN_LOCK", "BLOCKED", "DONE"}
ALLOWED_GATES = {"GO", "WORK", "REVIEW"}


def run(*args):
    return subprocess.check_output(args, text=True).strip()


def load_json_from_ref(ref, path):
    raw = run("git", "show", f"{ref}:{path}")
    return json.loads(raw)


def changed_files(base, head):
    raw = run("git", "diff", "--name-only", base, head)
    return [p for p in raw.splitlines() if p.strip()]


def owner_for_path(path, workstreams):
    matches = []
    for ws in workstreams:
        for prefix in ws.get("paths", []):
            if path.startswith(prefix):
                matches.append((len(prefix), ws))
    if not matches:
        return None
    return sorted(matches, key=lambda x: x[0], reverse=True)[0][1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()

    # SECURITY PROPERTY: read gates from BASE, not proposed HEAD.
    # A workstream cannot unlock itself inside the same PR it is trying to merge.
    registry = load_json_from_ref(args.base, "control/workstreams.json")
    workstreams = registry["workstreams"]
    files = changed_files(args.base, args.head)

    violations = []
    unmapped = []
    seen = set()

    for path in files:
        ws = owner_for_path(path, workstreams)
        if ws is None:
            # Root/control-independent docs are allowed but surfaced for review.
            unmapped.append(path)
            continue
        key = ws["code"]
        if key in seen:
            continue
        seen.add(key)
        gate = ws.get("gate", "BLOCKED")
        if gate in BLOCKING_GATES or gate not in ALLOWED_GATES:
            violations.append((key, ws.get("name", ""), gate))
        else:
            print(f"ALLOW {key}: gate={gate} mode={ws.get('execution_mode')}")

    if unmapped:
        print("NOTICE: changed paths without workstream mapping:")
        for p in unmapped:
            print(f"  - {p}")

    if violations:
        print("\nIAS GOVERNANCE GATE: BLOCKED", file=sys.stderr)
        for code, name, gate in violations:
            print(f"  - {code} {name}: gate={gate}", file=sys.stderr)
        print("\nUnlock/reopen must be committed to the base branch through the authorized Control Plane before this work PR can pass.", file=sys.stderr)
        return 42

    print("\nIAS GOVERNANCE GATE: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
