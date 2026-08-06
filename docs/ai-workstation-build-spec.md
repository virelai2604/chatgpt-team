<div align="center">

# 🖥️ OpenClaw 24-Hour BIFL Workstation

### Every part, and the reason for it

**Prepared** 2026-08-06 · **Region** Indonesia (Jakarta) · **Envelope** Rp 130–215 juta

</div>

---

**Purpose** — Always-available OpenClaw / Gunawan AgentOS dispatcher, WSL2 automation, RAG and indexing, cloud-model escalation, scheduled local AI jobs, and durable business-data retention.

**How to read this** — every component gets the part number, the specification, and **the reason it was chosen over the alternatives**. Where the original decision record chose differently, the disagreement is stated with its evidence so you can overrule it. Nothing is asserted without a reason you can check.

| Mark | Meaning |
|:--:|---|
| ✅ | Verified against manufacturer or major-retailer source |
| ⚠️ | Unverified — confirm before purchase |
| 🔧 | Changed from the original decision record, with reasoning |
| 🚨 | Purchase-blocking warning |

---

## Contents

**[⚖️ The one decision to make first](#️-the-one-decision-to-make-first)** · **[1 Compute](#1-compute)** · **[2 Memory](#2-memory)** · **[3 Graphics](#3-graphics)** · **[4 Storage](#4-storage)** · **[5 Power & Cooling](#5-power--cooling)** · **[6 Backup & Network](#6-backup--network)** · **[7 Software](#7-software)** · **[8 Running It 24 Hours](#8-running-it-24-hours)** · **[9 Buying It](#9-buying-it)** · **[10 Budget](#10-budget)** · **[11 What Changed](#11-what-changed-from-the-original)**

---

## ⚖️ The one decision to make first

Everything else in this document is settled. This is not.

| | **A · Cloud-primary** ⭐ | **B · As specified** | **C · Local-primary** |
|---|---|---|---|
| Heavy reasoning runs on | Cloud APIs | Cloud APIs | This machine |
| GPU | RTX 5060 Ti 16 GB | RTX 5080 16 GB | RTX 5090 32 GB |
| GPU cost | Rp 8–11 juta | Rp 24–30 juta | Rp 46–65 juta |
| **VRAM ceiling** | **16 GB** | **16 GB** | **32 GB** |
| Memory | 96 GB @ 6000 | 96 GB @ 6000 | 128 GB @ 5600 |
| PSU | 850–1000 W | 1200 W | 1200 W |
| **Complete environment** | **Rp 114–195 juta** | **Rp 130–215 juta** | **Rp 157–248 juta** |

### Why this is the only real decision

Builds A and B have the **identical VRAM ceiling**. The RTX 5080 buys clock speed and memory bandwidth — not capacity. The documented GPU workload is embeddings, OCR acceleration, Whisper transcription and *"moderate local inference,"* none of which is bandwidth-bound. So roughly **Rp 16–19 juta** of the difference between A and B buys no change in which models will actually run.

Build C is the only option that changes *which models fit*. 32 GB is the difference between running a 27–32B model at usable quantization and not running it.

**The RTX 5080 sits between two coherent positions** — too expensive to be a support card, too small to be the main event.

> **⭐ Recommendation: A**, on the grounds that the project's documented gaps (persistent memory, marketplace APIs, revenue automation) are software, not hardware. If local inference is genuinely the point rather than the fallback, go straight to **C** — B is not a step toward it.
>
> **The decision record selects B.** This document specifies B throughout. Swap the GPU and PSU rows for A or C.

---

## 1. Compute

### CPU — AMD Ryzen 9 9950X

**Part** `100-100001277WOF` ✅ *(boxed, without cooler)*
**Spec** 16C/32T · 4.3 GHz base, 5.7 GHz boost · 170 W TDP (≈230 W PPT) · 80 MB cache · AM5 · Zen 5
**Cost** Rp 10.5–12.5 juta

**Why this part.** The workload is overwhelmingly parallel and CPU-bound: WSL2, file indexing, OCR, database work, containers, browser automation, concurrent agents. Those scale with core count. 16 cores is the most AM5 offers.

**Why not the 9950X3D.** The 3D V-Cache variant costs more and helps games, which benefit from a large L3 on a single CCD. Nothing in this workload is L3-latency-sensitive. Choose the X3D only if gaming is a major secondary use.

**Why boxed, not tray.** Tray CPUs sold to individuals in Indonesia frequently carry no warranty. The ≈Rp 500k premium buys a serial-verifiable warranty on the single most expensive non-GPU part.

> ### ✅ Timing is clear — buy now
> Zen 6 desktop (**"Olympic Ridge"**) is reported for **2027**, not 2026 — AMD's published 2026 Zen 6 roadmap covers **EPYC server** parts, not Ryzen desktop. **AM5 is supported through 2029**, with Zen 6 and reportedly Zen 7 staying on the socket; AM6 is not expected until 2030.
>
> There is no near-term refresh to wait for, and this board should accept a Zen 6 drop-in later.

### Motherboard — ASUS ProArt X870E-CREATOR WIFI ✅

**Spec** AM5 · X870E · ATX · 16+2+2 power stages · **4 × M.2** (M.2_1 & M.2_2 PCIe 5.0 ×4 up to 128 Gbps; M.2_3 & M.2_4 PCIe 4.0) · **10 GbE + 2.5 GbE** · Wi-Fi 7 · **2 × USB4 40 Gbps** · up to 256 GB DDR5 · BIOS FlashBack
**Cost** Rp 8.5–11.0 juta

**Why this board over cheaper X870E.** Three things earn the premium, and none is branding:

1. **Four M.2 slots.** This is what makes the storage tiering possible without add-in cards. A two-slot board forces the archive tier onto SATA or PCIe adapters.
2. **10 GbE onboard.** The NAS architecture depends on it. Adding a 10 GbE card later costs money *and* a PCIe slot.
3. **BIOS FlashBack.** Lets you update the BIOS with no CPU installed — the insurance policy against a board shipping with firmware older than your CPU stepping. On a build this expensive, that alone justifies the choice.

> **⚠️ Lane sharing.** M.2_2 shares bandwidth with the second PCIe 5.0 ×16 slot. Harmless with one GPU, blocking if you add a second accelerator later. **Populate M.2_3 before M.2_2** so that option stays open without re-seating drives.

---

## 2. Memory

### 🔧 96 GB — G.Skill Flare X5 `F5-6000J3036F48GX2-FX5` ✅

**Spec** 2 × 48 GB · DDR5-6000 · **CL30-36-36-96** · **1.35 V** · AMD EXPO · U-DIMM, non-ECC
**Cost** Rp 4–6 juta

**Why 48 GB modules instead of the specified 64 GB.**

| | Specified 2 × 64 GB | **This 2 × 48 GB** |
|---|---|---|
| Part | `F5-6000J3244G64GX2-FX5` ✅ | **`F5-6000J3036F48GX2-FX5`** ✅ |
| Capacity | 128 GB | 96 GB |
| Rated timings | CL32-44-44-96 | **CL30-36-36-96** |
| Voltage | 1.40 V | **1.35 V** |
| Realistic stable speed | ≈DDR5-5600 | **DDR5-6000** |
| Cost | Rp 7.5–11 juta | **Rp 4–6 juta** |

64 GB DDR5 UDIMMs are dual-rank and high-density — they load the AM5 memory controller hard and rarely run stable at their rated speed. 48 GB modules are a well-trodden AM5 configuration that genuinely holds DDR5-6000. The result is tighter timings, lower voltage, less heat, better odds of booting at the advertised profile, and **≈Rp 3–5 juta cheaper**.

**When to keep 128 GB instead.** Only if the workload genuinely commits more than ~96 GB. The original document's own upgrade trigger sets that bar at *"sustained committed memory exceeds approximately 100–110 GB"* — which the documented workload does not reach. Two DIMM slots stay free either way, so 192 GB remains available later.

**Why two DIMMs, never four.** Four dual-rank DDR5 modules on AM5 force the memory controller down to markedly lower speeds and introduce stability problems that are miserable to diagnose on an always-on machine. Two sticks also preserve the upgrade path.

**Why not ECC.** The original preferred *"Kingston FURY Renegade Pro ECC UDIMM if present on ASUS QVL."* Treat as unlikely to be actionable — ECC UDIMM validation on AM5 consumer boards is inconsistent even where the CPU supports it, and 2 × 64 GB ECC kits are rare. Check the QVL; if nothing qualifies, proceed with non-ECC without treating it as a compromise. **The backup discipline in [§8](#8-running-it-24-hours) is the real integrity control here.** If ECC is a hard requirement, that is a Threadripper/W790 platform decision, not a DIMM substitution.

> ### 📋 RAM purchasing rule
> 1. Open the ASUS ProArt X870E-CREATOR WIFI memory QVL
> 2. Filter: Ryzen 9000 · your module capacity · **two-DIMM** configuration
> 3. Buy a **single matched kit** — never two kits of two
> 4. Prefer **stability at 5600** over an unverified 6000
> 5. Boot at JEDEC defaults; enable EXPO only after extended testing passes

---

## 3. Graphics

### RTX 5080 16 GB *(Build B, as decided)*

**Part** ASUS TUF Gaming `TUF-RTX5080-O16G-GAMING` ✅ or MSI RTX 5080 16G SUPRIM SOC
**Spec** 16 GB GDDR7 · 10,752 CUDA cores · 960 GB/s · 5th-gen Tensor cores · **360 W TGP** ✅
**Cost** Rp 24–30 juta

**Why a premium three-fan model** rather than the cheapest 5080: this machine runs 24 hours. Cooler and PCB quality determine fan noise, sustained clocks and service life far more than the ~5% clock difference between AIB models. Buy the cooler, not the bin.

**Why 16 GB is the constraint.** It runs embeddings, OCR acceleration, Whisper, image generation and quantized models up to roughly 14B comfortably. A 27–32B model at usable quantization does not fit.

**The disagreement, stated once.** ⬆️ See [the build decision](#️-the-one-decision-to-make-first). The RTX 5060 Ti 16 GB has the same VRAM ceiling for ≈Rp 16–19 juta less; the RTX 5090's 32 GB is the only thing that changes which models fit. The decision record chose the 5080 deliberately and that stands — the measured upgrade triggers below are the right mechanism for revisiting it, not a re-argument now.

### 📈 When the RTX 5090 becomes justified

Upgrade when one or more of these is **measured**, not anticipated:

- Repeated CUDA out-of-memory failures at 16 GB
- The required model won't run acceptably at the chosen quantization
- Daily local inference runs for many hours
- Cloud API cost exceeds the amortized GPU cost
- Privacy rules prevent cloud escalation
- Image/video generation becomes revenue work
- Multiple users need concurrent local inference

> **📉 Pricing note.** Indonesian GPU prices moved **upward** through 2026. RTX 5080 launched at Rp 20.3 juta SRP and now sits near Rp 24 juta; RTX 5090 launched at Rp 40.8 juta and now runs Rp 46–65 juta. If the 5090 path is genuinely likely, **waiting is more likely to cost than save**.

---

## 4. Storage

### Why this tiering exists

Three distinct jobs with different requirements, deliberately not mixed:

| Job | Needs | Lives on |
|---|---|---|
| Boot, execute, compile | Low latency, moderate capacity | NVMe 1 |
| Active AI read/write | High endurance, high capacity | NVMe 2 |
| Archive, evidence, backup | Capacity, parity, snapshots | **NAS** |

### NVMe 1 — Samsung 990 PRO 2 TB `MZ-V9P2T0BW` ✅

**Spec** PCIe 4.0 ×4 · NVMe 2.0 · M.2 2280 · 7,450/6,900 MB/s · **1,200 TBW** · TLC V-NAND · AES-256 · TCG Opal 2.0
**Slot** M.2_1 · **Cost** Rp 2.6–3.5 juta

**Contents** — Windows · Program Files · WSL2 Ubuntu VHDX (`/home/user`) · active Git repos · Python `.venv` · Node and Codex runtime

**Why 2 TB and not 1 TB.** The WSL VHDX grows without bound, Docker metadata accumulates, and package caches are relentless. **Keep 400–500 GB free** — NVMe write performance and endurance both degrade as drives fill.

**Why the WSL VHDX must live here.** It is a heavily random-write workload. On a USB drive or network share it is slow and, more importantly, prone to corruption on disconnect.

### NVMe 2 — Samsung 990 PRO 4 TB `MZ-V9P4T0BW` ✅

**Spec** as above, plus 4 GB DRAM · **2,400 TBW**
**Slot** M.2_3 *(not M.2_2 — see the lane-sharing warning)* · **Cost** Rp 5.5–7.5 juta

**Contents**
```text
AI-Core/
├── models/            ├── databases/          ├── indexes/
├── datasets/          │   ├── sqlite/         │   └── chroma/
├── normalized/        │   └── duckdb/         ├── outputs/current/
├── transcripts/       ├── logs/               └── cache/
└── chunks/
```

**Why 2,400 TBW matters here.** This is the write-heavy tier — indexing, OCR output, transcripts, database writes, model downloads. Endurance is the spec that determines whether the drive survives the machine's intended life. **Keep 800 GB free.**

### 🔧 NVMe 3 — deferred, not deleted

**Original** a third 4 TB 990 PRO for archive and staging, Rp 5.5–7.5 juta
**Revised** buy it on trigger; the NAS covers the role at build time

**Why deferred.** The original buys this drive **and** a 24 TB dual-parity NAS **and** 40 TB of rotating offline capacity. Its defined contents — completed outputs, exports, snapshots, old models, rebuildable indexes, temporary ingestion — are archive-class data the NAS already holds, at 6× the capacity, with parity and snapshots an internal drive structurally cannot provide.

The original says so itself: *"The third NVMe is not a backup. It is still inside the same computer."* And it already applies this exact reasoning to the **fourth** M.2 slot — *"avoid buying unused flash too early."* With a NAS in the build, that logic reaches the third slot too.

**Buy it when** the active 4 TB exceeds 75–80% after NAS offload · ingestion staging over 10 GbE is a *measured* bottleneck · write separation shows measurable benefit. A mid-tier Gen4 NVMe suffices then — **archive workloads do not need 2,400 TBW.**

---

## 5. Power & Cooling

### CPU cooler — 🔧 Noctua NH-D15 G2 **LBC** ✅

**Spec** 168 mm tall · 8 heatpipes · 2 × 140 mm fans · **Low Base Convexity** · 6-year warranty
**Cost** Rp 2.3–3.0 juta

**🚨 Order the LBC variant specifically.** Noctua ships **three** base-convexity versions and the plain part number gets you the wrong one:

| Variant | Designed for |
|---|---|
| **LBC** *(Low)* | **Flat IHS — AM5, AM4, LGA2066, direct-die, lapped CPUs** |
| Standard *(Medium)* | All-round compromise |
| HBC *(High)* | De-shaped Intel 12th–14th gen under high ILM pressure |

Noctua documents LBC as **ideal for AM5**, specifically for combining the lowest possible CCD temperatures with the lowest possible IOD temperatures. Standard *works*; LBC is the manufacturer's stated optimum **at identical price**. The variant is engraved on the base — verify on receipt.

**Why air, not liquid.** AMD recommends liquid cooling for optimum 9950X performance, and for a machine running 24 hours that recommendation is the wrong trade. An AIO pump is a wear item with a finite life and a failure mode that kills the CPU; a fan failure is audible, gradual and a Rp 400k fix. Run a modest PPT limit or Eco Mode and the thermal difference is small — smaller than the reduction in noise and sustained electrical stress.

### PSU — Seasonic VERTEX GX-1200 ATX 3.1 ✅

**Spec** 1,200 W · 80 PLUS Gold · ATX 3.1 / PCIe 5.1 · **native 12V-2×6** · 135 mm fluid-dynamic-bearing fan · OPP/OVP/UVP/SCP/OCP/OTP · **12-year warranty**
**Cost** Rp 4.2–5.5 juta

**Why 1,200 W when the system draws ~600 W.** NVIDIA's reference recommendation for the RTX 5080 is **850 W** — this is ≈40% above it. The justification is explicit: **the 1,200 W is bought for the RTX 5090 upgrade path, not the current card.** The 5090's 575 W TGP genuinely needs this class of unit, and buying now avoids a second PSU purchase.

**If the 5090 path is abandoned, an 850–1,000 W VERTEX is the correct part** and saves roughly Rp 1.5 juta.

**Why ATX 3.1 and native 12V-2×6.** The 12VHPWR connector's melting failures were overwhelmingly associated with adapter daisy-chains and incomplete seating. A native cable from an ATX 3.1 supply removes the adapter entirely. The 12-year warranty is the other half — a PSU failure can take other components with it.

> **⚠️** Early VERTEX units shipped with 12VHPWR cables before the ATX update. **Confirm which cable is in the box.**

### Case — Fractal Design Meshify 2 XL

**Cost** Rp 3.0–5.0 juta

**Why a full tower.** Not for the aesthetics — for airflow volume and service access. A machine that runs continuously in Jakarta's climate needs unrestricted intake and room to work when replacing fans or drives. The mesh front is the functional part; the size is what keeps GPU clearance and cable bend radius from becoming problems.

### Fans — 5 × Noctua NF-A14x25 G2 PWM

**Layout** 3 front intake · 1 rear exhaust · 1–2 top exhaust · **Cost** Rp 1.5–2.8 juta

**Why positive pressure.** More intake than exhaust means air enters through **filtered** front intakes rather than being drawn through every unfiltered gap in the chassis. In a dusty environment this is the difference between cleaning filters and disassembling heatsinks.

**Why one fan family.** Consistent PWM curves and acoustic signature. Mixed fans produce beat frequencies that are far more irritating than either fan alone at the same dB.

### UPS — APC Smart-UPS SMT2200IC ⚠️

**Spec** 2,200 VA ≈ **1,980 W** · pure sine wave · replaceable battery
**Optional** APC Network Management Card 3 `AP9640` — SNMP alerting and remote graceful shutdown
**Cost** Rp 12–25 juta

**Why pure sine wave, not simulated.** Active PFC power supplies — which every unit in this class is — can behave unpredictably on the stepped approximation cheaper UPSs produce, sometimes refusing to transfer to battery at all. The whole point is graceful shutdown; a UPS that fails to transfer is worse than none.

**Why size on watts, not VA.** A 2,200 VA unit delivers ≈1,980 W. VA is the headline number; watts is the one that determines whether your tower plus networking actually stays up long enough to checkpoint databases and stop cleanly.

| ✅ Connect | ❌ Do not connect |
|---|---|
| PC tower · primary monitor **only** · router · switch · NAS | Laser printer · space heater · high-power speakers · secondary monitors |

**Shutdown sequence**
```
1. Alert immediately on utility failure
2. Stop new heavy jobs
3. Checkpoint databases and active work
4. Shut down local models
5. Gracefully stop WSL, then Windows — before battery exhaustion
6. Shut down NAS once workstation data is safe
```

---

## 6. Backup & Network

### 🚨 NAS — read this before ordering

**Specified** Synology DS923+ ⚠️ · 4-bay · ECC memory · 10 GbE **via PCIe** `E10G22-T1-Mini`

**The trap.** The DS923+ dates to 2022. Its successor, the **DS925+** (April 2025), **removed the PCIe expansion slot** — and that slot is the only path to 10 GbE. The DS925+ tops out at dual 2.5 GbE, ≈5 Gbps aggregated and only for multi-stream traffic.

This build specifies a 10 GbE workstation↔NAS link, and because the archive NVMe is deferred, **staging traffic now runs over that link**. The network speed is load-bearing. A retailer offering "the current model" would hand you exactly the unit that silently breaks the storage design.

| Option | 10 GbE | Bays | Verdict |
|---|:--:|:--:|---|
| **Synology DS923+** *(specified)* | ✅ via PCIe | 4 | Verify availability first |
| Synology DS925+ | ❌ **impossible** | 4 | **Do not substitute** |
| **Synology DS1525+** | ✅ upgrade slot | 5 | ≈+$160, extra bay — **the real successor** |
| **UGREEN DXP4800 Plus** | ✅ **built-in** | 4 | Faster hardware, non-Synology software |

**Also — drive compatibility.** Synology's 2025 Plus models launched blocking non-Synology drives at setup with no bypass; **DSM 7.3 reversed it** for 3.5″ HDDs and 2.5″ SATA SSDs. The reversal does **not** cover M.2 — NVMe pools still require Synology-branded drives on those models. The DS923+ is exempt entirely. Moving to a DS1525+ means confirming **DSM 7.3 or later** before buying third-party drives.

### NAS drives — 4 × 12 TB CMR ⚠️

**Parts** WD Red Pro `WD121KFGX` or Seagate IronWolf Pro `ST12000NT001`
**Array** SHR-2 or RAID 6 → **≈24 TB usable** · **Cost** Rp 35–58 juta with the NAS

**Why CMR, never SMR.** Shingled drives rewrite overlapping tracks on write, which collapses performance during RAID rebuilds — exactly when you need the array to survive. Some SMR drives have failed rebuilds outright. This is the single most important spec on the line item.

**Why dual parity (SHR-2/RAID 6).** With 12 TB drives, a rebuild takes many hours under full load — the precise conditions under which a second drive is most likely to fail. Single parity means that second failure loses the array. Dual parity costs one drive of capacity and buys the ability to survive it.

**Contents**
```text
NAS/
├── raw-source-of-truth/     ├── configurations/
├── manifests-sha256/        ├── workstation-images/
├── sqlite-backups/          ├── project-archives/
├── business-outputs/        ├── immutable-snapshots/
└── staging/                 ← absorbs the deferred NVMe 3 role
```

### Offline backup — 2 × 20 TB, rotated ⚠️

**Parts** WD Elements Desktop or Seagate Expansion Desktop · **Cost** Rp 15–25 juta

**Why two, rotated, and physically disconnected.** A NAS is not a backup — it is online storage. Ransomware encrypts everything it can reach, including mounted network shares. Theft and fire take the NAS and the workstation together. **The only defence is a copy that is physically disconnected and stored elsewhere.** Rotating two drives means one is always offline, and you never have a window with zero valid backups.

### Network — TP-Link Omada TL-SX1008 ⚠️ · Cat6A

**Cost** Rp 7–15 juta · optional

**Why 10 GbE is not a luxury here.** At 1 GbE a full restore of 24 TB takes days. At 10 GbE, staging and restore become operations you'll actually perform rather than avoid — which is what determines whether the backup discipline survives contact with reality.

---

## 7. Software

| Layer | Selection | Why |
|---|---|---|
| Host OS | **Windows 11 Pro** | BitLocker, Hyper-V/WSL2, policy controls. Pro, not Home — Home lacks BitLocker and group policy |
| Linux | **Ubuntu 24.04 LTS under WSL2** | LTS for a five-year support horizon on a machine meant to last |
| Runtimes | Node.js · Python via `uv` + per-project `.venv` · Git · Docker where useful | One venv per project prevents the dependency collisions that break unattended jobs |
| Agent stack | OpenClaw · Codex CLI · Ollama · cloud API path | — |
| Data | Raw files + SHA-256 manifests · SQLite/FTS5 · CSV/JSONL · Chroma · DuckDB + Parquet | Manifests make the raw archive verifiable, not merely present |

---

## 8. Running It 24 Hours

### Service profile — OpenClaw stays up, the GPU does not

| Service | Status | GPU | Rule |
|---|:--:|:--:|---|
| OpenClaw gateway / router | 🟢 Always | — | Supervised service |
| Scheduler / task queue | 🟢 Always | — | Trigger jobs at controlled times |
| SQLite / Chroma memory | 🟢 Always | — | Clean shutdown · frequent backups |
| Cloud AI escalation | 🔵 On demand | — | **Default** for hard reasoning and final review |
| Ollama / Qwen fallback | 🔵 On demand | ◐ | Load only the required model |
| OCR / transcription | 🟡 Scheduled | ◐ | Batch during low-use periods |
| Heavy local LLM | 🔴 Justified only | ● | Never keep a large model resident without work |
| Browser / marketplace | 🟡 Scheduled | — | **Human approval** for publishing, payments, deletion, credentials |

**Why the GPU idles.** Keeping a model resident burns power and heat around the clock for latency you rarely need. The gateway, scheduler and memory layer are what must be always-available; inference is bursty and can be loaded on demand.

### Configuration

<table>
<tr><th width="50%">BIOS</th><th width="50%">Windows & WSL</th></tr>
<tr valign="top"><td>

- Stable ASUS release, **never beta**
- Load optimized defaults after updating
- EXPO only after baseline testing
- Memory context restore only once stable
- **Do not overclock**
- Eco Mode / PPT limit for noise and heat
- PCIe link settings on Auto
- Restore on AC Power Loss **only** with UPS + service recovery configured

</td><td>

- BitLocker on · recovery keys stored **offline**
- WSL VHDX stays on the internal OS NVMe
- **Never** put live SQLite or Chroma on USB or network shares
- Controlled Windows Update restart windows
- Maintenance reboot weekly or monthly
- Services under systemd or a watchdog
- Separate Windows and WSL Python environments
- `uv` with one `.venv` per project

</td></tr>
</table>

**Why no overclocking, ever, on this machine.** An overclock that is 99.9% stable produces a silent data corruption roughly once a day on a machine doing continuous database writes. The performance gain is single-digit percent; the failure mode is undetectable corruption in your evidence layer.

### Thermal targets

*Operational targets, not manufacturer limits — the point is longevity, not survival.*

| Component | Preferred sustained |
|---|---:|
| CPU — normal agent work | **< 75 °C** |
| CPU — long all-core work | < 85 °C |
| GPU core — sustained compute | < 75 °C |
| GPU memory / hotspot | Monitor vendor sensors; avoid limits |
| NVMe | **< 65 °C** |

### Dust control

Positive pressure · clean filters **every 1–2 months** in a dusty environment · inspect heatsinks and fan bearings **every 6 months** · never place the tower on the floor · keep **15–20 cm** clearance around intakes and exhausts

### Backup policy

<table>
<tr><th>🔄 Daily</th><th>📅 Weekly</th></tr>
<tr valign="top"><td>

- SQLite online backup or safe snapshot
- Incremental to NAS — Markdown, JSON, CSV, manifests, configs, business outputs
- Chroma backup after ingestion completes

</td><td>

- NAS snapshot
- Verify backup job logs
- Export critical tables to CSV/JSONL
- Copy configuration and recovery documents

</td></tr>
<tr><th>📦 Monthly</th><th>🔬 Quarterly</th></tr>
<tr valign="top"><td>

- Connect offline drive **A**, verified backup, disconnect
- Next month drive **B**
- Inactive drive stored in a **separate location**

</td><td>

- **Restore-test** a SQLite database
- **Restore-test** documents and one full project
- SMART review across all drives
- UPS self-diagnostics
- Confirm BitLocker + NAS recovery credentials accessible

</td></tr>
</table>

**Why quarterly restore tests are the load-bearing item.** An untested backup is a hypothesis. The failure mode people actually hit is not "no backup" — it is "backup exists, restore fails." Restore-testing is the only thing that converts the hypothesis into a fact.

| Class | Priority | | Class | Priority |
|---|:--:|---|---|:--:|
| Raw source files | 🔴 **Critical** | | Chroma indexes | 🟢 Rebuildable |
| SQLite manifests & ledgers | 🔴 **Critical** | | Ollama models | 🟢 Re-downloadable |
| Business / capstone outputs | 🔴 **Critical** | | OCR / temp cache | 🟢 Rebuildable |
| Configuration & scripts | 🔴 **Critical** | | | |

**Why classification matters.** Backing up everything equally means backing up 4 TB of re-downloadable model weights at the same priority as irreplaceable source evidence. Classify once and the backup window stops being a problem.

### Maintenance schedule

| Item | Interval | Service window |
|---|---|---|
| Dust filters | 1–2 months | Clean; replace only if damaged |
| Fans | 6 months | Replace on bearing noise, vibration, RPM instability |
| Thermal paste | 3–5 years, or on temp change | Replace only when needed |
| SSD health | Monthly SMART | 4–8 years depending on writes |
| HDD health | Monthly SMART + scrub | Replace proactively on errors or warranty horizon |
| UPS self-test | Monthly | **Battery 3–5 years — this is a consumable** |
| NAS scrub | Monthly–quarterly | Replace failing disks immediately |
| BIOS | Quarterly review | Update only for security, stability, compatibility |
| GPU | Continuous | First major upgrade likely 4–7 years |
| Case / cooler / PSU | Annual inspection | Outlasts multiple CPU/GPU cycles |

---

## 9. Buying It

### Pre-purchase checklist

**Components**
- [ ] CPU is **boxed** `100-100001277WOF`, not tray
- [ ] 🚨 Cooler is the **LBC** variant — check the engraving on the base
- [ ] RAM part number is on the **current** ASUS QVL
- [ ] PSU is **ATX 3.1** with a **native 12V-2×6** cable
- [ ] NAS disks are **CMR, not SMR**
- [ ] 🚨 NAS model can actually reach 10 GbE — **not a DS925+**
- [ ] If a 2025-gen NAS: **DSM 7.3 or later** before buying third-party drives

**Physical fit**
- [ ] Case supports 168 mm cooler height
- [ ] Cooler clears RAM height and the side panel
- [ ] GPU length, thickness and cable bend radius fit
- [ ] Both NVMe drives get motherboard heatsinks
- [ ] No GPU adapter daisy-chain

**System**
- [ ] M.2_3 populated before M.2_2 — preserves the second PCIe 5.0 slot
- [ ] UPS **wattage**, not VA, is adequate
- [ ] GPU, board, SSDs and UPS carry **official Indonesian warranty**
- [ ] Builder performs extended memory, CPU, GPU, SSD and power testing
- [x] ~~Wait for a platform refresh~~ — ✅ **resolved: Zen 6 is 2027, AM5 runs to 2029**

### Burn-in & acceptance

| # | Test | Duration |
|--:|---|---|
| 1 | MemTest86 | ≥ 4 complete passes |
| 2 | OCCT memory + CPU | 2–4 hours |
| 3 | Prime95 blend or y-cruncher | 1–2 hours, watching temps |
| 4 | GPU compute / stress | 1–2 hours |
| 5 | **Combined CPU + GPU** | 30–60 min — tests PSU and airflow |
| 6 | NVMe extended | SMART + large sequential write/read |
| 7 | Network | Sustained 10 GbE transfer to NAS |
| 8 | UPS | Simulated utility failure → graceful shutdown |
| 9 | WSL | Restart, mount, Docker/Ollama/OpenClaw recovery |
| 10 | Backup restore | One project + one SQLite database |

> ### ✅ Accept only if
> Zero memory errors · zero WHEA hardware errors · no unexplained reboot · no thermal throttling within configured limits · no GPU power-connector warning · no NVMe SMART warning · successful UPS-triggered graceful shutdown · **successful backup restoration**

**Why test 5 is the one people skip and shouldn't.** CPU and GPU stress tests run separately both pass on an underspecified PSU or a poorly-ventilated case. Simultaneous load is the condition that actually occurs during real work, and the one that exposes transient power delivery and airflow failures.

---

## 10. Budget

*Planning ranges, **not** quotations. Re-check at purchase — Indonesian GPU pricing moves weekly.*

| Area | Original | **This revision** |
|---|---:|---:|
| Core tower | Rp 80–105 juta | **Rp 68–92 juta** |
| APC Smart-UPS 2200 VA | Rp 12–25 juta | Rp 12–25 juta |
| NAS · 4 × 12 TB | Rp 35–55 juta | Rp 35–58 juta |
| Two 20 TB offline drives | Rp 15–25 juta | Rp 15–25 juta |
| 10 GbE switch / cabling *(optional)* | Rp 7–15 juta | Rp 7–15 juta |
| **Complete environment** | Rp 142–225 juta | **Rp 130–215 juta** |

**Staged purchase order**, if buying over time: tower → **UPS** → NAS → offline rotation → 10 GbE switch.

> **⚠️ Do not remove the UPS or backup layer to afford a higher GPU.** The GPU determines how fast the machine works; those two determine whether the work survives.

---

## 11. What Changed From the Original

**4 components changed · 2 risks found · 1 question resolved · 1 dissent recorded · ≈Rp 10–12 juta removed with no capability loss**

| # | Change | Why | Δ Cost |
|--:|---|---|---:|
| 1 | Cooler → **LBC** variant | Noctua's stated optimum for AM5's flat IHS; original ruled out HBC but settled on standard | None |
| 2 | Memory → **96 GB @ 6000 CL30** | 64 GB modules rarely hold rated speed on AM5; 48 GB do. Faster, cooler, cheaper | −Rp 3–5 juta |
| 3 | Archive NVMe → **deferred** | Role duplicated by the 24 TB NAS already in the build | −Rp 5.5–7.5 juta |
| 4 | RTX 5080 budget → **Rp 24–30 juta** | Verified street pricing; original over-provisioned | −Rp 3 juta |
| 5 | 🚨 **DS925+ warning** added | Successor NAS removed the PCIe slot — cannot reach 10 GbE at all | — |
| 6 | ⚠️ Synology drive policy added | 2025 models restricted third-party drives; DSM 7.3 reversed for HDD/SATA, not M.2 | — |
| 7 | ✅ CPU timing resolved | Zen 6 desktop is 2027; AM5 supported to 2029 — no reason to wait | — |
| 8 | PSU 1,200 W **kept** | Justified as RTX 5090 headroom, not 5080 sizing — reasoning now explicit | — |

**Kept entirely unchanged** — the operational half of the original document, which was its strongest part: 24-hour service profile · BIOS and WSL reliability rules · thermal targets · dust control · backup cadence and classification · UPS shutdown sequence · burn-in and acceptance criteria · maintenance schedule · upgrade triggers.

---

## Verification Status

**✅ Verified** — Ryzen 9 9950X MPN and specs · ProArt X870E-Creator feature set and M.2 topology · both G.Skill kit MPNs · Noctua variant guidance · Samsung 990 PRO MPNs, performance, TBW · Seasonic VERTEX GX-1200 specs · RTX 5080 specs and AIB models · Synology 2025 drive policy and DSM 7.3 reversal · DS925+ loss of PCIe/10 GbE and DS1525+/UGREEN alternatives · Zen 6 timing and AM5 support horizon · Indonesian RTX 5080/5090 street pricing

**⚠️ Not verified** — exact current IDR quotations · APC, Synology, WD/Seagate, Fractal, TP-Link stock and warranty terms in Indonesia · current DS923+ availability · DS1525+ Indonesian pricing · UPS availability at 230 V

## Sources

[AMD Ryzen 9 9950X](https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-9-9950x.html) ·
[ASUS ProArt X870E-CREATOR WIFI](https://www.asus.com/id/motherboards-components/motherboards/proart/proart-x870e-creator-wifi/techspec/) ·
[NVIDIA RTX 5080](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/) ·
[Noctua — NH-D15 G2 versions explained](https://noctua.at/en/nh-d15-g2-versions-explained) ·
[Noctua NH-D15 G2 LBC](https://www.noctua.at/en/products/nh-d15-g2-lbc/features) ·
[G.Skill Flare X5 DDR5 EXPO](https://www.gskill.com/products/1/165/396/Flare-X5-DDR5-AMD-EXPO) ·
[Samsung 990 PRO datasheet](https://download.semiconductor.samsung.com/resources/data-sheet/samsung_nvme_ssd_990_pro_datasheet_rev.2.0.pdf) ·
[Seasonic VERTEX GX ATX 3.1](https://seasonic.com/vertex-gx/) ·
[Fractal Meshify 2 XL](https://support.fractal-design.com/support/solutions/articles/4000174747-meshify-2-xl) ·
[Tom's Hardware — Synology DSM 7.3 drive-support reversal](https://www.tomshardware.com/pc-components/nas/synology-walks-back-controversial-compatibility-policy-for-2025-nas-units-third-party-hdd-and-ssd-support-returns-with-diskstation-manager-7-3-update) ·
[Dong Knows Tech — DS925+ vs DS923+](https://dongknows.com/synology-diskstation-ds925-review/) ·
[iFeeltech — DS1525+ review](https://ifeeltech.com/blog/synology-ds1525-plus-review) ·
[VideoCardz — Zen 6 desktop set for 2027](https://videocardz.com/newz/amd-zen-6-desktop-ryzen-olympic-ridge-reportedly-set-to-launch-in-2027) ·
[TweakTown — AM5 through 2029](https://www.tweaktown.com/news/111864/amds-am5-socket-support-for-ryzen-cpus-will-continue-through-2029-zen-6-and-zen-7/index.html) ·
[Kompas Tekno — RTX 5080/5090 Indonesian pricing](https://tekno.kompas.com/read/2025/01/31/12060017/nvidia-mulai-jual-gpu-rtx-5080-dan-5090-di-indonesia-ini-harganya)

---

<div align="center">

## 🛒 Final Purchase Line

**AMD Ryzen 9 9950X** `100-100001277WOF` · **ASUS ProArt X870E-CREATOR WIFI**
**96 GB G.Skill Flare X5** `F5-6000J3036F48GX2-FX5` · **Premium RTX 5080 16 GB**
**Samsung 990 PRO 2 TB** `MZ-V9P2T0BW` **+ 4 TB** `MZ-V9P4T0BW`
**Seasonic VERTEX GX-1200** · **Noctua NH-D15 G2 LBC** · **Fractal Meshify 2 XL** · **5 × NF-A14x25 G2**
**APC Smart-UPS SMT2200IC** · **Synology DS923+ or DS1525+ · 4 × 12 TB CMR** · **2 × 20 TB offline**

*Third NVMe deferred · Cooler is **LBC** · NAS must reach **10 GbE***

</div>
