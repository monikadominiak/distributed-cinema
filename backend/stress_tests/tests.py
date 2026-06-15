"""
Cinema Reservation System — Stress Tests
=========================================
Run against a live node:  python stress_tests.py --base-url http://localhost:8000
Run against all 3 nodes:  python stress_tests.py --base-url http://localhost:8000 http://localhost:8001 http://localhost:8002

Dependencies:
    pip install httpx rich

Each test prints a summary table with latencies and a pass/fail verdict.
"""

import asyncio
import random
import time
import argparse
from collections import Counter, defaultdict

import httpx
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()

# ── helpers ────────────────────────────────────────────────────────────────────

SEATS_CACHE: list[str] = []

async def fetch_seats(base: str) -> list[str]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{base}/seats")
        r.raise_for_status()
        return [s["seat"] for s in r.json()]

async def reset_all(base: str, seats: list[str]) -> None:
    """Cancel every ACTIVE reservation so tests start clean."""
    console.print(f"[dim]Resetting all reservations on {base}…[/dim]")
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(f"{base}/bulk-cancel", json={"seat_numbers": seats})

def make_payload(seat: str, tag: str = "test") -> dict:
    return {
        "seat_number": seat,
        "customer_name": f"User-{tag}-{random.randint(1000,9999)}",
        "customer_email": f"user{random.randint(1,999)}@test.com",
        "movie_id": "MOVIE-001"
    }

def print_summary(title: str, results: list[dict]) -> None:
    ok      = [r for r in results if r["status"] in (200, 201)]
    conflict= [r for r in results if r["status"] == 409]
    errors  = [r for r in results if r["status"] not in (200, 201, 409)]
    latencies = [r["latency"] for r in results]
    avg_ms  = (sum(latencies) / len(latencies) * 1000) if latencies else 0
    max_ms  = (max(latencies) * 1000) if latencies else 0

    t = Table(title=title, show_header=True, header_style="bold cyan")
    t.add_column("Metric", style="bold")
    t.add_column("Value")
    t.add_row("Total requests",  str(len(results)))
    t.add_row("✅ Success (2xx)", str(len(ok)))
    t.add_row("⚔️  Conflict (409)", str(len(conflict)))
    t.add_row("❌ Errors",        str(len(errors)))
    t.add_row("Avg latency",     f"{avg_ms:.1f} ms")
    t.add_row("Max latency",     f"{max_ms:.1f} ms")
    console.print(t)

    if errors:
        sample = Counter(r["status"] for r in errors)
        console.print(f"[red]Error status codes: {dict(sample)}[/red]")

# ── Test 1: Same request very quickly (single client hammering one seat) ───────

async def stress_test_1(base: str, seats: list[str], n: int = 200) -> None:
    """
    ST-1: One client fires the same reservation request N times as fast as possible.
    Expected: exactly 1 success, rest 409. No 5xx.
    """
    seat = seats[0]
    await reset_all(base, seats)

    async def reserve(client: httpx.AsyncClient):
        t0 = time.perf_counter()
        try:
            r = await client.post(f"{base}/reservations", json=make_payload(seat, "st1"))
            return {"status": r.status_code, "latency": time.perf_counter() - t0}
        except Exception as e:
            return {"status": 500, "latency": time.perf_counter() - t0, "error": str(e)}

    async with httpx.AsyncClient(timeout=15) as client:
        tasks = [reserve(client) for _ in range(n)]
        results = await asyncio.gather(*tasks)

    print_summary(f"ST-1 — Same seat hammered {n}× from 1 client", list(results))

    success_count = sum(1 for r in results if r["status"] in (200, 201))
    if success_count == 1:
        rprint("[green bold]✔ ST-1 PASS — exactly 1 seat reserved[/green bold]")
    else:
        rprint(f"[red bold]✘ ST-1 FAIL — {success_count} reservations created for 1 seat[/red bold]")

# ── Test 2: Two+ clients make random requests ──────────────────────────────────

async def stress_test_2(bases: list[str], seats: list[str], n_per_client: int = 150) -> None:
    """
    ST-2: Multiple clients (one per node) each fire random reserve/update/cancel
    requests concurrently.
    Expected: no 5xx, all 2xx or 4xx responses, system remains consistent.
    """
    await reset_all(bases[0], seats)

    async def random_action(client: httpx.AsyncClient, base: str, seat: str):
        action = random.choice(["reserve", "update", "cancel", "read"])
        t0 = time.perf_counter()
        try:
            if action == "reserve":
                r = await client.post(f"{base}/reservations", json=make_payload(seat, "st2"))
            elif action == "update":
                r = await client.put(f"{base}/reservations/{seat}", json={
                    "customer_name": f"Updated-{random.randint(0,999)}",
                    "customer_email": "upd@test.com"
                })
            elif action == "cancel":
                r = await client.delete(f"{base}/reservations/{seat}")
            else:
                r = await client.get(f"{base}/reservations/{seat}")
            return {"status": r.status_code, "action": action, "latency": time.perf_counter() - t0}
        except Exception as e:
            return {"status": 500, "action": action, "latency": time.perf_counter() - t0, "error": str(e)}

    all_results = []
    async with httpx.AsyncClient(timeout=15) as client:
        tasks = []
        for i in range(n_per_client * len(bases)):
            base = bases[i % len(bases)]
            seat = random.choice(seats)
            tasks.append(random_action(client, base, seat))
        all_results = await asyncio.gather(*tasks)

    print_summary(f"ST-2 — {len(all_results)} random ops across {len(bases)} node(s)", all_results)

    errors = [r for r in all_results if r["status"] >= 500]
    if not errors:
        rprint("[green bold]✔ ST-2 PASS — no 5xx errors[/green bold]")
    else:
        rprint(f"[red bold]✘ ST-2 FAIL — {len(errors)} server errors[/red bold]")

# ── Test 3: Two clients race to occupy ALL seats ───────────────────────────────

async def stress_test_3(bases: list[str], seats: list[str]) -> None:
    """
    ST-3: Two clients (hitting different nodes) simultaneously try to reserve
    every seat. LWT must ensure each seat goes to exactly one client.
    Expected: total successes == len(seats), each seat reserved exactly once.
    """
    await reset_all(bases[0], seats)

    base_a = bases[0]
    base_b = bases[1] if len(bases) > 1 else bases[0]

    async def reserve_all(client: httpx.AsyncClient, base: str, label: str):
        results = []
        shuffled = seats.copy()
        random.shuffle(shuffled)
        for seat in shuffled:
            t0 = time.perf_counter()
            try:
                r = await client.post(f"{base}/reservations", json=make_payload(seat, label))
                results.append({"status": r.status_code, "seat": seat, "client": label, "latency": time.perf_counter() - t0})
            except Exception as e:
                results.append({"status": 500, "seat": seat, "client": label, "latency": time.perf_counter() - t0})
        return results

    async with httpx.AsyncClient(timeout=30) as client:
        ra, rb = await asyncio.gather(
            reserve_all(client, base_a, "ClientA"),
            reserve_all(client, base_b, "ClientB"),
        )

    all_results = ra + rb
    print_summary("ST-3 — Two clients race for all seats", all_results)

    # Verify: each seat must have exactly 1 success
    seat_wins: dict[str, list] = defaultdict(list)
    for r in all_results:
        if r["status"] in (200, 201):
            seat_wins[r["seat"]].append(r["client"])

    double_booked = {s: w for s, w in seat_wins.items() if len(w) > 1}
    unbooked      = [s for s in seats if s not in seat_wins]
    a_wins = sum(1 for w in seat_wins.values() if w == ["ClientA"])
    b_wins = sum(1 for w in seat_wins.values() if w == ["ClientB"])

    t = Table(title="ST-3 Seat distribution", header_style="bold magenta")
    t.add_column("Metric"); t.add_column("Value")
    t.add_row("Seats total",        str(len(seats)))
    t.add_row("Client A reservations", str(a_wins))
    t.add_row("Client B reservations", str(b_wins))
    t.add_row("Double-booked seats", str(len(double_booked)))
    t.add_row("Unbooked seats",      str(len(unbooked)))
    console.print(t)

    if not double_booked and a_wins > 0 and b_wins > 0:
        rprint("[green bold]✔ ST-3 PASS — no double bookings, both clients got seats[/green bold]")
    elif double_booked:
        rprint(f"[red bold]✘ ST-3 FAIL — {len(double_booked)} seats double-booked: {list(double_booked.keys())[:5]}[/red bold]")
    else:
        rprint(f"[yellow bold]⚠ ST-3 PARTIAL — no double bookings but one client got 0 seats[/yellow bold]")

# ── Test 4: Constant cancellations and re-occupancy ───────────────────────────

async def stress_test_4(bases: list[str], seats: list[str], duration_s: int = 20) -> None:
    """
    ST-4 (pairs): One goroutine constantly cancels, another constantly reserves.
    Run for `duration_s` seconds.
    Expected: no 5xx, system stable under churn.
    """
    await reset_all(bases[0], seats)
    stop = asyncio.Event()
    all_results = []
    lock = asyncio.Lock()

    base_reserver = bases[0]
    base_canceller = bases[1] if len(bases) > 1 else bases[0]

    async def reserver(client: httpx.AsyncClient):
        while not stop.is_set():
            seat = random.choice(seats)
            t0 = time.perf_counter()
            try:
                r = await client.post(f"{base_reserver}/reservations", json=make_payload(seat, "st4r"))
                async with lock:
                    all_results.append({"status": r.status_code, "op": "reserve", "latency": time.perf_counter() - t0})
            except Exception:
                async with lock:
                    all_results.append({"status": 500, "op": "reserve", "latency": time.perf_counter() - t0})
            await asyncio.sleep(0)  # yield

    async def canceller(client: httpx.AsyncClient):
        while not stop.is_set():
            seat = random.choice(seats)
            t0 = time.perf_counter()
            try:
                r = await client.delete(f"{base_canceller}/reservations/{seat}")
                async with lock:
                    all_results.append({"status": r.status_code, "op": "cancel", "latency": time.perf_counter() - t0})
            except Exception:
                async with lock:
                    all_results.append({"status": 500, "op": "cancel", "latency": time.perf_counter() - t0})
            await asyncio.sleep(0)

    async with httpx.AsyncClient(timeout=15) as client:
        t = asyncio.create_task(asyncio.sleep(duration_s))
        r_task = asyncio.create_task(reserver(client))
        c_task = asyncio.create_task(canceller(client))
        await t
        stop.set()
        await asyncio.gather(r_task, c_task, return_exceptions=True)

    print_summary(f"ST-4 — Churn for {duration_s}s (reserve + cancel)", all_results)
    errors = [r for r in all_results if r["status"] >= 500]
    if not errors:
        rprint("[green bold]✔ ST-4 PASS — no 5xx during churn[/green bold]")
    else:
        rprint(f"[red bold]✘ ST-4 FAIL — {len(errors)} server errors[/red bold]")

# ── Test 5: Large group bulk-cancel ───────────────────────────────────────────

async def stress_test_5(base: str, seats: list[str]) -> None:
    """
    ST-5 (pairs): Fill all seats, then fire many concurrent bulk-cancel requests
    covering overlapping seat ranges.
    Expected: all seats end up CANCELLED exactly once, no 5xx.
    """
    # First fill all seats
    console.print("[dim]ST-5: filling all seats…[/dim]")
    async with httpx.AsyncClient(timeout=30) as client:
        tasks = [
            client.post(f"{base}/reservations", json=make_payload(s, "st5"))
            for s in seats
        ]
        await asyncio.gather(*tasks)

    # Split seats into overlapping chunks for concurrent bulk-cancel
    chunk = max(1, len(seats) // 4)
    chunks = [seats[i:i+chunk] for i in range(0, len(seats), chunk)]
    # Add two fully overlapping chunks to provoke duplicate cancel attempts
    chunks.append(seats[:chunk])
    chunks.append(seats)  # one request cancels everything

    results = []
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=30) as client:
        tasks = [
            client.post(f"{base}/bulk-cancel", json={"seat_numbers": c})
            for c in chunks
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    for r in responses:
        if isinstance(r, Exception):
            results.append({"status": 500, "latency": 0})
        else:
            results.append({"status": r.status_code, "latency": time.perf_counter() - t0})

    print_summary("ST-5 — Concurrent bulk-cancel (overlapping seat ranges)", results)

    # Verify all seats are now CANCELLED
    async with httpx.AsyncClient(timeout=15) as client:
        all_r = await client.get(f"{base}/reservations")
        active = [r for r in all_r.json() if r.get("status") == "ACTIVE"]

    if not active:
        rprint("[green bold]✔ ST-5 PASS — all seats cancelled[/green bold]")
    else:
        rprint(f"[yellow bold]⚠ ST-5 PARTIAL — {len(active)} seats still ACTIVE after bulk cancel[/yellow bold]")

# ── Entry point ────────────────────────────────────────────────────────────────

async def main(bases: list[str]) -> None:
    global SEATS_CACHE
    SEATS_CACHE = await fetch_seats(bases[0])
    console.print(f"[cyan]Loaded {len(SEATS_CACHE)} seats from {bases[0]}[/cyan]")
    console.print(f"[cyan]Nodes under test: {bases}[/cyan]\n")

    console.rule("[bold yellow]Stress Test 1[/bold yellow]")
    await stress_test_1(bases[0], SEATS_CACHE, n=200)

    console.rule("[bold yellow]Stress Test 2[/bold yellow]")
    await stress_test_2(bases, SEATS_CACHE, n_per_client=150)

    console.rule("[bold yellow]Stress Test 3[/bold yellow]")
    await stress_test_3(bases, SEATS_CACHE)

    console.rule("[bold yellow]Stress Test 4 (pairs)[/bold yellow]")
    await stress_test_4(bases, SEATS_CACHE, duration_s=20)

    console.rule("[bold yellow]Stress Test 5 (pairs)[/bold yellow]")
    await stress_test_5(bases[0], SEATS_CACHE)

    console.rule("[bold green]All stress tests complete[/bold green]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cinema reservation stress tests")
    parser.add_argument(
        "--base-url", nargs="+",
        default=["http://localhost:8000"],
        help="Base URL(s) of API nodes, e.g. http://localhost:8000 http://localhost:8001"
    )
    args = parser.parse_args()
    asyncio.run(main(args.base_url))