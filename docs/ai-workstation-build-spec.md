<div align="center">

# 🖥️ OpenClaw 24-Hour BIFL Workstation

### Tier 1 Compute · Tier 3 Storage, Backup & Data Discipline

**Prepared** 2026-08-06 · **Region** Indonesia (Jakarta) · **Budget** Rp 136–218 juta

</div>

---

> ### 📌 Decision of Record
>
> An **RTX 5080-based Tier 1 compute platform**, plus Tier 3 storage, backup, UPS, monitoring and data separation.
>
> Do **not** move to RTX 5090 unless measured local-AI workloads repeatedly exceed 16 GB VRAM, or local inference directly generates enough revenue to justify the additional capital, power and heat.

**Purpose** — Always-available OpenClaw / Gunawan AgentOS dispatcher, WSL2 automation, RAG and indexing, cloud-model escalation, scheduled local AI jobs, and durable business-data retention.

<table>
<tr><td>

**Legend**

| Mark | Meaning |
|:--:|---|
| ✅ | Part number verified against vendor or major-retailer source |
| ⚠️ | Unverified — confirm before purchase |
| 🔧 | Corrected from the original decision record — see [§10](#10-correction-register) |

</td></tr>
</table>

---

## Contents

| # | Section | # | Section |
|--:|---|--:|---|
| 1 | [Purchase Specification](#1-purchase-specification) | 6 | [Backup Policy](#6-backup-policy) |
| 2 | [Capacity & Drive Map](#2-capacity--drive-map) | 7 | [Power & Shutdown](#7-power--shutdown) |
| 3 | [24-Hour Operating Profile](#3-24-hour-operating-profile) | 8 | [Pre-Purchase Checklist](#8-pre-purchase-checklist) |
| 4 | [Reliability Configuration](#4-reliability-configuration) | 9 | [Burn-In & Acceptance](#9-burn-in--acceptance) |
| 5 | [NAS Compatibility Warning](#5-nas-compatibility-warning) | 10 | [Correction Register](#10-correction-register) |
| | | 11 | [Maintenance · Triggers · Budget](#11-maintenance-triggers--budget) |

---

## 1. Purchase Specification

### 1.1 Compute Core

| Component | Part | Key specification |
|---|---|---|
| **CPU** | AMD Ryzen 9 9950X · `100-100001277WOF` ✅ | 16C/32T · 4.3→5.7 GHz · 170 W · 80 MB cache · AM5 |
| **Cooler** 🔧 | **Noctua NH-D15 G2 LBC** ✅ | 168 mm · 8 heatpipes · 2×140 mm · *Low Base Convexity* |
| **Motherboard** | ASUS ProArt X870E-CREATOR WIFI ✅ | 4× M.2 (2× PCIe 5.0) · 10 GbE + 2.5 GbE · 2× USB4 · Wi-Fi 7 · 16+2+2 |
| **Memory** | 2 × 64 GB DDR5-5600 EXPO, QVL-approved<br>Candidate: G.Skill Flare X5 `F5-6000J3244G64GX2-FX5` ✅ | 128 GB total · run at 5600 · non-ECC |
| **GPU** | ASUS TUF RTX 5080 16 GB OC `TUF-RTX5080-O16G-GAMING` ✅<br>*or* MSI RTX 5080 16G SUPRIM SOC | 16 GB GDDR7 · 10,752 CUDA · 960 GB/s · 360 W TGP |

> **⚠️ Cooler variant matters.** Order `NH-D15 G2 **LBC**`, not the plain `NH-D15 G2`. Noctua documents LBC as the optimum for AM5's flat IHS. The variant is engraved on the base — verify on receipt. Same price. → [§10.1](#101-cooler-variant--standard-base--lbc)

### 1.2 Storage

| Slot | Part | Capacity | Endurance | Role |
|---|---|---:|---:|---|
| M.2_1 (Gen5) | Samsung 990 PRO `MZ-V9P2T0BW` ✅ | 2 TB | 1,200 TBW | OS · WSL VHDX · repos |
| M.2_3 (Gen4) | Samsung 990 PRO `MZ-V9P4T0BW` ✅ | 4 TB | 2,400 TBW | Active AI-Core |
| M.2_2, M.2_4 | *empty* | — | — | Reserved for expansion |

**Shared 990 PRO specs** ✅ — PCIe 4.0 ×4 · NVMe 2.0 · M.2 2280 · 7,450/6,900 MB/s · TLC V-NAND · AES-256 · TCG Opal 2.0 · 5-yr warranty

> **🔧 Third NVMe deferred.** The original specified a third 4 TB 990 PRO for archive and staging. With a 24 TB dual-parity NAS in the build, that role is already covered — at 6× the capacity, with snapshots the internal drive cannot provide. Deferred behind a measured trigger, **saving ≈Rp 5.5–7.5 juta**. → [§10.2](#102-archivestaging-nvme--deferred-not-deleted)
>
> M.2_3 is used before M.2_2 deliberately: populating M.2_2 steals lanes from the second PCIe 5.0 ×16 slot.

### 1.3 Power & Cooling

| Component | Part | Specification |
|---|---|---|
| **PSU** | Seasonic VERTEX GX-1200 ATX 3.1 ✅ | 1,200 W · 80+ Gold · PCIe 5.1 · native 12V-2×6 · 135 mm FDB · **12-yr warranty** |
| **Case** | Fractal Design Meshify 2 XL | Full tower · high-airflow mesh · long GPU clearance |
| **Fans** | 5 × Noctua NF-A14x25 G2 PWM | 3 front intake · 1 rear · 1–2 top exhaust |
| **UPS** | APC Smart-UPS SMT2200IC ⚠️ | 2,200 VA ≈ **1,980 W** · replaceable battery |
| **UPS card** | APC Network Management Card 3 `AP9640` ⚠️ | SNMP alerting · optional |

> **On the 1,200 W.** NVIDIA's reference recommendation for the RTX 5080 is **850 W** — this is ~40% above it. That is deliberate: it buys headroom for the documented RTX 5090 upgrade path (575 W TGP), avoiding a PSU replacement later. **If the 5090 path is abandoned, an 850–1,000 W VERTEX is the correct part.** → [§10.5](#105-psu--1200-w-reconciled-not-reduced)

### 1.4 Backup & Network

| Component | Part | Specification |
|---|---|---|
| **NAS** | Synology DS923+ ⚠️ | 4-bay · ECC memory · optional 10 GbE — **read [§5](#5-nas-compatibility-warning) first** |
| **NAS drives** | WD Red Pro 12 TB `WD121KFGX` *or*<br>Seagate IronWolf Pro 12 TB `ST12000NT001` ⚠️ | 4 × 12 TB **CMR**, NAS-rated |
| **Array** | Synology SHR-2 or RAID 6 | ≈24 TB usable · two-drive fault tolerance |
| **Offline** | WD Elements *or* Seagate Expansion Desktop ⚠️ | 2 × 20 TB USB, rotated monthly |
| **Switch** | TP-Link Omada TL-SX1008 ⚠️ | 8-port 10 GbE · optional |
| **Cabling** | Certified Cat6A | 10 GbE |

### 1.5 Software

| Layer | Selection |
|---|---|
| Host OS | Windows 11 Pro — BitLocker, Hyper-V/WSL2, policy controls |
| Linux | Ubuntu 24.04 LTS under WSL2 |
| Runtimes | Node.js · Python (`uv` + per-project `.venv`) · Git · Docker where useful |
| Agent stack | OpenClaw · Codex CLI · Ollama · cloud API path |
| Data | Raw files + SHA-256 manifests · SQLite/FTS5 · CSV/JSONL · Chroma · DuckDB + Parquet |

### 📋 RAM Purchasing Rule

> Do **not** buy RAM from the description alone.
>
> 1. Open the ASUS ProArt X870E-CREATOR WIFI memory QVL
> 2. Filter: Ryzen 9000 · 64 GB modules · two-DIMM configuration
> 3. Select a **single matched 2 × 64 GB kit**
> 4. Prefer **DDR5-5600 stability** over unverified DDR5-6000
> 5. Boot at JEDEC defaults; enable EXPO only after extended testing passes
>
> **On ECC:** the original preferred an ECC UDIMM kit "if present on the QVL." Treat as unlikely to be actionable — ECC UDIMM validation on AM5 consumer boards is inconsistent and 2 × 64 GB ECC kits are rare. Proceed with non-ECC without treating it as a compromise. → [§10.3](#103-ecc-udimm--verify-before-designing-around-it)

---

## 2. Capacity & Drive Map

| Layer | Raw | Keep free | Content |
|---|---:|---:|---|
| OS NVMe | 2 TB | ≥ 400–500 GB | Windows · WSL VHDX · programs · repos · caches |
| Active AI NVMe | 4 TB | ≥ 800 GB | Models · datasets · OCR · SQLite · Chroma · DuckDB |
| **Internal total** | **6 TB** | ≈4.5–5 TB ceiling | Fast local production layer |
| NAS | 4 × 12 TB | ≈24 TB usable | Versioned backup · raw evidence · archive |
| Offline rotation | 2 × 20 TB | — | One connected only during backup; one stored offsite |

> **⚠️ An internal archive drive is not a backup.** It shares the chassis, the power rail and the operating system.

<details>
<summary><b>📁 Directory layout — click to expand</b></summary>

**NVMe 1 — 990 PRO 2 TB — System**
```text
C:\Windows · C:\Program Files · C:\Users\User
WSL2 Ubuntu VHDX  →  /home/user
active Git repositories · Python .venv · Node & Codex runtime
```

**NVMe 2 — 990 PRO 4 TB — Active AI-Core**
```text
AI-Core/
├── models/            ├── databases/
├── datasets/          │   ├── sqlite/
├── normalized/        │   └── duckdb/
├── transcripts/       ├── indexes/
├── chunks/            │   └── chroma/
├── logs/              └── outputs/current/
└── cache/
```

**Synology NAS — archive, evidence, backup**
```text
NAS/
├── raw-source-of-truth/     ├── configurations/
├── manifests-sha256/        ├── workstation-images/
├── sqlite-backups/          ├── project-archives/
├── business-outputs/        ├── immutable-snapshots/
└── staging/                 ← absorbs the deferred NVMe 3 role
    ├── incoming/  ├── completed/  ├── exports/
    ├── old-models/            └── rebuildable-indexes/
```

</details>

---

## 3. 24-Hour Operating Profile

OpenClaw stays available around the clock — **the GPU does not**.

| Service | Status | GPU | Operating rule |
|---|:--:|:--:|---|
| OpenClaw gateway / router | 🟢 Always | — | Run as a supervised service |
| Scheduler / task queue | 🟢 Always | — | Trigger jobs at controlled times |
| SQLite / Chroma memory | 🟢 Always | — | Clean shutdown · frequent backups |
| Cloud AI escalation | 🔵 On demand | — | **Default** for hard reasoning and final review |
| Ollama / Qwen fallback | 🔵 On demand | ◐ | Load only the required model |
| OCR / transcription | 🟡 Scheduled | ◐ | Batch during low-use periods |
| Heavy local LLM | 🔴 Justified only | ● | Never keep a large model resident without work |
| Browser / marketplace | 🟡 Scheduled | — | **Human approval** for publishing, payments, deletion, credentials |

---

## 4. Reliability Configuration

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
- Scheduled maintenance reboot weekly/monthly
- Services under systemd or a watchdog
- Separate Windows and WSL Python environments
- `uv` with one `.venv` per project

</td></tr>
</table>

### 🌡️ Thermal Targets

*Operational targets, not manufacturer limits.*

| Component | Preferred sustained |
|---|---:|
| CPU — normal agent work | **< 75 °C** |
| CPU — long all-core work | < 85 °C |
| GPU core — sustained compute | < 75 °C |
| GPU memory / hotspot | Monitor vendor sensors; avoid limits |
| NVMe | **< 65 °C** |
| Motherboard / VRM | Steady front-to-back airflow |

### 🧹 Dust Control

Positive pressure — three filtered front intakes, fewer/slower exhausts · Clean filters **every 1–2 months** in a dusty environment · Inspect heatsinks and fan bearings **every 6 months** · Never place the tower directly on the floor · Keep **15–20 cm** clearance around intakes and exhausts

---

## 5. NAS Compatibility Warning

> **🚨 Read before ordering the NAS.** Synology changed its drive-compatibility policy for 2025-generation Plus models, then partially reversed it. Which unit you buy determines which drives will work.

| Generation | Third-party HDDs | Detail |
|---|:--:|---|
| **DS923+** (2022, as specified) | ✅ **Unaffected** | Pre-2025 models are exempt. WD Red Pro and IronWolf Pro work normally. |
| **DS925+ / DS1525+** (2025 Plus) | ⚠️ **Needs DSM 7.3** | Launch policy blocked non-Synology drives at setup with *no bypass*. DSM 7.3 restored 3.5″ HDD and 2.5″ SATA SSD support from WD, Seagate and others. |
| **M.2 NVMe, all 2025 models** | ❌ **Still restricted** | The reversal does **not** cover M.2. NVMe storage pools still require drives from Synology's official compatibility list. |

**Action items**

- The DS923+ remains the lowest-friction choice — if still available at sensible pricing, the specified 12 TB drives work without qualification.
- Substituting a 2025-generation unit is likely (DS923+ dates to 2022). **Confirm DSM 7.3 or later before buying third-party drives.**
- Planning an NVMe cache in the NAS? Budget for **Synology-branded M.2** regardless of model.
- Check whether a DS923+ successor ships with 10 GbE built in — the specified unit needs the optional `E10G22-T1-Mini`, an extra line item.

---

## 6. Backup Policy

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

- Connect offline drive **A**, run verified backup, disconnect
- Next month use drive **B**
- Store the inactive drive in a **separate physical location**

</td><td>

- Restore-test a SQLite database
- Restore-test documents and one full project
- Review SMART across all SSDs and HDDs
- UPS self-diagnostics
- Confirm BitLocker + NAS recovery credentials accessible

</td></tr>
</table>

### Data Classification

| Class | Priority | | Class | Priority |
|---|:--:|---|---|:--:|
| Raw source files | 🔴 **Critical** | | Chroma indexes | 🟢 Rebuildable |
| SQLite manifests & ledgers | 🔴 **Critical** | | Ollama models | 🟢 Re-downloadable |
| Business / capstone outputs | 🔴 **Critical** | | OCR / temp cache | 🟢 Rebuildable |
| Configuration & scripts | 🔴 **Critical** | | | |

---

## 7. Power & Shutdown

**Recommended UPS** — APC Smart-UPS SMT2200IC or 230 V equivalent

| ✅ Connect to UPS | ❌ Do not connect |
|---|---|
| PC tower · primary monitor **only** · router · network switch · NAS | Laser printer · space heater · high-power speakers · secondary monitors |

**Shutdown sequence**

```
1. Alert immediately on utility failure
2. Stop new heavy jobs
3. Checkpoint databases and active work
4. Shut down local models
5. Gracefully stop WSL, then Windows — before battery exhaustion
6. Shut down NAS once workstation data is safe
```

> **Size on watts, not VA.** A 2,200 VA Smart-UPS delivers ≈1,980 W. Confirm that sustains tower plus networking for the runtime you actually need.

---

## 8. Pre-Purchase Checklist

**Components**
- [ ] CPU is **boxed** Ryzen 9 9950X (`100-100001277WOF`), not an unverified tray unit
- [ ] Cooler is the **LBC** variant — check the engraving on the base 🔧
- [ ] RAM part number is on the **current** ASUS QVL, or explicitly vendor-validated
- [ ] PSU is the **ATX 3.1** revision with a **native 12V-2×6** cable — early VERTEX units shipped 12VHPWR
- [ ] NAS disks are **CMR, not SMR**
- [ ] NAS drive-compatibility policy confirmed for the exact model → [§5](#5-nas-compatibility-warning)

**Physical fit**
- [ ] Case supports 168 mm cooler height
- [ ] Cooler clears RAM height and the side panel
- [ ] GPU length, thickness and cable bend radius fit the case
- [ ] Both NVMe drives receive motherboard heatsinks
- [ ] No GPU adapter daisy-chain

**System**
- [ ] M.2 lane sharing understood — populating M.2_2 affects the second PCIe 5.0 slot
- [ ] UPS output **wattage**, not only VA, is adequate
- [ ] GPU, board, SSDs and UPS carry **official Indonesian warranty**, not grey-market
- [ ] Builder performs extended memory, CPU, GPU, SSD and power testing
- [ ] No imminent Zen 6 / AM5 refresh before paying full price for the current flagship

---

## 9. Burn-In & Acceptance

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
> Zero memory errors · zero WHEA hardware errors · no unexplained reboot · no thermal throttling within configured limits · no GPU power-connector warning · no NVMe SMART warning · successful UPS-triggered graceful shutdown · successful backup restoration

---

## 10. Correction Register

*Each item changes the original decision record. Rationale and source given so each can be accepted or rejected on evidence.*

### 10.1 Cooler variant — standard-base → LBC

The original specified *"NH-D15 G2 standard-base … not the HBC version intended primarily for highly convex Intel CPUs."* Ruling out HBC is correct; the conclusion stops one step short.

Noctua ships **three** base-convexity versions. The **LBC (Low Base Convexity)** version achieves optimal contact on relatively flat CPUs and is documented by Noctua as **ideal for AM5** — including for combining the lowest possible CCD temperatures with the lowest possible IOD temperatures. The standard version is the medium-convexity all-rounder; HBC targets de-shaped Intel 12th–14th gen under high ILM pressure.

The standard version *works* on AM5. LBC is the manufacturer's specified optimum for this socket, **at the same price**.

### 10.2 Archive/staging NVMe — deferred, not deleted

The original buys a third 4 TB 990 PRO **and** a 24 TB dual-parity NAS **and** 40 TB of rotating offline capacity. The NVMe's defined contents — completed outputs, exports, snapshots, old models, rebuildable indexes, temporary ingestion — are archive-class data the NAS already holds, at 6× the capacity, with parity and snapshots the internal drive lacks.

The original already applies this reasoning to the *fourth* M.2 slot: *"Avoid buying unused flash too early; preserve expansion."* With a NAS in the build, that logic reaches the third slot too.

**Buy it when** the active 4 TB exceeds 75–80% after NAS offload · ingestion staging over 10 GbE is a *measured* bottleneck · write separation shows measurable benefit. A mid-tier Gen4 NVMe suffices then — archive workloads do not need 2,400 TBW.

**Saves ≈Rp 5.5–7.5 juta at build time.**

### 10.3 ECC UDIMM — verify before designing around it

The original offers *"Kingston FURY Renegade Pro DDR5 ECC UDIMM kit if present on ASUS QVL"* as first preference. Treat as unlikely to be actionable: ECC UDIMM support on AM5 consumer boards is inconsistent and often unvalidated even where the CPU supports ECC; Renegade Pro ECC kits target workstation platforms and are rarely offered as 2 × 64 GB.

Check the QVL. If nothing qualifies, proceed with non-ECC — the backup discipline in [§6](#6-backup-policy) is the real integrity control. **If ECC is a hard requirement, that is a Threadripper/W790 platform decision, not a DIMM substitution.**

### 10.4 GPU — dissent recorded, decision upheld

For the record: 16 GB is the same VRAM ceiling as cards costing roughly a third as much, and half what the RTX 5090 offers. For a workload list of embeddings, OCR, Whisper and *"moderate local inference,"* an RTX 5060 Ti 16 GB delivers the same ceiling at ≈Rp 8–11 juta; for genuine local inference of 27–32B models, only 32 GB changes what fits.

**The decision record selects the RTX 5080 deliberately, and that choice is retained throughout this document.** The measured upgrade triggers in [§11](#-upgrade-triggers) are the correct mechanism for revisiting it.

### 10.5 PSU — 1,200 W reconciled, not reduced

NVIDIA's reference system-power recommendation for the RTX 5080 is **850 W**; this build specifies **1,200 W**, ≈40% above. Justified here because the RTX 5090 upgrade path is documented and the 5090's 575 W TGP genuinely requires this class of unit — buying now avoids replacing the PSU later.

The reasoning should be explicit: **the 1,200 W is bought for the future GPU, not the current one.**

### 10.6 NAS drive-compatibility policy — new risk

Not an error in the original — the policy change post-dates typical guidance and does not affect the DS923+ as specified. It becomes decision-relevant the moment a 2025-generation model is substituted, which is likely given DS923+ availability in 2026. → [§5](#5-nas-compatibility-warning)

---

## 11. Maintenance, Triggers & Budget

### 🔧 Maintenance Schedule

| Item | Interval | Service window |
|---|---|---|
| Dust filters | 1–2 months | Clean; replace only if damaged |
| Fans | 6 months | Replace on bearing noise, vibration, RPM instability |
| Thermal paste | 3–5 years, or on temp change | Replace only when needed |
| SSD health | Monthly SMART | 4–8 years depending on writes |
| HDD health | Monthly SMART + scrub | Replace proactively on errors or warranty horizon |
| UPS self-test | Monthly | Battery commonly 3–5 years |
| NAS scrub | Monthly–quarterly | Replace failing disks immediately |
| BIOS | Quarterly review | Update only for security, stability, compatibility |
| Windows / WSL | Monthly controlled | Keep LTS and supported releases |
| GPU | Continuous monitoring | First major upgrade likely 4–7 years |
| Case / cooler / PSU | Annual inspection | Outlasts multiple CPU/GPU cycles |

### 📈 Upgrade Triggers

<table>
<tr><th>RTX 5090 — when <i>measured</i></th><th>RAM beyond 128 GB — when</th></tr>
<tr valign="top"><td>

- Repeated CUDA OOM failures at 16 GB
- Required model won't run at chosen quantization
- Daily local inference runs many hours
- Cloud API cost exceeds amortized GPU cost
- Privacy rules prevent cloud escalation
- Image/video generation becomes revenue work
- Multiple users need concurrent local inference

</td><td>

- Sustained committed memory > ≈100–110 GB
- WSL, agents, databases, models regularly page to disk
- Larger local models need CPU/RAM offload
- Multiple concurrent workers proven useful

</td></tr>
</table>

### 💰 Budget Envelope — Indonesia

*Planning ranges, **not** live quotations. All IDR figures ⚠️ unverified — re-check at purchase.*

| Area | Original | **This revision** |
|---|---:|---:|
| Core tower — CPU, board, RAM, GPU, NVMe, PSU, cooler, case, fans | Rp 80–105 juta | **Rp 74–98 juta** |
| APC Smart-UPS 2200 VA class | Rp 12–25 juta | Rp 12–25 juta |
| Synology DS923+ · 4 × 12 TB | Rp 35–55 juta | Rp 35–55 juta |
| Two 20 TB offline drives | Rp 15–25 juta | Rp 15–25 juta |
| 10 GbE switch / cabling *(optional)* | Rp 7–15 juta | Rp 7–15 juta |
| **Complete 24-hour BIFL environment** | Rp 142–225 juta | **Rp 136–218 juta** |

Difference is the deferred archive NVMe. Staged purchase is viable — tower and UPS first, then NAS, then offline rotation.

> **⚠️ Do not remove the UPS or backup plan to afford a higher GPU.**

---

## Verification Status

**✅ Verified** against manufacturer or major-retailer sources
Ryzen 9 9950X MPN and specifications · ASUS ProArt X870E-Creator WiFi feature set and M.2 topology · G.Skill Flare X5 128 GB MPN · Noctua NH-D15 G2 variant guidance · Samsung 990 PRO MPNs, performance and TBW · Seasonic VERTEX GX-1200 specifications · RTX 5080 specifications and AIB model names · Synology 2025 drive-compatibility policy and DSM 7.3 reversal

**⚠️ Not verified — confirm before purchase**
All IDR pricing (volatile; Indonesian GPU pricing moves weekly) · APC, Synology, WD/Seagate, Fractal and TP-Link availability in Indonesia · current DS923+ availability and successor models · RTX 5090 pricing · whether a Zen 6 / AM5 refresh is imminent

---

## Sources

**Project evidence** — OpenClaw BIFL P4 Grade Decision and 24-hour addendum (uploaded decision record)

**Official technical sources**

[AMD Ryzen 9 9950X](https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-9-9950x.html) ·
[ASUS ProArt X870E-CREATOR WIFI](https://www.asus.com/id/motherboards-components/motherboards/proart/proart-x870e-creator-wifi/techspec/) ·
[NVIDIA RTX 5080](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/) ·
[Noctua — NH-D15 G2 versions explained](https://noctua.at/en/nh-d15-g2-versions-explained) ·
[Noctua NH-D15 G2 LBC](https://www.noctua.at/en/products/nh-d15-g2-lbc/features) ·
[G.Skill Flare X5 DDR5 EXPO](https://www.gskill.com/products/1/165/396/Flare-X5-DDR5-AMD-EXPO) ·
[Samsung 990 PRO datasheet](https://download.semiconductor.samsung.com/resources/data-sheet/samsung_nvme_ssd_990_pro_datasheet_rev.2.0.pdf) ·
[Seasonic VERTEX GX ATX 3.1](https://seasonic.com/vertex-gx/) ·
[Fractal Meshify 2 XL](https://support.fractal-design.com/support/solutions/articles/4000174747-meshify-2-xl) ·
[Tom's Hardware — Synology restores third-party drive support in DSM 7.3](https://www.tomshardware.com/pc-components/nas/synology-walks-back-controversial-compatibility-policy-for-2025-nas-units-third-party-hdd-and-ssd-support-returns-with-diskstation-manager-7-3-update)

---

<div align="center">

## 🛒 Final Purchase Line

**AMD Ryzen 9 9950X** · **ASUS ProArt X870E-CREATOR WIFI** · **128 GB QVL 2 × 64 GB DDR5**
**Premium RTX 5080 16 GB** · **Samsung 990 PRO 2 TB + 4 TB** · **Seasonic VERTEX GX-1200**
**Noctua NH-D15 G2 LBC** · **Fractal Meshify 2 XL** · **5 × Noctua NF-A14x25 G2**
**APC Smart-UPS 2200 VA** · **Synology DS923+ · 4 × 12 TB CMR** · **2 × 20 TB offline, rotated**

*Third NVMe deferred to trigger ([§10.2](#102-archivestaging-nvme--deferred-not-deleted)) · Cooler is the **LBC** variant ([§10.1](#101-cooler-variant--standard-base--lbc))*

</div>
