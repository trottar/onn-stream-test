---
memory_schema: 1
as_of: 2026-10-15
status: E6-R1 — the alpha hardware shortlist, from the E4 close-out's floors and this evening's web research (Cowork, not Code; prices and stock as seen 2026-10-15, US retail; nothing measured). Selection itself waits for E5-S2 (the probe and the E1 rows on a candidate)
---

# E6-R1 — candidate shortlist for the alpha host

**What the host must carry** (`E4_CLOSEOUT_2026-10-15.md` §3): ≥ 6 cores
of the 4650G's per-core speed class (≥ 4 with grab deferral), 1.5 GB
for the stack without swap (1.25 GB with deferral), 8 GB system, VAAPI
H.264 encode at 720p60 on a driver the companion has run on
(`radeonsi` is the only one measured), wired Ethernet. The reference
itself is an HP EliteDesk with a Ryzen 5 PRO 4650G, idle 5.3 W at the
socket sensor (not the wall).

**ROADMAP §E6's rule:** "do not select the absolute cheapest machine
merely because it has a superficially similar benchmark score." Every
figure below is a retailer's or a reviewer's, dated today; none is ours.

## 1. The shortlist

| # | candidate | CPU / iGPU | why it fits | price seen (2026-10-15) | idle (reviewer, wall) | caveats |
| --- | --- | --- | --- | --- | --- | --- |
| **A** | **Lenovo ThinkCentre M75q Gen 2 Tiny**, refurbished | Ryzen 5 PRO 5650GE, 6C/12T Zen 3, 35 W; Vega 7 (same VCN generation and `radeonsi` driver family as the reference) | the closest thing to the reference in a 1-litre box: six cores a step *faster* per core than the 4650G (Zen 3 vs Zen 2), the same AMD VAAPI path, 16 GB, NVMe, wired GbE; the best-documented Linux Tiny there is | **$367** Best Buy refurbished "Excellent", 16 GB / 256 GB, 90-day warranty; eBay/other refurbishers list 8-32 GB variants (Newegg, DeluxePCs, Swing) | ~12 W (ServeTheHome, same chassis with a 4750GE) | 35 W GE part: sustained all-core clocks below the 65 W 4650G's — the "speed class" claim needs E5-S2's PS1-STREAM/CONC rows, not a benchmark; withdrawn model, refurbished only |
| **B** | **HP EliteDesk / Elite Mini 805 G8**, refurbished or used | Ryzen 5 PRO 5650GE, as A | the direct successor of the reference's own family (an HP 805-series with the 4650G); identical firmware/BIOS habits to what the project already runs | **$400** eBay used, 16 GB / 256 GB (store seller, 30-day returns); **$730** Newegg refurbished 16 GB / 512 GB; Best Buy and Newegg also list it new at 8 GB | not found for this exact unit; same 35 W class as A, expect ~10-12 W | pricier than A for the same silicon; new 8 GB configs sit exactly on the 8 GB line |
| **C** | **Beelink SER5 (5560U)**, new | Ryzen 5 5560U, 6C/12T Zen 3, 15-25 W; Vega 6 | the cheap new-build with the right core count and the AMD VAAPI path; the one to try if the user wants new, not refurbished | **$230** (Notebookcheck's review price); **$341** DROIX 16 GB / 1 TB — *out of stock* there today | not published in the sources read | a 15 W sustained limit: six cores that are not the 4650G's speed class under a sustained stream + grab; vendor firmware/fan-curve quality on Linux is the usual SER5 complaint; this is exactly the "similar benchmark score" trap unless E5-S2 measures it |
| **D** | **Dell OptiPlex 3000 / 7000 Micro**, refurbished | Core i5-12500T, 6 P-cores/12T, 35 W; UHD 770 (Quick Sync, VAAPI via `iHD`) | the cross-vendor control: six fast cores, the lowest idle in the class (5.5-6.5 W wall measured by ServeTheHome on a 7000 Micro with an i7-12700), excellent Linux support, very good H.264 encode | **$450** PCLiquidations, OptiPlex 3000 Micro Grade C, 8 GB / 256 GB, 1-year warranty, "only 1 left"; the 7000 Micro by quote | 5.5-6.5 W (STH, i7-12700 unit) | **a different VA driver** (`iHD`, not `radeonsi`): the companion's encoder command has never run on it; E5-S1's model says `unknown` until measured; 8 GB as sold (expandable) |
| — | Minisforum UM760 Slim (7640HS, Zen 4, Radeon 760M) | — | more than the alpha needs; a better encoder (VCN 4) | $623 Minisforum, **sold out**; Best Buy no longer stocks it | — | out of stock, out of price class; keep for the "optional higher tier" question only |
| — | Intel N100 / N305 boxes | 4 / 8 Gracemont cores | — | ~$130-300 | ~10 W (CNX, Weibu N305 on Ubuntu) | **not a candidate**: the cores are roughly half the 4650G's per-core speed, so eight of them do not make "6 of this speed class"; idle is no better than A; H.264 encode exists but the whole CPU-time floor would have to be re-measured on it |

## 2. Reading

- **Pick A as the primary candidate, B as the fallback for the same
  silicon.** They satisfy every line of the alpha on paper, cost
  $370-400 refurbished, and keep the project on the one VA driver it has
  measured. The only open question is whether a 35 W GE part holds the
  4650G's per-core speed under CONC — E5-S2 answers that in one
  evening (the probe, then PS1-STREAM and CONC from the E1 suite).
- **C** is the new-build option if refurbished is unwanted; it must be
  measured before it is believed, and the 15 W limit is the risk.
- **D** is worth one unit only if the user wants to know whether Intel
  Quick Sync is a viable second path (it would widen E6's choices a lot);
  otherwise it adds a driver the project has not validated.
- **Idle power cannot be compared yet:** the reference's 5.3 W is a
  socket sensor, the reviewers' figures are wall watts. E5-S2 should put
  a wall meter on the reference and the candidate in the same evening.
- Prices move daily; the refurbished Tiny market (eBay, Newegg
  refurbishers, Best Buy outlet) is deep for the 5650GE, so availability
  is not a risk for A or B.

## 3. Next (E5-S2 / E6-R2)

1. The user picks A (or B) and buys one — the user's purchase, not
   Code's, not Cowork's.
2. E5-S2 on it: `tools/capability_probe.py`, then the E1 rows
   PS1-STREAM, SNES-STREAM, META, CONC with E4-S2's pass rule, a wall
   meter on both machines; the capability model's "speed class"
   threshold gets its first second data point.
3. E6-R2: the selection, from that evidence, against §E6's eight
   criteria.

## Sources

- [Best Buy — Lenovo ThinkCentre M75q G2 Micro, 5650GE, refurbished](https://www.bestbuy.com/product/lenovo-thinkcentre-m75q-g2-micro-amd-ryzen-5-pro-5650ge-16gb256gb-w11p-black/JXRKGP5HGS)
- [Newegg — M75q Gen 2 Tiny 5650GE refurbished](https://www.newegg.com/p/1VK-0003-1SS84) · [DeluxePCs](https://deluxepcs.com/products/m75qg2-5650ge-16-1tbn-wf-1p) · [Swing Computers](https://www.swingcomputers.com/products/lenovo-thinkcentre-m75q-gen-2-tiny-ryzen-5-pro-5650ge-8gb-ram-256gb-nvme-4)
- [ServeTheHome — M75q Tiny Gen2 35 W Ryzen 5000 review, power page](https://www.servethehome.com/lenovo-thinkcentre-m75q-tiny-gen2-35w-amd-ryzen-5000-powerhouse/5/) · [M75q Gen2 (4750GE) review, power page](https://www.servethehome.com/lenovo-thinkcentre-m75q-gen2-tiny-review-amd-changes-the-game/4/)
- [eBay — HP EliteDesk 805 G8 Mini 5650GE 16/256, used](https://www.ebay.com/itm/147545348547) · [Newegg — 805 G8 Mini refurbished 16/512](https://www.newegg.com/p/1VK-001E-4V4F2) · [Best Buy — HP Elite Mini 805 G8 new](https://www.bestbuy.com/product/hp-elite-mini-805-g8-amd-ryzen-5-pro-5650ge-16gb-256gb-ssd-windows-11-pro-black/JJG9TKW353)
- [Notebookcheck — Beelink SER5 (5560U) review](https://www.notebookcheck.net/Ryzen-5-5560U-performance-debut-Beelink-SER5-mini-PC-review.762934.0.html) · [DROIX — Beelink SER5](https://droix.net/product/beelink-ser5/)
- [PCLiquidations — OptiPlex 3000 Micro i5-12500T](https://www.pcliquidations.com/dell-optiplex-3000-micro/p/162884) · [OptiPlex 7000 Micro i5-12500T](https://www.pcliquidations.com/dell-optiplex-7000-micro/p/162042) · [ServeTheHome — OptiPlex 7000 Micro review, power page](https://www.servethehome.com/dell-optiplex-7000-intel-alder-lake-tinyminimicro-pc-review/4/)
- [Minisforum — UM760 Slim](https://store.minisforum.com/products/minisforum-um760-slim-mini-pc) · [Best Buy — UM760 Slim](https://www.bestbuy.com/product/minisforum-um760-slim-mini-pc-amd-ryzen-5-7640hs-16gb-memory-1tb-ssd-black/CGCLRV3GYF/sku/10146603)
- [CNX Software — Weibu N10 (i3-N305) review, Ubuntu power](https://www.cnx-software.com/2023/03/18/intel-core-i3-n305-mini-pc-review-windows-11-ubuntu-22-04/)
