#!/usr/bin/env python3
"""Thailand IP forensic analysis + report generator.

Reads a TOU_ip_located CSV (geolocated IP hits) and emits a Markdown
forensic report for the Thailand (TH) subset: summary stats, timeline,
provenance/org breakdowns, and a full per-IP detail table.

Usage:  python3 th_report.py <input.csv> [output.md]
BOM-safe, tolerant of missing/None columns and schema drift.
"""
import csv, sys, os
from collections import Counter, defaultdict

def g(r, *keys):
    for k in keys:
        v = (r.get(k) or "").strip()
        if v:
            return v
    return ""

def to_int(s, default=0):
    try:
        return int(str(s).strip())
    except (ValueError, TypeError):
        return default

def load_th(path, cc="TH"):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if g(r, "countryCode").upper() == cc]

def build_report(rows, source):
    n = len(rows)
    total_hits = sum(to_int(g(r, "hits_deduped")) for r in rows)
    dates = sorted(d for d in (g(r, "first_date") for r in rows) if d)
    ldates = sorted(d for d in (g(r, "last_date") for r in rows) if d)
    span_lo = dates[0] if dates else "-"
    span_hi = ldates[-1] if ldates else (dates[-1] if dates else "-")
    ipv6 = sum(1 for r in rows if ":" in g(r, "ip"))

    prov = Counter(g(r, "provenance") or "(none)" for r in rows)
    orgs = Counter(g(r, "org", "isp") or "(unknown)" for r in rows)
    hits_by_org = defaultdict(int)
    for r in rows:
        hits_by_org[g(r, "org", "isp") or "(unknown)"] += to_int(g(r, "hits_deduped"))

    rows_sorted = sorted(rows, key=lambda r: (g(r, "first_date") == "", g(r, "first_date")))
    top_by_hits = sorted(rows, key=lambda r: -to_int(g(r, "hits_deduped")))[:10]

    L = []
    w = L.append
    w("# Thailand (TH) IP Forensic Analysis\n")
    w(f"**Source:** `{os.path.basename(source)}`  ")
    w(f"**Scope:** country code `TH`\n")

    w("## 1. Summary\n")
    w("| Metric | Value |")
    w("|---|---|")
    w(f"| Distinct TH IPs | {n} |")
    w(f"| Total deduped hits | {total_hits} |")
    w(f"| Activity window | {span_lo} → {span_hi} |")
    w(f"| IPv6 addresses | {ipv6} |")
    w(f"| Distinct orgs/ISPs | {len(orgs)} |")
    w(f"| Distinct provenance sources | {len(prov)} |\n")

    w("## 2. Provenance (evidence source)\n")
    w("| Source | IPs | Share |")
    w("|---|---:|---:|")
    for src, c in prov.most_common():
        w(f"| {src} | {c} | {c/n*100:.0f}% |")
    w("")

    w("## 3. Organizations / ISPs\n")
    w("| Org / ISP | IPs | Deduped hits |")
    w("|---|---:|---:|")
    for org, c in orgs.most_common():
        w(f"| {org} | {c} | {hits_by_org[org]} |")
    w("")

    w("## 4. Top IPs by activity\n")
    w("| IP | Hits | First | Last | Provenance | Org/ISP |")
    w("|---|---:|---|---|---|---|")
    for r in top_by_hits:
        w("| `%s` | %s | %s | %s | %s | %s |" % (
            g(r, "ip"), to_int(g(r, "hits_deduped")),
            g(r, "first_date") or "-", g(r, "last_date") or "-",
            g(r, "provenance") or "-", (g(r, "org", "isp") or "-")[:40]))
    w("")

    w("## 5. Full detail (chronological by first-seen)\n")
    w("| IP | Hits | First | Last | Provenance | Org/ISP |")
    w("|---|---:|---|---|---|---|")
    for r in rows_sorted:
        w("| `%s` | %s | %s | %s | %s | %s |" % (
            g(r, "ip"), to_int(g(r, "hits_deduped")),
            g(r, "first_date") or "-", g(r, "last_date") or "-",
            g(r, "provenance") or "-", (g(r, "org", "isp") or "-")[:40]))
    w("")
    return "\n".join(L)

def main(argv):
    if len(argv) < 2:
        print("usage: python3 th_report.py <input.csv> [output.md]", file=sys.stderr)
        return 2
    src = argv[1]
    out = argv[2] if len(argv) > 2 else os.path.splitext(src)[0] + "_TH_report.md"
    rows = load_th(src)
    md = build_report(rows, src)
    with open(out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Wrote {out}  ({len(rows)} TH rows)", file=sys.stderr)
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
