<div align="center">

# 📊 Build Spec — What Changed & Why

### Original decision record → revised specification

**Compared** 2026-08-06 · Every change with its evidence, so each can be accepted or rejected individually

</div>

---

## At a glance

| | Original | Revised | Δ |
|---|---|---|---:|
| **Complete environment** | Rp 142–225 juta | **Rp 130–215 juta** | −Rp 10–12 juta |
| **Tower only** | Rp 80–105 juta | **Rp 68–92 juta** | −Rp 12–13 juta |
| Components changed | — | 4 | |
| New risks found | — | 2 | |
| Items verified | partial | 12 | |

**Nothing was cut for cost.** Every reduction comes from a component that was over-provisioned for its stated job, or duplicated by another component already in the build.

---

## 🔧 Changed components

### 1 · CPU cooler — wrong variant ordered

| | |
|---|---|
| **Original** | `NH-D15 G2 standard-base` or `chromax.black` |
| **Revised** | `NH-D15 G2 **LBC**` (Low Base Convexity) |
| **Cost impact** | **None** — same price |
| **Severity** | 🟡 Suboptimal, not broken |

The original checklist reads *"Cooler is the standard-base NH-D15 G2, not the HBC version intended primarily for highly convex Intel CPUs."* Ruling out HBC is right; the conclusion stops one step short.

Noctua ships **three** base-convexity variants. **LBC** achieves optimal contact on relatively flat CPUs and is documented by Noctua as **ideal for AM5**, specifically for combining the lowest possible CCD temperatures with the lowest possible IOD temperatures. Standard is the medium-convexity all-rounder; HBC targets de-shaped Intel 12th–14th gen under high ILM pressure.

Standard *works* on AM5. LBC is the manufacturer's stated optimum for this socket at identical cost. **The variant is engraved on the base — verify on receipt.**

> 📎 [Noctua — NH-D15 G2 versions explained](https://noctua.at/en/nh-d15-g2-versions-explained)

---

### 2 · Memory — 128 GB slow, or 96 GB fast?

| | Original | Revised |
|---|---|---|
| **Part** | G.Skill Flare X5 `F5-6000J3244G64GX2-FX5` | **`F5-6000J3036F48GX2-FX5`** |
| **Capacity** | 128 GB (2 × 64 GB) | 96 GB (2 × 48 GB) |
| **Rated timings** | CL32-44-44-96 | **CL30-36-36-96** |
| **Voltage** | 1.40 V | **1.35 V** |
| **Realistic stable speed** | ≈DDR5-5600 | **DDR5-6000** |
| **Cost** | Rp 7.5–11 juta | **Rp 4–6 juta** |
| **Saving** | | **≈Rp 3–5 juta** |

64 GB DDR5 UDIMMs are dual-rank and high-density — hard on the AM5 memory controller, and rarely stable at rated speed. 48 GB modules are a well-trodden AM5 configuration that genuinely runs at DDR5-6000. The revised kit is faster, cooler, cheaper, and far more likely to boot at its advertised profile.

**Keep 128 GB only if** the workload genuinely commits more than ~96 GB. The original document's own upgrade trigger sets that bar at *"sustained committed memory exceeds approximately 100–110 GB"* — which the documented workload does not currently reach. Two DIMM slots remain free in either case.

> ⚠️ The original also listed *"Kingston FURY Renegade Pro DDR5 ECC UDIMM if present on ASUS QVL"* as first preference. Treat as unlikely to be actionable — ECC UDIMM validation on AM5 consumer boards is inconsistent, and 2 × 64 GB ECC kits are rare. If ECC is a hard requirement, that is a Threadripper/W790 platform decision, not a DIMM substitution.

---

### 3 · Archive NVMe — duplicated by the NAS

| | |
|---|---|
| **Original** | 3rd × Samsung 990 PRO 4 TB (`MZ-V9P4T0BW`) at build time |
| **Revised** | Deferred behind a measured trigger; role moves to NAS |
| **Cost impact** | **−Rp 5.5–7.5 juta** |
| **Severity** | 🟡 Redundant spend |

The original buys a third 4 TB 990 PRO **and** a 24 TB dual-parity NAS **and** 40 TB of rotating offline capacity.

The NVMe's own defined contents — completed outputs, exports, snapshots, old models, rebuildable indexes, temporary ingestion — are archive-class data the NAS already holds, at 6× the capacity, with parity and snapshots the internal drive structurally cannot provide. The original states this itself: *"The third NVMe is not a backup. It is still inside the same computer."*

The original already applies exactly this reasoning to the **fourth** M.2 slot — *"Avoid buying unused flash too early; preserve expansion."* With a NAS in the build, that logic reaches the third slot too.

**Buy it when** the active 4 TB exceeds 75–80% after NAS offload · ingestion staging over 10 GbE becomes a *measured* bottleneck · write separation shows measurable benefit. A mid-tier Gen4 NVMe suffices then — archive workloads do not need 2,400 TBW.

---

### 4 · GPU budget line — over-provisioned

| | Original | Revised |
|---|---:|---:|
| RTX 5080 budget | Rp 27–32 juta | **Rp 24–30 juta** |

Indonesian street pricing, verified: RTX 5080 launched at Rp 20.3 juta SRP and sits near **Rp 24 juta**, reaching ≈Rp 30 juta for premium three-fan models. RTX 5090 launched at Rp 40.8 juta and now runs **Rp 46–65 juta**.

> **Trend note:** GPU pricing in Indonesia moved *upward* through 2026, not down. If the RTX 5090 upgrade path is genuinely likely, waiting is more likely to cost than save.

---

## 🚨 New risks found

### 5 · The DS925+ cannot do 10 GbE — build-breaking substitution

| | |
|---|---|
| **Severity** | 🔴 **Breaks the storage design** |
| **Status** | Not an error in the original — a change in the product line |

The DS923+ dates to 2022. Its successor, the **DS925+** (April 2025), **removed the PCIe expansion slot** — and that slot is the only path to 10 GbE on a DS923+, via the optional `E10G22-T1-Mini`. The DS925+ tops out at dual 2.5 GbE, ≈5 Gbps aggregated, and only for multi-stream traffic.

This build specifies a 10 GbE workstation↔NAS link. **A DS925+ cannot deliver it at any price.** Because deferring the archive NVMe (change 3) pushes staging traffic onto that link, the network speed is now load-bearing rather than a convenience.

The trap: a retailer offering "the current model" hands you exactly the unit that silently breaks the design.

| Option | 10 GbE | Bays | Verdict |
|---|:--:|:--:|---|
| **Synology DS923+** *(specified)* | ✅ via PCIe | 4 | Verify availability first |
| Synology DS925+ | ❌ **impossible** | 4 | **Do not substitute** |
| **Synology DS1525+** | ✅ upgrade slot | 5 | ≈+$160, extra bay — **the real successor** |
| **UGREEN DXP4800 Plus** | ✅ built-in | 4 | Faster hardware, non-Synology software |

> 📎 [Dong Knows Tech — DS925+ vs DS923+](https://dongknows.com/synology-diskstation-ds925-review/) · [iFeeltech — DS1525+ review](https://ifeeltech.com/blog/synology-ds1525-plus-review)

---

### 6 · Synology drive-compatibility policy

| Generation | Third-party HDDs | Detail |
|---|:--:|---|
| DS923+ (2022) | ✅ Unaffected | Pre-2025 models exempt |
| DS925+ / DS1525+ (2025) | ⚠️ **Needs DSM 7.3** | Launch policy blocked non-Synology drives at setup with no bypass; DSM 7.3 restored HDD and SATA SSD support |
| M.2 NVMe, all 2025 models | ❌ Still restricted | Reversal does **not** cover M.2 pools |

Moving to a DS1525+ means confirming **DSM 7.3 or later** before buying the 12 TB WD/Seagate drives. Planning an NVMe cache? Budget Synology-branded M.2 regardless of model.

> 📎 [Tom's Hardware — Synology restores third-party drive support in DSM 7.3](https://www.tomshardware.com/pc-components/nas/synology-walks-back-controversial-compatibility-policy-for-2025-nas-units-third-party-hdd-and-ssd-support-returns-with-diskstation-manager-7-3-update)

---

## ✅ Resolved — no change needed

### CPU timing — clear to buy now

The original checklist carried an open question about waiting for a platform refresh. **Resolved favourably:**

- Zen 6 desktop (**"Olympic Ridge"**) is reported for **2027**, not 2026. AMD's published 2026 Zen 6 roadmap covers **EPYC server** parts, not Ryzen desktop.
- **AM5 socket support extends through 2029**, with Zen 6 — and reportedly Zen 7 — staying on the socket. AM6 is not expected until 2030.

There is no near-term refresh to wait for, and the X870E board bought today should accept a Zen 6 drop-in later. **The 9950X + X870E platform is a safe purchase.**

> 📎 [VideoCardz — Zen 6 desktop set for 2027](https://videocardz.com/newz/amd-zen-6-desktop-ryzen-olympic-ridge-reportedly-set-to-launch-in-2027) · [TweakTown — AM5 through 2029](https://www.tweaktown.com/news/111864/amds-am5-socket-support-for-ryzen-cpus-will-continue-through-2029-zen-6-and-zen-7/index.html)

### PSU — 1,200 W kept, reasoning made explicit

NVIDIA's reference recommendation for the RTX 5080 is **850 W**; the build specifies **1,200 W**, ≈40% above. **Retained** — the documented RTX 5090 upgrade path needs it (575 W TGP), and buying now avoids replacing the PSU later.

The reasoning should be stated plainly though: **the 1,200 W is bought for the future GPU, not the current one.** If the 5090 path is abandoned, an 850–1,000 W VERTEX is the correct part.

---

## ⚖️ Unresolved — the GPU question

**Dissent recorded; the original decision stands.**

The RTX 5080 and the RTX 5060 Ti 16 GB have the **identical VRAM ceiling**. The 5080 buys clock speed and memory bandwidth — not capacity. The documented GPU workload (embeddings, OCR, Whisper, "moderate local inference") is not bandwidth-bound, so ≈Rp 16–19 juta of the difference buys no change in what will actually run.

Only the RTX 5090's 32 GB changes *which models fit*.

| | A · Cloud-primary ⭐ | B · As specified | C · Local-primary |
|---|---|---|---|
| GPU | RTX 5060 Ti 16 GB | RTX 5080 16 GB | RTX 5090 32 GB |
| Cost | Rp 8–11 juta | Rp 24–30 juta | Rp 46–65 juta |
| VRAM | 16 GB | 16 GB | **32 GB** |
| Complete environment | **Rp 114–195 juta** | Rp 130–215 juta | Rp 157–248 juta |

**The decision record selects Build B deliberately, and the specification documents it throughout.** The measured upgrade triggers are the right mechanism for revisiting this — not a re-argument now.

---

## 📋 Everything kept unchanged

The operational half of the original document survives intact and forms the backbone of the revision:

**Platform** — Ryzen 9 9950X · ASUS ProArt X870E-CREATOR WIFI · Samsung 990 PRO 2 TB + 4 TB · Seasonic VERTEX GX-1200 · Fractal Meshify 2 XL · 5 × Noctua NF-A14x25 G2 · APC Smart-UPS SMT2200IC · 4 × 12 TB CMR · 2 × 20 TB offline rotation · Windows 11 Pro + WSL2 Ubuntu 24.04

**Operations** — 24-hour service profile · BIOS and Windows/WSL reliability rules · thermal targets · dust control · daily/weekly/monthly/quarterly backup policy · data classification · UPS shutdown sequence · compatibility checklist · 10-step burn-in and acceptance criteria · maintenance and replacement schedule · upgrade triggers

These sections were the strongest part of the source document. They are reproduced without modification.

---

<div align="center">

### Summary

**4 components changed** · **2 new risks found** · **1 question resolved** · **1 dissent recorded**
**≈Rp 10–12 juta removed with no capability loss**

*Full specification: [`ai-workstation-build-spec.md`](./ai-workstation-build-spec.md)*

</div>
