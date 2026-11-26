"""Seal the exact private reply bytes or check an existing anonymous receipt."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys


TEXT_FIELDS = {"intent", "target", "view_time", "acceptance", "tie_none", "next_action"}


def distinct_keys(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def disposition(reply):
    if not isinstance(reply, dict) or reply.get("schema") != "fx-brief-v1":
        raise ValueError("unrecognized reply schema")
    if reply.get("response") == "declined" and set(reply) == {"schema", "response"}:
        return "declined"
    fields = {"schema", "response", "brief", "role", "exposure", "endorsed"}
    if reply.get("response") != "brief" or set(reply) != fields:
        raise ValueError("unexpected response fields")
    brief = reply["brief"]
    if not isinstance(brief, dict) or set(brief) != TEXT_FIELDS:
        raise ValueError("incomplete brief")
    if any(not isinstance(s, str) or not s.strip() for s in brief.values()):
        raise ValueError("empty or invalid brief text")
    if reply["role"] not in ("independent_fx", "involved", "other_or_unsure"):
        raise ValueError("unrecognized role response")
    if reply["exposure"] not in ("unseen", "seen", "unsure") or reply["endorsed"] is not True:
        raise ValueError("invalid exposure or endorsement response")
    if reply["role"] == "independent_fx" and reply["exposure"] == "unseen":
        return "eligible_by_self_report"
    return "outside_prospective_intake"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reply", type=Path, help="original private UTF-8 JSON export")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--seal", metavar="NEW_RECEIPT", type=Path)
    mode.add_argument("--verify", metavar="EXISTING_RECEIPT", type=Path)
    args = parser.parse_args()
    raw = args.reply.read_bytes()
    reply = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=distinct_keys)
    facts = {"schema": "fx-brief-receipt-v1", "sha256": hashlib.sha256(raw).hexdigest(),
             "bytes": len(raw), "disposition": disposition(reply)}
    if args.seal:
        receipt = {**facts, "sealed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        with args.seal.open("x", encoding="utf-8", newline="\n") as dest:
            dest.write(json.dumps(receipt, indent=2) + "\n")
        print(f"Sealed ({facts['disposition']}).")
        return
    receipt = json.loads(args.verify.read_bytes(), object_pairs_hook=distinct_keys)
    if not isinstance(receipt, dict) or set(receipt) != set(facts) | {"sealed_utc"}:
        raise ValueError("unexpected receipt structure")
    if any(type(receipt[k]) is not type(v) or receipt[k] != v for k, v in facts.items()):
        raise ValueError("receipt does not match the reply bytes or disposition")
    when = datetime.fromisoformat(receipt["sealed_utc"])
    if when.tzinfo is None or when.utcoffset().total_seconds() != 0:
        raise ValueError("receipt has no UTC timestamp")
    print(f"Verified ({facts['disposition']}).")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, TypeError) as error:
        sys.exit(f"Invalid reply or receipt: {error}")
