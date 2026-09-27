# ai-generated: 100% - generated with ChatGPT to validate the Lab 2 svcdesk API

import json
import os
import sys
import time
import urllib.error
import urllib.request


BASE_URL = os.getenv("SVCDESK_URL", "http://svcdesk:8080")


def request(method, path, body=None, headers=None):
    url = BASE_URL + path

    data = None
    request_headers = {
        "Content-Type": "application/json",
    }

    if headers:
        request_headers.update(headers)

    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers=request_headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")

            if content:
                return response.status, json.loads(content)

            return response.status, None

    except urllib.error.HTTPError as exc:
        content = exc.read().decode("utf-8")

        try:
            parsed = json.loads(content)
        except Exception:
            parsed = None

        return exc.code, parsed


def wait_for_service():
    for _ in range(30):
        try:
            status, _ = request("GET", "/health")

            if status == 200:
                return
        except Exception:
            pass

        time.sleep(1)

    raise RuntimeError("svcdesk did not become ready")


def run_tests():
    passed = 0
    failed = 0

    def check(condition, name):
        nonlocal passed, failed

        if condition:
            passed += 1
            print(f"PASS: {name}")
        else:
            failed += 1
            print(f"FAIL: {name}")

    wait_for_service()

    # 1
    status, body = request("GET", "/health")
    check(status == 200, "health status")

    # 2
    check(body == {"status": "ok", "service": "svcdesk"}, "health body")

    # 3
    status, body = request("GET", "/does-not-exist")
    check(status == 404, "unknown path")

    ticket_body = {
        "title": "Own tests ticket",
        "reporter": {
            "name": "Test User",
            "vip": False,
        },
        "impact": 1,
        "urgency": 1,
    }

    # 4
    status, ticket = request(
        "POST",
        "/tickets",
        ticket_body,
        {
            "X-Test-Clock": "2026-10-14T10:00:00Z",
        },
    )
    check(status == 201, "create ticket")

    ticket_id = ticket["id"]

    # 5
    check(ticket["priority"] == "P1", "priority matrix")

    # 6
    status, fetched = request("GET", f"/tickets/{ticket_id}")
    check(status == 200 and fetched["id"] == ticket_id, "get ticket")

    # 7
    status, _ = request(
        "POST",
        f"/tickets/{ticket_id}/ack",
        headers={
            "X-Test-Clock": "2026-10-14T10:05:00Z",
        },
    )
    check(status == 200, "ack ticket")

    # 8
    status, _ = request(
        "POST",
        f"/tickets/{ticket_id}/start",
        headers={
            "X-Test-Clock": "2026-10-14T10:06:00Z",
        },
    )
    check(status == 200, "start ticket")

    # 9
    status, _ = request(
        "POST",
        f"/tickets/{ticket_id}/resolve",
        headers={
            "X-Test-Clock": "2026-10-14T10:10:00Z",
        },
    )
    check(status == 200, "resolve ticket")

    # 10
    metrics_body = {
        "window": {
            "from": "2026-09-01T00:00:00Z",
            "to": "2026-09-22T00:00:00Z",
        },
        "events": [],
    }

    status, metrics = request(
        "POST",
        "/dora/metrics",
        metrics_body,
    )

    check(
        status == 200
        and metrics["deployment_frequency_per_day"] == 0.0
        and metrics["counts"]["deployments"] == 0,
        "empty DORA log",
    )

    print(f"ITSMLAB-TESTS: passed={passed} failed={failed}")

    return 0 if failed == 0 and passed >= 10 else 1


if __name__ == "__main__":
    sys.exit(run_tests())