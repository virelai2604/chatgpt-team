<div align="center">

# 💰 Workstation Build — Price Comparison

### Original decision record vs. revised specification

**Region** Indonesia · **Prepared** 2026-08-06 · Planning ranges, not quotations

</div>

---

## Bottom line

| | Original | **Revised** | Saved |
|---|---:|---:|---:|
| **Complete environment** | Rp 142–225 juta | **Rp 130–215 juta** | **Rp 10–12 juta** |
| Core tower only | Rp 80–105 juta | **Rp 68–92 juta** | Rp 12–13 juta |

**Nothing was cut to save money.** Every reduction comes from a part that was over-provisioned for its job, or duplicated by another part already in the build.

---

## Line-by-line

| Component | Original | Revised | Δ | Why the price changed |
|---|---:|---:|---:|---|
| **Memory** | Rp 7.5–11 juta | **Rp 4–6 juta** | **−Rp 3–5 juta** | Switched from 128 GB (2×64 GB) to **96 GB (2×48 GB)**. 64 GB DDR5 modules are dual-rank and rarely hold rated speed on AM5; 48 GB modules do, at tighter timings and lower voltage. The workload doesn't reach the 128 GB threshold. |
| **Archive NVMe** | Rp 5.5–7.5 juta | **Rp 0** | **−Rp 5.5–7.5 juta** | The third 4 TB SSD was **deferred**. Its contents are archive data the 24 TB NAS already holds — with parity and snapshots the internal drive can't provide. Buy it later only if a measured bottleneck appears. |
| **GPU (RTX 5080)** | Rp 27–32 juta | **Rp 24–30 juta** | **−Rp 3 juta** | Budget was **over-provisioned**. Verified Indonesian street pricing sits near Rp 24 juta, up to ≈Rp 30 juta for premium models. |
| **NAS + drives** | Rp 35–55 juta | Rp 35–58 juta | +Rp 0–3 juta | Ceiling raised slightly to cover a **DS1525+ substitution** if the DS923+ is unavailable (the DS925+ can't do 10 GbE). |
| Cooler | same | same | None | Corrected to the **LBC** variant — same price, better fit for AM5. |
| PSU | same | same | None | 1,200 W **kept** — justified as RTX 5090 headroom, not 5080 sizing. |
| CPU · board · storage · case · fans · UPS · offline drives | unchanged | unchanged | — | — |

---

## Why prices moved — the short version

**⬇️ Memory got cheaper because bigger isn't better here.**
128 GB sounds like more headroom, but two 64 GB sticks stress the AM5 memory controller and usually won't run at their advertised speed. Two 48 GB sticks are faster *and* cheaper. You lose 32 GB of capacity the workload never uses.

**⬇️ The archive SSD disappeared because it was a duplicate.**
The build already includes a 24 TB NAS whose entire job is archive and backup. A third internal SSD doing the same thing — with no parity, in the same box, on the same power — was paying twice for one job.

**⬇️ The GPU line came down because the budget was too high.**
Nothing changed about the card. The original just budgeted Rp 27–32 juta for an RTX 5080 that actually sells for Rp 24–30 juta in Indonesia.

**↔️ The NAS line ticked up as insurance.**
Not a real cost increase — headroom in case you can't find the older DS923+ and have to buy the DS1525+, which is the only current model that still reaches 10 GbE.

---

## ⚠️ Price-trend warning

GPU prices in Indonesia moved **upward** through 2026, not down.

| Card | Launch (SRP) | Now |
|---|---:|---:|
| RTX 5080 | Rp 20.3 juta | ≈Rp 24 juta (to ~30 for premium) |
| RTX 5090 | Rp 40.8 juta | Rp 46–65 juta |

**If the RTX 5090 upgrade is genuinely likely, waiting is more likely to cost than save.**

---

<div align="center">

*All rupiah figures are planning estimates — re-check at purchase, GPU pricing moves weekly.*
*Full spec: `ai-workstation-build-spec.md`*

</div>
