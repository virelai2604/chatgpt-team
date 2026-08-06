# OpenClaw 24-Hour BIFL Workstation

## Tier 1 Compute + Tier 3 Storage, Backup, and Data Discipline

**Prepared:** 2026-08-06
**Purpose:** Always-available OpenClaw / Gunawan AgentOS dispatcher, WSL2 automation, RAG and indexing, cloud-model escalation, scheduled local AI jobs, and durable business-data retention.

> **Decision of record:** RTX 5080-based Tier 1 compute platform plus Tier 3 storage, backup, UPS, monitoring and data separation. Do not move to RTX 5090 unless measured local-AI workloads repeatedly exceed 16 GB VRAM, or local inference directly generates enough revenue to justify the additional capital, power and heat.

**Document status:** Merged from the OpenClaw 24-hour BIFL decision record, with component-level corrections applied where manufacturer documentation contradicted the original selection. Corrections are marked **[CORRECTED]** and explained in §14. Part numbers verified against vendor or major-retailer sources are marked ✅.

---

## 1. Exact Purchase Specification

| Category | Exact recommended brand/model | Capacity / specification | Qty | Primary purpose | BIFL rationale |
|---|---|---:|---:|---|---|
| CPU | **AMD Ryzen 9 9950X** — boxed `100-100001277WOF` ✅ | 16C/32T; 4.3 GHz base, 5.7 GHz boost; 170 W; 80 MB cache; AM5 | 1 | WSL2, indexing, OCR, databases, containers, automation | Mature AM5 platform; high multicore capacity; replaceable desktop CPU |
| CPU cooler | **Noctua NH-D15 G2 LBC** ✅ **[CORRECTED]** | 168 mm tall; 8 heatpipes; 2 × 140 mm fans; Low Base Convexity | 1 | Continuous CPU cooling | Air cooling avoids pump failure; 6-year warranty; replaceable fans. **LBC is Noctua's specified optimum for AM5** — see §14.1 |
| Motherboard | **ASUS ProArt X870E-CREATOR WIFI** ✅ | AM5; 4 DIMM, max 256 GB; 4 × M.2 (2 × PCIe 5.0 ×4, 2 × PCIe 4.0); 10 GbE + 2.5 GbE; Wi-Fi 7; 2 × USB4 40 Gbps; 16+2+2 stages | 1 | Expansion, networking, storage, serviceability | Creator I/O, BIOS FlashBack, four NVMe slots, 24/7-oriented protection |
| RAM | **QVL-approved 2 × 64 GB DDR5-5600 EXPO UDIMM kit** — G.Skill Flare X5 `F5-6000J3244G64GX2-FX5` ✅ is a verified candidate (run at 5600) | **128 GB total, 2 × 64 GB** | 1 kit | WSL, Chroma, SQLite, DuckDB, browser agents, model spillover | Two-DIMM layout far more stable than four; preserves 192/256 GB upgrade path. **ECC UDIMM: see §14.3** |
| GPU | **ASUS TUF Gaming RTX 5080 16 GB OC** `TUF-RTX5080-O16G-GAMING` ✅ or **MSI RTX 5080 16G SUPRIM SOC** | 16 GB GDDR7; 10,752 CUDA; 960 GB/s; 360 W TGP | 1 | CUDA, embeddings, OCR, Whisper, moderate local inference | Premium cooler and PCB. **Dissent recorded — see §14.4** |
| OS NVMe | **Samsung 990 PRO 2 TB** `MZ-V9P2T0BW` ✅ | PCIe 4.0 ×4, NVMe 2.0; TLC; DRAM; **1,200 TBW**; 7,450/6,900 MB/s | 1 | Windows, WSL VHDX, applications, repositories | Mature high-end Gen4 drive; Samsung Magician health monitoring |
| Active AI/data NVMe | **Samsung 990 PRO 4 TB** `MZ-V9P4T0BW` ✅ | PCIe 4.0 ×4; TLC; 4 GB DRAM; **2,400 TBW** | 1 | Models, datasets, normalized files, transcripts, databases, active outputs | High endurance and capacity for write-heavy AI work |
| Archive/staging NVMe | **DEFERRED — do not buy at build time** **[CORRECTED]** | (was: 3rd × 990 PRO 4 TB) | 0 | — | Redundant against a 24 TB NAS at build time. Buy on trigger — see §14.2 |
| Spare M.2 slots | Leave M.2_2 and M.2_4 empty initially | Future 4–8 TB NVMe | 0 | Future growth | Avoid buying unused flash too early |
| PSU | **Seasonic VERTEX GX-1200 ATX 3.1** ✅ | 1,200 W; 80 PLUS Gold; ATX 3.1 / PCIe 5.1; native 12V-2×6; 135 mm FDB fan; **12-yr warranty** | 1 | Stable long-uptime power delivery | Sized for the documented RTX 5090 upgrade path — see §14.5 |
| Case | **Fractal Design Meshify 2 XL** | Full tower; high-airflow mesh; extensive drive and fan support | 1 | Cooling, cable management, GPU clearance | Large serviceable chassis; supports future GPU/storage/fan upgrades |
| Front intake fans | **Noctua NF-A14x25 G2 PWM** | 140 mm PWM | 3 | Filtered front intake | High airflow, replaceable, long warranty |
| Rear exhaust fan | **Noctua NF-A14x25 G2 PWM** | 140 mm PWM | 1 | Rear exhaust | Consistent fan family and control curve |
| Top exhaust fan | **Noctua NF-A14x25 G2 PWM** | 140 mm PWM | 1–2 | Low-speed heat exhaust | Run only as needed to limit dust and noise |
| UPS | **APC Smart-UPS SMT2200IC** or 230 V equivalent | 2,200 VA / ≈1,980 W | 1 | Graceful shutdown and write protection | Smart monitoring, replaceable battery, headroom for tower and network |
| UPS network card | **APC Network Management Card 3 AP9640** | SNMP / network monitoring | 1 optional | Remote alerting and graceful shutdown | Useful for unattended 24-hour operation |
| Primary backup NAS | **Synology DS923+** | 4-bay; ECC memory; optional 10 GbE | 1 | Local versioned backup and shared archive | Replaceable drives, snapshots, mature software. **Model-choice caveat — §10** |
| NAS drives | **WD Red Pro 12 TB `WD121KFGX`** or **Seagate IronWolf Pro 12 TB `ST12000NT001`** | 12 TB CMR, NAS-rated | 4 | RAID / SHR storage | CMR, vibration tolerance, multi-year warranty |
| NAS layout | Synology SHR-2 or RAID 6 | ≈24 TB usable from 4 × 12 TB before overhead | 1 array | Two-drive fault tolerance | Better resilience than single parity for a business archive |
| Offline backup | **WD Elements Desktop 20 TB** or **Seagate Expansion Desktop 20 TB** | USB external HDD | 2, rotated | Offline / off-site backup | Protects against ransomware, NAS failure, theft, operator error |
| OS | **Windows 11 Pro** | Current supported release | 1 | Business apps and host control | BitLocker, Hyper-V/WSL2, policy controls |
| Linux layer | **Ubuntu 24.04 LTS under WSL2** | LTS | 1 distro | Python, Node, Ollama, automation, local RAG | Stable Linux-first toolchain |
| Network switch | **TP-Link Omada TL-SX1008** or equivalent | 8-port 10 GbE | 1 optional | Workstation-to-NAS transfer | Makes Tier 3 storage practical at scale |
| Ethernet cabling | Certified Cat6A | 10 GbE | As needed | NAS / workstation link | Durable, standards-based |

### RAM purchasing rule

Do not buy RAM from the generic description alone. Before purchase:

1. Open the ASUS ProArt X870E-CREATOR WIFI memory QVL.
2. Filter for Ryzen 9000, 64 GB module capacity, two-DIMM configuration.
3. Select a **single matched 2 × 64 GB kit**.
4. Prefer DDR5-5600 stability over unverified DDR5-6000 speed.
5. Run at JEDEC defaults first; enable EXPO only after extended memory testing passes.

---

## 2. Capacity Map

| Layer | Raw capacity | Recommended usable target | Content |
|---|---:|---:|---|
| OS NVMe | 2 TB | Keep ≥ 400–500 GB free | Windows, WSL VHDX, programs, repositories, temp caches |
| Active AI NVMe | 4 TB | Keep ≥ 800 GB free | Ollama models, datasets, OCR/transcripts, SQLite, Chroma, DuckDB, active work |
| Archive/staging NVMe | *(deferred)* | — | Moved to NAS at build time — see §14.2 |
| Internal NVMe total | **6 TB raw** at build | ≈4.5–5 TB working ceiling | Fast local production layer |
| NAS | 4 × 12 TB | ≈24 TB usable with dual parity | Versioned backup, raw evidence, business archive |
| Offline rotation | 2 × 20 TB | One connected only during backup; one stored separately | Disaster recovery and ransomware protection |

> **Important:** an internal archive NVMe is **not** a backup. It sits in the same chassis, on the same power rail, behind the same OS.

---

## 3. Recommended Drive Assignment

### NVMe 1 — Samsung 990 PRO 2 TB (M.2_1, PCIe 5.0 slot)

```text
C:\Windows
C:\Program Files
C:\Users\User
WSL2 Ubuntu VHDX
/home/user
active Git repositories
Python virtual environments
Node and Codex runtime
```

### NVMe 2 — Samsung 990 PRO 4 TB (M.2_3, PCIe 4.0) — Active AI-Core

```text
AI-Core/
├── models/
├── datasets/
├── normalized/
├── transcripts/
├── chunks/
├── databases/
│   ├── sqlite/
│   └── duckdb/
├── indexes/
│   └── chroma/
├── outputs/
│   └── current/
├── logs/
└── cache/
```

> Placed in **M.2_3** deliberately: M.2_2 shares bandwidth with the second PCIe 5.0 ×16 slot, so leaving it empty preserves the option of a second accelerator without re-seating drives.

### Synology NAS — archive, evidence, and backup

```text
NAS/
├── raw-source-of-truth/
├── manifests-sha256/
├── sqlite-backups/
├── business-outputs/
├── configurations/
├── workstation-images/
├── project-archives/
├── immutable-snapshots/
└── staging/              # absorbs the deferred NVMe 3 role
    ├── incoming/
    ├── completed/
    ├── exports/
    ├── old-models/
    └── rebuildable-indexes/
```

---

## 4. 24-Hour BIFL Operating Profile

OpenClaw should remain available 24 hours, but the GPU should not run at full load continuously.

| Service | 24-hour status | GPU demand | Operating rule |
|---|---|---|---|
| OpenClaw gateway / router | Always running | None | Run as a supervised service |
| Scheduler / task queue | Always running | None | Trigger jobs at controlled times |
| SQLite / Chroma memory | Available continuously | None | Clean shutdown and frequent backups |
| Cloud AI escalation | On demand | No local GPU | Default for difficult reasoning and final review |
| Ollama / Qwen fallback | On demand | Medium | Load only the required model |
| OCR / transcription | Scheduled | Medium | Run in batches during low-use periods |
| Heavy local LLM | Only when justified | High | Do not keep a large model resident without work |
| Browser / marketplace jobs | Scheduled | Mostly CPU/RAM | Human approval for publishing, payments, deletion, credentials |

---

## 5. Reliability Configuration

### BIOS

- Update to a stable ASUS BIOS release, not a beta.
- Load optimized defaults after updating.
- Enable EXPO only after baseline testing.
- Enable memory context restore only after stability is established.
- Do not overclock.
- Use AMD Eco Mode or a sensible PPT limit if noise and heat are priorities.
- Keep PCIe link settings on Auto unless troubleshooting.
- Enable Restore on AC Power Loss only if UPS and automatic service recovery are configured.

### Windows and WSL

- BitLocker enabled, recovery keys stored offline.
- Keep the WSL VHDX on the internal OS NVMe.
- Never keep actively written SQLite or Chroma databases on USB HDDs or network shares.
- Controlled Windows Update restart windows.
- Scheduled maintenance reboot weekly or monthly.
- Run OpenClaw, Ollama and dependent services under systemd or a watchdog.
- Maintain separate Windows and WSL Python environments.
- Use `uv` with one `.venv` per project.

### Thermal targets

Operational targets, not manufacturer limits:

| Component | Preferred sustained range |
|---|---:|
| CPU during normal agent work | Below 75 °C |
| CPU during long all-core work | Preferably below 85 °C |
| GPU core during sustained compute | Preferably below 75 °C |
| GPU memory / hotspot | Monitor vendor sensors; avoid sustained operation near limits |
| NVMe drives | Preferably below 65 °C |
| Motherboard / VRM | Maintain steady front-to-back airflow |

### Dust control

- Positive pressure: three filtered front intakes, fewer or lower-speed exhausts.
- Clean front and bottom filters every 1–2 months in a dusty environment.
- Inspect heatsinks and fan bearings every 6 months.
- Do not place the tower directly on the floor.
- Keep 15–20 cm clearance around intake and exhaust areas.

---

## 6. Backup Policy

### Daily
- SQLite online backup or safe snapshot.
- Incremental backup of Markdown, JSON, CSV, manifests, configurations and business outputs to NAS.
- Chroma backup after ingestion/indexing completes.

### Weekly
- NAS snapshot.
- Verify backup job logs.
- Export critical database tables to CSV/JSONL.
- Copy essential configuration and recovery documents.

### Monthly
- Connect offline drive A, run a complete verified backup, disconnect.
- Next month use drive B.
- Store the inactive drive in a separate physical location.

### Quarterly
- Restore-test a sample SQLite database.
- Restore-test several documents and one full project.
- Review SMART data for all SSDs and HDDs.
- Test UPS self-diagnostics.
- Confirm BitLocker and NAS recovery credentials remain accessible.

### Data classification

| Data class | Priority |
|---|---|
| Raw source files | **Critical** |
| SQLite manifests and ledgers | **Critical** |
| Business / capstone outputs | **Critical** |
| Configuration and scripts | **Critical** |
| Chroma indexes | Rebuildable |
| Ollama models | Re-downloadable |
| OCR / temp cache | Rebuildable |

---

## 7. UPS Sizing and Shutdown

Normal OpenClaw operation may draw well under 1,000 W, but GPU transients and simultaneous CPU/GPU load require margin.

**Recommended:** APC Smart-UPS SMT2200IC or equivalent 230 V model.

**Connect to UPS:** PC tower · primary monitor only · router · network switch · NAS
**Do not connect:** laser printer · space heater · high-power speakers · nonessential secondary monitors

**Shutdown sequence:**

1. Alert immediately on utility failure.
2. Stop new heavy jobs.
3. Checkpoint databases and active work.
4. Shut down local models.
5. Gracefully stop WSL and Windows before battery exhaustion.
6. Shut down NAS after workstation data is safe.

> Size on **watts, not VA**. A 2,200 VA Smart-UPS delivers ≈1,980 W; confirm that sustains tower plus networking for the runtime you need.

---

## 8. Compatibility Checks Before Payment

- [ ] CPU is boxed AMD Ryzen 9 9950X (`100-100001277WOF`), not an unverified tray unit.
- [ ] Cooler is the **LBC** variant — verify the engraving on the base. **[CORRECTED]**
- [ ] Case supports 168 mm cooler height.
- [ ] Cooler clears RAM height and the case side panel.
- [ ] Exact RTX 5080 length, thickness and power-cable bend radius fit the case.
- [ ] RAM part number appears on the current ASUS QVL or is explicitly validated by the RAM vendor.
- [ ] PSU is the **ATX 3.1** revision with a **native 12V-2×6** cable — early VERTEX units shipped 12VHPWR.
- [ ] No GPU adapter daisy-chain is used.
- [ ] Both NVMe drives receive motherboard heatsinks.
- [ ] M.2 lane sharing understood: populating M.2_2 affects the second PCIe 5.0 slot.
- [ ] UPS output **wattage**, not only VA, is adequate.
- [ ] GPU, motherboard, SSDs and UPS carry official Indonesian warranty, not grey-market.
- [ ] NAS disks are **CMR, not SMR**.
- [ ] NAS drive-compatibility policy confirmed for the exact model purchased — see §10. **[NEW]**
- [ ] Builder performs extended memory, CPU, GPU, SSD and power testing.
- [ ] Confirm no imminent Zen 6 / AM5 refresh before paying full price for the current flagship.

---

## 9. Burn-In and Acceptance Test

Run before accepting the system:

1. **MemTest86** — at least four complete passes.
2. **OCCT memory and CPU** — 2–4 hours.
3. **Prime95 blend or y-cruncher** — 1–2 hours, observing temperatures.
4. **GPU compute/stress test** — 1–2 hours.
5. **Combined CPU + GPU load** — 30–60 minutes, testing PSU and case airflow.
6. **NVMe extended test** — SMART inspection plus large sequential write/read verification.
7. **Network test** — sustained 10 GbE transfer to NAS.
8. **UPS test** — simulated utility failure and graceful shutdown.
9. **WSL test** — restart, mount, Docker/Ollama/OpenClaw service recovery.
10. **Backup restore test** — restore one project and one SQLite database.

**Accept only if there are:** zero memory errors · zero WHEA hardware errors · no unexplained reboot · no thermal throttling within configured limits · no GPU power-connector warning · no NVMe SMART warning · successful UPS-triggered graceful shutdown · successful backup restoration.

---

## 10. NAS Model and Drive-Compatibility Caveat **[NEW]**

Synology changed its drive-compatibility policy for 2025-generation Plus models, and the situation is still in motion. This affects which NAS you buy and which drives go in it.

| Model generation | Third-party HDD support | Notes |
|---|---|---|
| **DS923+** (2022, as specified) | **Unaffected** | Pre-2025 models are exempt from the policy. WD Red Pro and IronWolf Pro work normally. |
| **DS925+ / DS1525+** (2025 Plus series) | Restored **with DSM 7.3** | The launch policy blocked non-Synology drives at setup with no bypass. Synology walked it back in DSM 7.3, restoring 3.5″ HDD and 2.5″ SATA SSD support from WD, Seagate and others. |
| **M.2 NVMe, all 2025 models** | **Still restricted** | The walk-back does **not** cover M.2. Storage pools on NVMe still require drives from Synology's official compatibility list. |

**Practical guidance:**

- If the DS923+ is still available at a sensible price, it remains the lowest-friction choice for this build — the 12 TB WD/Seagate drives specified above work without qualification.
- If you substitute a 2025-generation model (likely, given the DS923+ dates to 2022), confirm the unit ships with or can be updated to **DSM 7.3 or later** *before* buying third-party drives.
- If you plan an NVMe read/write cache in the NAS at any point, budget for Synology-branded M.2 drives regardless of model, since that restriction still stands.
- Also check whether a DS923+ successor with 10 GbE built in has shipped — the specified unit needs the optional E10G22-T1-Mini to reach 10 GbE, which is an extra line item.

---

## 11. Maintenance and Replacement Schedule

| Item | Inspection interval | Expected service window |
|---|---|---|
| Dust filters | 1–2 months | Clean; replace only if damaged |
| Fans | 6 months | Replace on bearing noise, vibration or RPM instability |
| Thermal paste | After 3–5 years, or on temperature change | Replace only when needed |
| SSD health | Monthly SMART review | Typically 4–8 years depending on writes |
| HDD health | Monthly SMART and scrub | Replace proactively on errors or warranty horizon |
| UPS self-test | Monthly | Battery commonly 3–5 years |
| NAS scrub | Monthly or quarterly | Repair/replace failing disks immediately |
| BIOS | Review quarterly | Update only for security, stability or required compatibility |
| Windows / WSL | Monthly controlled maintenance | Keep LTS and supported releases |
| GPU | Monitor continuously | Likely first major upgrade after 4–7 years |
| Case / cooler / PSU | Annual inspection | Designed to outlast multiple CPU/GPU cycles |

---

## 12. Upgrade Triggers

### Buy the archive/staging NVMe when **[NEW]**

- The active 4 TB NVMe repeatedly exceeds 75–80% usage after NAS offload.
- Ingestion staging over 10 GbE becomes a measured bottleneck, not an assumed one.
- Write-workload separation produces a measurable benefit.
- A dedicated scratch/cache drive is required.

At that point a mid-tier high-capacity Gen4 NVMe is sufficient — the archive role does not need 990 PRO endurance.

### Upgrade to RTX 5090 when one or more is *measured*

- Repeated CUDA out-of-memory failures at 16 GB.
- The required local model cannot run acceptably at the chosen quantization.
- Daily local inference runs for many hours.
- Cloud API costs exceed the amortized GPU cost.
- Privacy rules prevent cloud escalation.
- Local image/video generation becomes a revenue workload.
- Multiple users require concurrent local inference.

### Upgrade RAM beyond 128 GB when

- Sustained committed memory exceeds ≈100–110 GB.
- WSL, browser agents, databases and local models regularly page to disk.
- Larger local models require CPU/RAM offload.
- Multiple concurrent workers are proven useful.

---

## 13. Budget Envelope for Indonesia

Planning ranges, **not** live quotations. All IDR figures unverified — re-check at purchase.

| Area | Original plan | This revision |
|---|---:|---:|
| Core tower — CPU, board, RAM, RTX 5080, NVMe, PSU, cooler, case, fans | Rp 80–105 juta | **Rp 74–98 juta** |
| APC Smart-UPS 2200 VA class | Rp 12–25 juta | Rp 12–25 juta |
| Synology DS923+ + 4 × 12 TB | Rp 35–55 juta | Rp 35–55 juta |
| Two 20 TB offline drives | Rp 15–25 juta | Rp 15–25 juta |
| 10 GbE switch / cabling (optional) | Rp 7–15 juta | Rp 7–15 juta |
| **Complete 24-hour BIFL environment** | **Rp 142–225 juta** | **Rp 136–218 juta** |

Difference is the deferred archive NVMe (≈Rp 5.5–7.5 juta).

A staged purchase is viable: tower and UPS first, then NAS, then offline rotation. **Do not remove the UPS or backup plan to afford a higher GPU.**

---

## 14. Correction Register

Each item below changes the original decision record. Rationale and source given so the change can be accepted or rejected on evidence.

### 14.1 Cooler variant — standard-base → LBC

The original specified "NH-D15 G2 standard-base … not the HBC version intended primarily for highly convex Intel CPUs." Ruling out HBC is correct, but the conclusion stops one step short.

Noctua ships three base-convexity versions. The **LBC (Low Base Convexity)** version achieves optimal contact on relatively flat CPUs and is documented by Noctua as **ideal for AM5**, including for combining the lowest possible CCD temperatures with the lowest possible IOD temperatures. The standard version is the medium-convexity all-rounder; HBC targets de-shaped Intel 12th–14th gen under high ILM pressure.

The standard version will work on AM5. LBC is the manufacturer's specified optimum for this socket, at the same price. The variant is engraved on the base.

### 14.2 Archive/staging NVMe — deferred, not deleted

The original buys a third 4 TB 990 PRO *and* a 24 TB dual-parity NAS *and* 40 TB of rotating offline capacity. The NVMe's defined contents — completed outputs, exports, snapshots, old models, rebuildable indexes, temporary ingestion — are archive-class data that the NAS already holds, at 6× the capacity, with parity and snapshots the internal drive lacks.

The original document already applies exactly this reasoning to the fourth M.2 slot: *"Avoid buying unused flash too early; preserve expansion."* With a NAS in the build, that logic reaches the third slot too.

This is a **deferral with a defined trigger** (§12), not a removal. If ingestion staging over 10 GbE proves to be a real bottleneck, buy the drive then — and a mid-tier Gen4 NVMe will do, since archive workloads do not need 2,400 TBW.

**Saves ≈Rp 5.5–7.5 juta at build time.**

### 14.3 ECC UDIMM — verify before designing around it

The original offers "Kingston FURY Renegade Pro DDR5 ECC UDIMM kit if present on ASUS QVL" as first preference. Treat this as unlikely to be actionable:

- ECC UDIMM support on AM5 consumer boards is inconsistent and often unvalidated, even where the CPU technically supports ECC.
- Renegade Pro ECC kits target workstation platforms and are not commonly offered as 2 × 64 GB.
- The probability that a 2 × 64 GB ECC UDIMM kit appears on the ProArt X870E QVL is low.

Check the QVL. If nothing qualifies, proceed with the non-ECC 2 × 64 GB kit without treating it as a compromise — the backup discipline in §6 is the real integrity control here. If ECC is a hard requirement, that is a Threadripper/W790 platform decision, not a DIMM substitution.

### 14.4 GPU — dissent recorded, decision upheld

For the record: 16 GB is the same VRAM ceiling as cards costing roughly a third as much, and half of what the RTX 5090 offers. For a workload list of embeddings, OCR, Whisper and "moderate local inference," an RTX 5060 Ti 16 GB delivers the same ceiling at ≈Rp 8–11 juta; for genuine local inference of 27–32B models, only 32 GB changes what fits.

The decision record selects the RTX 5080 deliberately, and that choice is retained throughout this document. The measured upgrade triggers in §12 are the correct mechanism for revisiting it.

### 14.5 PSU — 1,200 W reconciled, not reduced

NVIDIA's reference system-power recommendation for the RTX 5080 is 850 W; this build specifies 1,200 W, roughly 40% above it. That is **justified here** because §12 documents an RTX 5090 upgrade path, and the 5090's 575 W TGP genuinely requires this class of unit. Buying it now avoids replacing the PSU later.

The reasoning should be explicit, though: the 1,200 W is bought for the *future* GPU, not the current one. If the 5090 path is abandoned, an 850–1,000 W VERTEX is the correct part.

### 14.6 NAS drive-compatibility policy — new risk, see §10

Not an error in the original — the policy change post-dates typical guidance and does not affect the DS923+ as specified. It becomes decision-relevant the moment a 2025-generation model is substituted, which is likely given DS923+ availability in 2026.

---

## 15. Verification Status

**✅ Verified** against manufacturer or major-retailer sources: Ryzen 9 9950X MPN and specifications; ASUS ProArt X870E-Creator WiFi feature set and M.2 topology; G.Skill Flare X5 128 GB MPN; Noctua NH-D15 G2 variant guidance; Samsung 990 PRO MPNs, performance and TBW; Seasonic VERTEX GX-1200 specifications; RTX 5080 specifications and AIB model names; Synology 2025 drive-compatibility policy and DSM 7.3 reversal.

**⚠️ Not verified — confirm before purchase:** all IDR pricing (volatile; Indonesian GPU pricing moves weekly); APC, Synology, WD/Seagate, Fractal and TP-Link model availability in Indonesia; current DS923+ availability and successor models; RTX 5090 pricing; whether a Zen 6 / AM5 refresh is imminent.

---

## 16. Sources

**Project evidence**
- OpenClaw BIFL P4 Grade Decision and 24-hour addendum (uploaded decision record).
- Tier 1: Ryzen 9 9950X, ProArt X870E, 128 GB, RTX 5080, 2 TB + 4 TB.
- Tier 3: additional archive NVMe, stronger backup, Smart-UPS class protection.
- 24-hour rule: keep gateway, scheduler, memory, logging and cloud escalation available; run heavy local GPU jobs only when justified.

**Official technical sources**
- [AMD Ryzen 9 9950X](https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-9-9950x.html)
- [ASUS ProArt X870E-CREATOR WIFI — tech specs](https://www.asus.com/id/motherboards-components/motherboards/proart/proart-x870e-creator-wifi/techspec/)
- [NVIDIA RTX 5080](https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5080/)
- [Noctua — NH-D15 G2 versions explained](https://noctua.at/en/nh-d15-g2-versions-explained)
- [Noctua NH-D15 G2 LBC — features](https://www.noctua.at/en/products/nh-d15-g2-lbc/features)
- [G.Skill Flare X5 DDR5 AMD EXPO](https://www.gskill.com/products/1/165/396/Flare-X5-DDR5-AMD-EXPO)
- [Samsung 990 PRO — datasheet (PDF)](https://download.semiconductor.samsung.com/resources/data-sheet/samsung_nvme_ssd_990_pro_datasheet_rev.2.0.pdf)
- [Seasonic VERTEX GX ATX 3.1](https://seasonic.com/vertex-gx/)
- [Fractal Meshify 2 XL — support](https://support.fractal-design.com/support/solutions/articles/4000174747-meshify-2-xl)
- [Tom's Hardware — Synology restores third-party drive support in DSM 7.3](https://www.tomshardware.com/pc-components/nas/synology-walks-back-controversial-compatibility-policy-for-2025-nas-units-third-party-hdd-and-ssd-support-returns-with-diskstation-manager-7-3-update)

---

## Final Purchase Line

**AMD Ryzen 9 9950X** + **ASUS ProArt X870E-CREATOR WIFI** + **128 GB QVL-approved 2 × 64 GB DDR5** + **premium RTX 5080 16 GB** + **Samsung 990 PRO 2 TB + 4 TB** + **Seasonic VERTEX GX-1200** + **Noctua NH-D15 G2 LBC** + **Fractal Meshify 2 XL** + **5 × Noctua NF-A14x25 G2** + **APC Smart-UPS 2200 VA** + **Synology DS923+ with 4 × 12 TB CMR** + **two rotating 20 TB offline drives**.

*Third NVMe deferred to trigger (§12). Cooler is the LBC variant (§14.1).*
