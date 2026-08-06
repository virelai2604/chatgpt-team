# AI Workstation Build Specification

**Purpose:** Local/hybrid AI development workstation — OpenClaw runtime, WSL2, Ollama, embeddings, OCR, transcription, RAG indexing, containerised services.
**Target market:** Indonesia (Jakarta). Prices in IDR, planning estimates only.
**Document status:** Part numbers verified against manufacturer/retailer sources where marked ✅. Prices are volatile and must be re-checked at purchase.

---

## 1. The decision that drives the build

The GPU choice is not a spec-sheet question — it determines what the machine is for. Pick one path before buying anything.

| | **Path A — Cloud-primary** | **Path B — Local-primary** |
|---|---|---|
| Heavy inference runs on | Cloud APIs (OpenAI / Anthropic) | This machine |
| GPU role | Embeddings, OCR, Whisper, small models | Primary inference, 27–32B class |
| GPU | RTX 5060 Ti 16 GB | RTX 5090 32 GB |
| VRAM ceiling | 16 GB | 32 GB |
| Est. total | **Rp 60–72 juta** | **Rp 115–135 juta** |

**Why not RTX 5080:** at Rp 27–32 juta it is too expensive for a support role and too VRAM-limited (16 GB) to be the primary inference engine. It occupies the weakest position between the two coherent options. If local inference is a *fallback*, Path A's card does the same supporting work for roughly a third of the price. If local inference is *the point*, only 32 GB changes which model classes actually fit.

**Recommendation: Path A.** The documented project gaps — persistent memory, marketplace APIs, revenue-linked automation — are software, not hardware. Path A funds the same CPU/RAM/storage capability while leaving ~Rp 50 juta uncommitted until logs prove a VRAM ceiling is actually being hit.

---

## 2. Core platform — identical in both paths

### CPU

| Field | Value |
|---|---|
| Part | AMD Ryzen 9 9950X |
| **MPN** | **100-100001277WOF** ✅ |
| Architecture | Zen 5 "Granite Ridge", TSMC 4 nm |
| Cores / threads | 16C / 32T |
| Clocks | 4.3 GHz base / 5.7 GHz boost |
| TDP | 170 W (≈230 W PPT) |
| Cache | 80 MB total (64 MB L3 + 16 MB L2) |
| Socket | AM5 |
| Cooler included | No — "WOF" = without fan |
| Planning price | Rp 10.5–12.5 juta |

Choose the 9950X over the 9950X3D unless gaming is a major secondary workload. Parallel throughput for indexing, OCR, WSL, containers and concurrent agents scales with cores, not 3D V-Cache.

### CPU cooler

| Field | Value |
|---|---|
| Part | **Noctua NH-D15 G2 LBC** ✅ |
| Variant | **LBC (Low Base Convexity) — this is the AM5-correct variant** |
| Planning price | Rp 2.3–3.0 juta |

> **Important:** Noctua ships three base-convexity variants. LBC is specified for AM5's relatively flat IHS and delivers the best contact quality on this socket — including the lowest simultaneous CCD and IOD temperatures. The **standard** (medium convexity) and **HBC** (high convexity, for de-shaped Intel 12th–14th gen under high ILM pressure) variants are the wrong choice here. The variant is engraved on the base — verify on receipt.

Run a modest PPT limit or Eco Mode rather than chasing peak boost. The performance loss is smaller than the reduction in heat, noise and sustained electrical stress.

### Motherboard

| Field | Value |
|---|---|
| Part | **ASUS ProArt X870E-CREATOR WIFI** ✅ |
| Chipset | AMD X870E, socket AM5 |
| Form factor | ATX |
| VRM | 16+2+2 power stages |
| M.2 slots | **4 total** — M.2_1 & M.2_2 PCIe 5.0 x4 (up to 128 Gbps); M.2_3 & M.2_4 PCIe 4.0 |
| Networking | 10 GbE + 2.5 GbE, Wi-Fi 7 |
| USB4 | 2 × 40 Gbps Type-C |
| Other USB | 1 × 20 Gbps Type-C, 7 × 10 Gbps Type-A, 1 × USB 2.0; front 20 Gbps header with 30 W PD 3.0 |
| Memory | DDR5, up to 256 GB |
| Planning price | Rp 8.5–11.0 juta |

> **Lane caveat:** M.2_2 shares bandwidth with the second PCIe 5.0 x16 slot. Irrelevant with a single GPU; blocking if a second accelerator or high-bandwidth PCIe card is added later. Plan drive placement accordingly.

The four M.2 slots are what justify this board over cheaper X870E options — they are the reason the storage tiering below is possible without add-in cards.

### Memory

| Field | Value |
|---|---|
| Part | G.Skill Flare X5 128 GB (2 × 64 GB) DDR5-6000 |
| **MPN** | **F5-6000J3244G64GX2-FX5** ✅ |
| Timings | CL32-44-44-96 |
| Voltage | 1.40 V |
| Profile | AMD EXPO |
| Type | U-DIMM, non-ECC, non-RGB |
| Planning price | Rp 7.5–11.0 juta |

**Two DIMMs, not four.** Dual-rank 64 GB modules load the AM5 memory controller heavily; two sticks give materially better stability and preserve an upgrade path to 192/256 GB.

**Expect to run below rated speed.** 2 × 64 GB dual-rank at DDR5-6000 is optimistic on AM5. Budget for DDR5-5600 as the realistic stable operating point. A stable 5600 configuration beats an unstable 6000 configuration in every way that matters for a machine meant to run unattended jobs.

**Mandatory:** confirm the exact kit appears on the ASUS ProArt X870E-Creator QVL before purchase.

---

## 3. GPU — path-dependent

### Path A (recommended) — RTX 5060 Ti 16 GB

| Field | Value |
|---|---|
| VRAM | 16 GB GDDR7 |
| TGP | ~180 W |
| Candidate models | ASUS PRIME / TUF, MSI Ventus 3X, Gigabyte Gaming OC |
| Planning price | Rp 8–11 juta |
| Verification | ⚠️ Indicative — confirm exact SKU and Indonesian warranty at purchase |

Sufficient for embeddings, OCR acceleration, Whisper transcription, image generation and small quantised models. Same 16 GB VRAM as the 5080 at roughly a third of the cost.

### Path B — RTX 5090 32 GB

| Field | Value |
|---|---|
| VRAM | 32 GB GDDR7 |
| TGP | 575 W |
| Planning price | Rp 45–60 juta |
| Verification | ⚠️ Specs from vendor documentation — confirm at purchase |

The only configuration that meaningfully raises the local model ceiling. Requires the 1200 W PSU below.

### Reference — RTX 5080 16 GB (not recommended, documented for comparison)

| Field | Value |
|---|---|
| CUDA cores | 10,752 ✅ |
| VRAM | 16 GB GDDR7, 256-bit ✅ |
| Bandwidth | 960 GB/s ✅ |
| Tensor cores | 5th generation (Blackwell) ✅ |
| TGP | 360 W ✅ |
| Models | ASUS `TUF-RTX5080-O16G-GAMING` ✅, MSI RTX 5080 16G Gaming Trio OC ✅, Gigabyte AORUS RTX 5080 MASTER ICE 16G ✅ |
| Planning price | Rp 27–32 juta |

---

## 4. Storage

| Slot | Part | MPN | Capacity | Role |
|---|---|---|---|---|
| M.2_1 (PCIe 5.0) | Samsung 990 PRO | **MZ-V9P2T0BW** ✅ | 2 TB | OS + execution |
| M.2_3 (PCIe 4.0) | Samsung 990 PRO | **MZ-V9P4T0BW** ✅ | 4 TB | Active AI/data |
| — | *(archive moved off NVMe — see below)* | | | |

**Samsung 990 PRO shared specs** ✅ — PCIe 4.0 x4, NVMe 2.0, M.2 2280, up to 7,450 MB/s read / 6,900 MB/s write, V-NAND 3-bit MLC, AES-256 hardware encryption, TCG Opal 2.0.
**Endurance:** 2 TB = 1,200 TBW · 4 TB = 2,400 TBW ✅

### Change from the original plan: drop the third NVMe

The original specification called for a 4 TB Gen4 NVMe (Rp 4.5–7.5 juta) for archive and staging. That role is defined as completed outputs, download staging, superseded models, snapshots and rebuildable caches — **none of it performance-sensitive**, and the same document correctly notes it is not a backup.

Replace with a **12–16 TB CMR HDD** (WD Red Pro / Seagate IronWolf Pro class, Rp 4–6 juta) or NAS capacity. Same job, roughly 3× the space, and it frees an M.2 slot.

### Storage map

```
SSD 1 — 2 TB NVMe — SYSTEM
  C:\Windows, C:\Applications
  WSL2 VHDX, /home/<user>
  Docker metadata, active repos, .venv
  Keep 20–25% free

SSD 2 — 4 TB NVMe — AI ACTIVE
  AI-Core/models          (Ollama)
  AI-Core/datasets
  AI-Core/normalized      (OCR output, transcripts)
  AI-Core/databases       (SQLite, DuckDB)
  AI-Core/indexes         (Chroma)
  AI-Core/outputs/current

HDD / NAS — ARCHIVE + STAGING
  AI-Core/archive
  AI-Core/exports
  AI-Core/snapshots
  AI-Core/incoming
  AI-Core/rebuildable-cache
```

> **Never** place actively-written SQLite databases or WSL virtual disks on a USB HDD or network share.

### Backup — 3-2-1

| Copy | Medium |
|---|---|
| 1 | Active NVMe |
| 2 | NAS or external HDD |
| 3 | Second rotating external HDD, or encrypted off-site/cloud |

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

## 5. Power, cooling, chassis

### PSU

| Path | Unit | Rating | Rationale |
|---|---|---|---|
| **A** | Seasonic Vertex GX-850 or GX-1000 | 850–1000 W | System peaks ≈ 450–500 W with a 180 W GPU |
| **B** | **Seasonic Vertex GX-1200** ✅ | 1200 W | Required headroom for the 575 W RTX 5090 |

**Vertex GX-1200 specs** ✅ — 1200 W, 80 PLUS Gold, ATX 3.1 / PCIe 5.1, fully modular, native 12V-2×6 cable, 135 mm fluid-dynamic-bearing fan, OPP/OVP/UVP/SCP/OCP/OTP, **12-year warranty**.

> A 1200 W unit is *only* justified by Path B. On Path A it is capacity you will never draw. Note that early Vertex units shipped with 12VHPWR cables before the ATX update to 12V-2×6 — confirm which cable is in the box.

### Case

Fractal Design Meshify 2 XL, Corsair 5000D Airflow, or equivalent high-airflow ATX chassis. Rp 3.0–5.0 juta.
Front intake / rear + top exhaust. Verify GPU length, thickness and power-cable bend radius against the exact card SKU.

### Fans

3–5 premium 140 mm PWM. Rp 1.5–2.8 juta.

### UPS

Pure sine-wave, 1500–2200 VA. APC Smart-UPS (SMT1500I / SMT2200I) or Eaton 5S/5SC class. Rp 5–14 juta. ⚠️ Model numbers indicative.

> **Size on watts, not VA.** A 1500 VA unit typically delivers ~900–1000 W. Confirm the real wattage sustains tower plus networking equipment for the runtime you need.

---

## 6. Software stack

| Layer | Selection |
|---|---|
| Host OS | Windows 11 Pro |
| Linux layer | WSL2 — Ubuntu 24.04 LTS |
| Runtimes | Node.js, Python (uv + per-project `.venv`), Git, Docker where useful |
| Agent stack | OpenClaw, Codex CLI, Ollama, cloud API path |
| Data | Raw files + SHA-256 manifests, SQLite/FTS5, CSV/JSONL, Markdown/JSON, Chroma, DuckDB + Parquet |
| Later | Neo4j, NAS services, central monitoring |

---

## 7. Pre-purchase checklist

- [ ] Exact RAM kit (`F5-6000J3244G64GX2-FX5`) appears on the ASUS ProArt X870E-Creator QVL
- [ ] Cooler is the **LBC** variant — verify engraving on the base
- [ ] Cooler clears RAM height and case side panel
- [ ] Case fits the exact GPU SKU: length, thickness, cable bend radius
- [ ] PSU ships with a **native 12V-2×6** cable — no adapter daisy-chains
- [ ] Motherboard BIOS revision supports the shipped CPU stepping (BIOS FlashBack available if not)
- [ ] Both NVMe drives sit under motherboard heatsink coverage
- [ ] Drive roles assigned correctly at OS install — Windows and WSL must not land on the archive volume
- [ ] UPS **wattage** (not VA) sustains tower + networking
- [ ] GPU carries official Indonesian warranty, not grey-market
- [ ] Assembly includes memory stability testing and sustained CPU/GPU load testing
- [ ] Verify whether a Zen 6 / next-gen AM5 refresh is imminent before paying full price for the current flagship

---

## 8. Budget summary

| Scope | Path A | Path B |
|---|---|---|
| Tower only | Rp 48–58 juta | Rp 95–112 juta |
| + UPS | Rp 55–70 juta | Rp 102–125 juta |
| + backup layer | Rp 60–72 juta | Rp 115–135 juta |

---

## 9. Verification status

**✅ Verified** against manufacturer or major-retailer listings: Ryzen 9 9950X MPN and specifications; ASUS ProArt X870E-Creator WiFi feature set; G.Skill Flare X5 128 GB MPN; Noctua NH-D15 G2 variant guidance; Samsung 990 PRO MPNs, performance and TBW; Seasonic Vertex GX-1200 specifications; RTX 5080 specifications and AIB model names.

**⚠️ Not verified — confirm before purchase:** all IDR prices (volatile, and GPU pricing in Indonesia moves week to week); RTX 5060 Ti and RTX 5090 exact SKUs; UPS model numbers; case and fan selections; current retailer stock.

---

## Sources

- [AMD Ryzen 9 9950X — official product page](https://www.amd.com/en/products/processors/desktops/ryzen/9000-series/amd-ryzen-9-9950x.html)
- [ASUS ProArt X870E-CREATOR WIFI — tech specs](https://www.asus.com/us/motherboards-components/motherboards/proart/proart-x870e-creator-wifi/techspec/)
- [Noctua — NH-D15 G2 versions explained](https://noctua.at/en/nh-d15-g2-versions-explained)
- [Noctua NH-D15 G2 LBC — features](https://www.noctua.at/en/products/nh-d15-g2-lbc/features)
- [G.Skill Flare X5 DDR5 AMD EXPO series](https://www.gskill.com/products/1/165/396/Flare-X5-DDR5-AMD-EXPO)
- [Samsung 990 PRO — datasheet (PDF)](https://download.semiconductor.samsung.com/resources/data-sheet/samsung_nvme_ssd_990_pro_datasheet_rev.2.0.pdf)
- [Seasonic VERTEX GX ATX 3.1](https://seasonic.com/vertex-gx/)
- [ASUS TUF Gaming RTX 5080 16GB — tech specs](https://www.asus.com/us/motherboards-components/graphics-cards/tuf-gaming/tuf-rtx5080-16g-gaming/techspec/)
