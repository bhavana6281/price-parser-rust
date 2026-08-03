#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def as_int(node: ET.Element, name: str) -> int:
    return int(float(node.attrib.get(name, "0")))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("xml", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    root = ET.parse(args.xml).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    tests = sum(as_int(suite, "tests") for suite in suites)
    failures = sum(as_int(suite, "failures") for suite in suites)
    errors = sum(as_int(suite, "errors") for suite in suites)
    skipped = sum(as_int(suite, "skipped") for suite in suites)
    passed = tests - failures - errors - skipped
    executed = passed + failures + errors
    report = {
        "tests": tests,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "skipped_or_xfailed": skipped,
        "executed_pass_rate_percent": round(100 * passed / executed, 4) if executed else None,
        "source": str(args.xml),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
