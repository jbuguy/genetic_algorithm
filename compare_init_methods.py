#!/usr/bin/env python3
"""
Compare initialization methods by number of vehicles, distance, and wait time.
Results are grouped by instance family (R, C, RC) and variant (1, 2).
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from vrptw.instance import Instance
from vrptw.generateInit import (
    random_generator,
    solomon_generator,
    cluster_first_route_second,
    savings_heuristic,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def parse_instance_name(filename: str) -> Optional[Tuple[str, str]]:
    """
    Extract (family, variant) from a Solomon-style filename.

    Examples
    --------
    R101.txt  → ("R",  "1")
    C205.txt  → ("C",  "2")
    RC102.txt → ("RC", "1")

    Returns None if the name doesn't match the expected pattern.
    """
    stem = Path(filename).stem.upper()
    match = re.match(r'^(RC|R|C)([12])\d*$', stem)
    if not match:
        return None
    return match.group(1), match.group(2)


def calculate_metrics(
    solution: List[int], instance: Instance
) -> Tuple[int, float, float]:
    """
    Return (num_vehicles, total_distance, total_wait) for a solution,
    or (0, inf, inf) if the solution is infeasible.
    """
    if not solution or solution[0] != 0:
        return 0, float("inf"), float("inf")

    total_distance = 0.0
    total_wait = 0.0
    current_time = 0.0
    current_load = 0
    current_location = 0
    visited: set = set()
    num_vehicles = 0

    for node in solution[1:]:
        if node == 0:
            total_distance += instance.distances[current_location][0]
            current_time = 0.0
            current_load = 0
            current_location = 0
            num_vehicles += 1
            continue

        if node in visited:
            return 0, float("inf"), float("inf")

        customer = instance.customer_map.get(node)
        if not customer:
            return 0, float("inf"), float("inf")

        if current_load + customer.demand > instance.capacity:
            return 0, float("inf"), float("inf")

        travel_time = instance.distances[current_location][node]
        arrival_time = current_time + travel_time

        if arrival_time > customer.dueDate:
            return 0, float("inf"), float("inf")

        wait_time = max(0.0, customer.readyTime - arrival_time)
        total_wait += wait_time
        total_distance += travel_time
        current_time = arrival_time + wait_time + customer.serviceTime
        current_load += customer.demand
        current_location = node
        visited.add(node)

    if current_location != 0:
        total_distance += instance.distances[current_location][0]
        num_vehicles += 1

    if visited != instance.customer_ids:
        return 0, float("inf"), float("inf")

    return num_vehicles, total_distance, total_wait


# ── printing helpers ──────────────────────────────────────────────────────────

COL_METHOD   = 20
COL_VEHICLES = 12
COL_DIST     = 15
COL_WAIT     = 15
ROW_WIDTH    = COL_METHOD + COL_VEHICLES + COL_DIST + COL_WAIT + 6

METHODS = {
    "Random":        random_generator,
    "Solomon":       solomon_generator,
    "Cluster-First": cluster_first_route_second,
    "Savings":       savings_heuristic,
}


def header_row() -> str:
    return (
        f"{'Method':<{COL_METHOD}}"
        f"{'Vehicles':>{COL_VEHICLES}}"
        f"{'Distance':>{COL_DIST}}"
        f"{'Wait Time':>{COL_WAIT}}"
    )


def data_row(method: str, vehicles, distance, wait) -> str:
    return (
        f"{method:<{COL_METHOD}}"
        f"{str(vehicles):>{COL_VEHICLES}}"
        f"{str(distance):>{COL_DIST}}"
        f"{str(wait):>{COL_WAIT}}"
    )


def avg_row(method: str, avg_v: float, avg_d: float, avg_w: float) -> str:
    return (
        f"{method:<{COL_METHOD}}"
        f"{avg_v:>{COL_VEHICLES}.2f}"
        f"{avg_d:>{COL_DIST}.2f}"
        f"{avg_w:>{COL_WAIT}.2f}"
    )


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    data_dir = Path("data")
    all_files = sorted(data_dir.glob("*.txt"))

    if not all_files:
        print("No instances found in data/ directory")
        return

    # ── Step 1: bucket files by (family, variant) ────────────────────────────
    # buckets[(family, variant)] = [Path, ...]
    buckets: Dict[Tuple[str, str], List[Path]] = defaultdict(list)
    skipped = []

    for f in all_files:
        key = parse_instance_name(f.name)
        if key:
            buckets[key].append(f)
        else:
            skipped.append(f.name)

    if skipped:
        print(f"Skipped (unrecognised naming): {', '.join(skipped)}\n")

    total_instances = sum(len(v) for v in buckets.values())
    print(f"Found {total_instances} instances across "
          f"{len(buckets)} groups: "
          + ", ".join(
              f"{fam}{var}({len(buckets[(fam,var)])})"
              for fam, var in sorted(buckets)
          )
    )

    # ── Step 2: solve every instance ─────────────────────────────────────────
    # raw_results[(family, variant)][instance_name][method_name] = metrics dict
    raw_results: Dict[Tuple[str, str], Dict[str, Dict]] = defaultdict(dict)

    for (fam, var), files in sorted(buckets.items()):
        print(f"\n── Group {fam}{var}: processing {len(files)} instance(s) ──")
        for instance_file in files:
            print(f"   {instance_file.name} ...", end=" ", flush=True)
            instance = Instance(str(instance_file))
            per_method: Dict[str, dict] = {}

            for method_name, method_func in METHODS.items():
                try:
                    solution = method_func(instance)
                    num_v, dist, wait = calculate_metrics(solution, instance)
                    per_method[method_name] = {
                        "vehicles": num_v,
                        "distance": round(dist, 2),
                        "wait_time": round(wait, 2),
                    }
                except Exception as exc:
                    per_method[method_name] = {
                        "vehicles": "ERR",
                        "distance": "ERR",
                        "wait_time": str(exc)[:25],
                    }

            raw_results[(fam, var)][instance_file.name] = per_method
            print("done")

    # ── Step 3: per-instance tables ───────────────────────────────────────────
    print("\n\n" + "=" * ROW_WIDTH)
    print("PER-INSTANCE RESULTS")
    print("=" * ROW_WIDTH)

    for (fam, var), instance_map in sorted(raw_results.items()):
        print(f"\n{'─'*ROW_WIDTH}")
        print(f"  Group: {fam}{var}")
        print(f"{'─'*ROW_WIDTH}")

        for inst_name, results in sorted(instance_map.items()):
            print(f"\n  Instance: {inst_name}")
            print(f"  {'-'*(ROW_WIDTH-2)}")
            print(f"  {header_row()}")
            print(f"  {'-'*(ROW_WIDTH-2)}")
            for m in METHODS:
                r = results[m]
                print("  " + data_row(m, r["vehicles"], r["distance"], r["wait_time"]))

    # ── Step 4: group-level average summary ───────────────────────────────────
    print("\n\n" + "=" * ROW_WIDTH)
    print("AVERAGE METRICS BY GROUP  (only feasible runs counted)")
    print("=" * ROW_WIDTH)

    # Column headers: one per group
    sorted_keys = sorted(raw_results.keys())
    group_labels = [f"{fam}{var}" for fam, var in sorted_keys]

    # For each (group, method) accumulate feasible results
    # accum[(group_key)][method] = {"vehicles": [], "distance": [], "wait": []}
    accum: Dict[Tuple, Dict[str, Dict[str, List[float]]]] = {}
    for key in sorted_keys:
        accum[key] = {m: {"vehicles": [], "distance": [], "wait": []} for m in METHODS}
        for inst_results in raw_results[key].values():
            for m in METHODS:
                r = inst_results[m]
                if isinstance(r["vehicles"], int) and r["distance"] != float("inf"):
                    accum[key][m]["vehicles"].append(r["vehicles"])
                    accum[key][m]["distance"].append(r["distance"])
                    accum[key][m]["wait"].append(r["wait_time"])

    def safe_avg(lst: List[float]) -> str:
        return f"{sum(lst)/len(lst):.2f}" if lst else "N/A"

    # Print one sub-table per group
    for key in sorted_keys:
        fam, var = key
        n_inst = len(raw_results[key])
        print(f"\n  Group {fam}{var}  ({n_inst} instance(s))")
        print(f"  {'-'*(ROW_WIDTH-2)}")
        print(f"  {header_row()}")
        print(f"  {'-'*(ROW_WIDTH-2)}")
        for m in METHODS:
            a = accum[key][m]
            print("  " + data_row(
                m,
                safe_avg(a["vehicles"]),
                safe_avg(a["distance"]),
                safe_avg(a["wait"]),
            ))

    # ── Step 5: cross-group comparison (one row per method) ───────────────────
    # Build a wide table: rows = methods, column groups = R1 / R2 / C1 / C2 / RC1 / RC2
    print("\n\n" + "=" * ROW_WIDTH)
    print("CROSS-GROUP COMPARISON  (avg distance  |  avg vehicles)")
    print("=" * ROW_WIDTH)

    # Determine how many groups we have and build dynamic column widths
    col_w = 18  # width per group column
    header = f"{'Method':<{COL_METHOD}}" + "".join(f"{g:>{col_w}}" for g in group_labels)
    print(f"\n  {header}")
    print(f"  {'-'*(COL_METHOD + col_w * len(group_labels))}")

    for m in METHODS:
        row = f"{m:<{COL_METHOD}}"
        for key in sorted_keys:
            a = accum[key][m]
            avg_d = safe_avg(a["distance"])
            avg_v = safe_avg(a["vehicles"])
            cell = f"{avg_d} / {avg_v}"
            row += f"{cell:>{col_w}}"
        print(f"  {row}")

    print(f"\n  (format: avg_distance / avg_vehicles)\n")


if __name__ == "__main__":
    main()