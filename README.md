# Bank Jateng Borobudur Marathon (BORMAR) 2026 — Race Analytics Dashboard & Results API

[![Live Demo](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-dc2626?style=for-the-badge&logo=github)](https://gbudidarma.github.io/bormar2026-results-api/)
[![Runners](https://img.shields.io/badge/Runners-12%2C800-09090b?style=for-the-badge)](https://gbudidarma.github.io/bormar2026-results-api/)
[![Total Finishers](https://img.shields.io/badge/Total%20Finishers-11%2C070%20(Incl.%20Black%20Flag)-dc2626?style=for-the-badge)](https://gbudidarma.github.io/bormar2026-results-api/)
[![Black Flag](https://img.shields.io/badge/Finished%20Black%20Flag%20(Medal)-2%2C346-38bdf8?style=for-the-badge)](https://gbudidarma.github.io/bormar2026-results-api/)
[![OpenAPI 3.0](https://img.shields.io/badge/API%20Spec-OpenAPI%203.0-6366f1?style=for-the-badge&logo=openapiinitiative)](openapi.json)
[![Support on Ko-fi](https://img.shields.io/badge/Support-Buy%20Me%20a%20Coffee-ff5e5b?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/V7V2JM8S4)

Complete official race telemetry, interactive HTML analytics dashboard, and OpenAPI 3.0.0 JSON datasets for **Bank Jateng Borobudur Marathon 2026** — covering **12,800 registered runners** and **11,070 total recognized finishers** (**8,724 full-distance finishers** + **2,346 `Finished Black Flag` Marathon runners** who passed **COP 3 @ KM 34.5** before the 09:45 WIB heat halt and earned finisher medals) across all 3 distance categories (**Marathon 42.195K**, **Half Marathon 21.1K**, and **10K**).

🌐 **Live Interactive Dashboard:** **[https://gbudidarma.github.io/bormar2026-results-api/](https://gbudidarma.github.io/bormar2026-results-api/)**

> **Data Source:** All official race results and checkpoint split timings are sourced from **[https://results.scorenow.co.id](https://results.scorenow.co.id)**
> - **Borobudur Marathon 2026 (`Marathon`, `Half Marathon`, `10K`):** [https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340](https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340)

---

## 🏴 Official Race Notice: Cut-Off Points (COP 1–3) & Full Marathon Black Flag Halt (09:45 WIB)

The **Bank Jateng Borobudur Marathon 2026 (42.195K Full Marathon)** started at **04:15 WIB** (Waves: W1 `04:15`, W2 `04:20`, W3 `04:25`, and W4 `04:30 WIB`) using the same official race clock (WIB) for every wave, was scheduled to end at **11:00 WIB (6 hours 30 minutes from W4 / 6 hours 45 minutes from 04:15 WIB)**, and was halted early by the **Black Flag at 09:45 WIB** due to dangerously high temperature/WBGT.

### 1. Official Marathon Cut-Off Times (COP) & Medal Calculation (Start: 04:15 WIB)
Cut-off times are based on the official race clock (WIB) starting at `04:15 WIB`. Runners who **passed COP 3 (KM 34.5 / mats KM 34 & KM 35 $\le$ 09:50 WIB)** but did not finish due to the 09:45 WIB Black Flag halt are classified as **`Finished Black Flag` (`2,346` runners — receive finisher medals 🏅)**. Runners who **did not pass COP 1, COP 2, or COP 3** are classified as **`DNF` (`188` runners — shuttle bus back to Race Village)**.

| Cut-Off Point (COP) | Distance (Timing Mat) | Closes At (WIB) | Max Elapsed (From 04:15 / From W4) | Telemetry & Medal Outcome |
| :--- | :---: | :---: | :---: | :--- |
| **COP 1** | **10.0 KM** (`KM 10`) | **`06:05 WIB`** | `1h 50m` (`1h 35m` from W4) | `4` DNF missed COP 1 (`4,439` active runners passed KM 10 $\le$ 06:05 WIB) |
| **COP 2** | **20.0 KM** (`KM 19.6`) | **`07:35 WIB`** | `3h 20m` (`3h 05m` from W4) | `83` DNF at/before COP 2 (`7` stopped at KM 10 + `13` at KM 15 + `63` cut off at KM 19.6) |
| **COP 3 (Medal Gate)** | **34.5 KM** (`KM 34` / `KM 35`) | **`09:50 WIB`** *(Halt @ 09:45)* | `5h 35m` (`5h 20m` from W4) | **🏅 `2,346` Passed COP 3 $\rightarrow$ `Finished Black Flag` (Get Medal)** • ❌ `97` DNF missed COP 3 (`KM 21.1–31.2` + `1` > 09:50 WIB) |
| **FINISH** | **42.195 KM** *(Finish Line)* | **`11:00 WIB`** | `6h 45m` (`6h 30m` from W4) | **🏆 `1,909` Full 42.195K Finishers** (`4,255` total medal recipients = `87.61%`) |

### 2. COP Breakdown: `Finished Black Flag` Medalists (`2,346`) vs. `DNF` (`188`)
In all JSON datasets (`marathon_results.json` and `bormar_all_results.json`) and in the interactive dashboard, all **2,346** non-finishing runners who passed COP 3 ($\le$ `09:50 WIB`) are unified under `"status": "BLACK_FLAG"`, `"remark": "Finished Black Flag"`, and `"class": "Passed COP 3 — Stopped at <last_checkpoint> (Get Medal)"`, while all **188** runners who did not pass COP are marked `"status": "DNF"` and `"remark": "Did Not Pass COP"`:

| Cohort / Pack Position | Last Timing Mat Reached | Course Range | Runners | COP Status & Medal Outcome |
| :--- | :---: | :---: | ---: | :--- |
| **🏅 Passed COP 3 — Front Pack** | **`KM 39.4`** | `~KM 39.4 – KM 41.9` | **`272`** (`11.6%` of BF) | Passed all 3 COPs, stopped < 2.8 KM from finish at 09:45 WIB $\rightarrow$ **`Finished Black Flag` (Get Medal)** |
| **🏅 Passed COP 3 — Main Pack** | **`KM 35`** | `~KM 35.0 – KM 39.4` | **`1,451`** (`61.8%` of BF) | Passed COP 3 (KM 34.5 $\le$ 09:50 WIB) & KM 35 mat before halt (`1,195` raw `QRY` + `256` raw `DNF`) $\rightarrow$ **`Finished Black Flag` (Get Medal)** |
| **🏅 Passed COP 3 — COP 3 Pack** | **`KM 34`** | `~KM 34.0 – KM 35.0` | **`623`** (`26.6%` of BF) | Cleared KM 34 / COP 3 within 09:50 WIB cutoff when halted $\rightarrow$ **`Finished Black Flag` (Get Medal)** |
| **Total `Finished Black Flag` 🏅** | **`KM 34` – `KM 39.4`** | **`~KM 34.0 – KM 41.9`** | **`2,346`** (`100.0%` of BF) | Combined with **`1,909` full 42.195K finishers**, **`4,255` of `4,857` (`87.61%`)** Marathon runners earned finisher medals. |
| **❌ Missed COP 3 @ KM 34.5** | `KM 21.1` – `KM 31.2` (+1 @ `KM 34`) | `~KM 21.1 – KM 34.0` | **`97`** (`51.6%` of DNF) | `13` at KM 21.1 + `7` at KM 26.2 + `28` at KM 28.4 + `48` at KM 31.2 + `1` over 09:50 WIB at KM 34 $\rightarrow$ **`DNF` (No Medal)** |
| **❌ Missed / Cut at COP 2 @ KM 20** | `KM 10` – `KM 19.6` | `~KM 10.0 – KM 20.0` | **`83`** (`44.1%` of DNF) | `7` stopped at KM 10 + `13` at KM 15 + `63` cut off at KM 19.6 (07:35 WIB) $\rightarrow$ **`DNF` (No Medal)** |
| **❌ Missed COP 1 / Early Dropout** | `None` / Early Retirement | `< KM 10` / Early | **`8`** (`4.3%` of DNF) | `4` missed COP 1 (KM 10 @ 06:05 WIB) + `4` early elite dropouts around 06:00 WIB $\rightarrow$ **`DNF` (No Medal)** |

---

## Race Telemetry Summary

| Event | Distance | Total Registered | Full Finishers (`%`) | 🏴🏅 Finished Black Flag (`%`) | Total Finishers Incl. Black Flag (`%`) | DNF — Missed COP (`%`) | DQ (`%`) | DNS (`%`) | Avg Finish Time | Best Finish Time | Avg Pace |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: | :---: |
| **Marathon** | `42.195 KM` | `4,857` | `1,909` (`39.30%`) | **`2,346` (`48.30%`)** | **`4,255` (`87.61%`)** | `188` (`3.87%`) | `24` (`0.49%`) | `390` (`8.03%`) | `04:50:49` | `02:20:23` | `6:54 /km` |
| **Half Marathon** | `21.1 KM` | `4,508` | `4,129` (`91.59%`) | `0` (`0.00%`) | `4,129` (`91.59%`) | `54` (`1.20%`) | `1` (`0.02%`) | `324` (`7.19%`) | `02:51:03` | `01:05:08` | `8:06 /km` |
| **10K** | `10.0 KM` | `3,435` | `2,686` (`78.20%`) | `0` (`0.00%`) | `2,686` (`78.20%`) | `257` (`7.48%`) | `8` (`0.23%`) | `484` (`14.09%`) | `01:28:02` | `00:32:20` | `8:48 /km` |
| **All 3 Events Combined** | **—** | **`12,800`** | **`8,724` (`68.16%`)** | **`2,346` (`18.33%`)** | **`11,070` (`86.48%`)** | **`499` (`3.90%`)** | **`33` (`0.26%`)** | **`1,198` (`9.36%`)** | **—** | **—** | **`8:03 /km`** |

---

## 🚀 Live Interactive Dashboard

Explore the full interactive race analytics, search all 12,800 runners, view podium finishers, inspect checkpoint split times, and analyze Black Flag telemetry:

👉 **[Launch Live Borobudur Marathon 2026 Dashboard (GitHub Pages)](https://gbudidarma.github.io/bormar2026-results-api/)** 👈

### Dashboard Key Features:
- 🎨 **Borobudur Red & Black Theme:** Modern, athletic brand styling calibrated for high contrast and readability in both **Dark Mode** (carbon charcoal `#09090b` + vibrant crimson accents) and **Light Mode**.
- 🔍 **Instant 12,800-Runner Search:** Instant multi-parameter filtering by Name, Bib Number, Country, Gender, Category, and Status.
- 🔗 **Direct ScoreNow Bib Hyperlinks:** Click any runner's Bib Number to open their official certificate and timing page on ScoreNow (`https://results.scorenow.co.id/myresults.aspx?CId=19723&RId=340&EId={eid}&AId={aid}`).
- 🏴 **COP 1–3 & Black Flag (09:45 WIB) Telemetry:** Interactive verification of all **2,346** Marathon runners who passed **COP 3 (KM 34.5 $\le$ 09:50 WIB)** and earned finisher medals (`Finished Black Flag`) vs. **188** `DNF` runners who did not pass COP 1, COP 2, or COP 3.
- 🏆 **Category Winners & Podiums:** 1st, 2nd, and 3rd place podium cards and summary tables for every race category.
- 🇮🇩 **Country & Nationality Insights:** Interactive domestic vs. international joiner pie charts and top foreign country breakdown.
- ⏱️ **Split Details Drawer:** Click any runner row to slide open segment interval split times and course progress.

> **GitHub Pages Deployment:** This repository includes `index.html` (and `dashboard.html`) pre-built with zero runtime dependencies. To activate GitHub Pages:
> 1. Go to repository **Settings** > **Pages**.
> 2. Under **Build and deployment > Source**, select **Deploy from a branch**.
> 3. Select branch **`main`** and folder **`/ (root)`**, then click **Save**.
> 4. Your dashboard will immediately be live at `https://gbudidarma.github.io/bormar2026-results-api/`.

---

## Example Runner Record

### Full 42.195K Marathon Finisher
```json
{
  "event_slug": "marathon",
  "event_name": "Marathon",
  "race_day": "Day 1",
  "position": 1,
  "status": "FINISHED",
  "raw_status": "FINISHED",
  "bib_no": "6",
  "name": "WILSON CHERUIYOT",
  "time": "02:20:23",
  "bruto_time": "02:20:23",
  "netto_time": "02:20:23",
  "category": "TOP 8 OVERALL",
  "gender": "Male",
  "country": "Kenya",
  "class": null,
  "remark": null,
  "last_checkpoint": "KM 39.4",
  "splits": {
    "KM 10": "14:32",
    "KM 15": "16:47",
    "KM 19.6": "16:17",
    "KM 21.1": "4:50",
    "KM 26.2": "16:38",
    "KM 28.4": "7:02",
    "KM 31.2": "9:37",
    "KM 34": "9:00",
    "KM 35": "2:34",
    "KM 39.4": "13:51"
  }
}
```

---

## Status Codes & Remarks
| Status / Remark | Meaning |
| :--- | :--- |
| `FINISHED` | Official full-distance finisher with recorded finish time and `position` rank (`1,909` in Marathon, `4,129` in Half Marathon, `2,686` in 10K) |
| `BLACK_FLAG` (`remark: "Finished Black Flag"`) | Full Marathon runner who **passed all 3 Cut-Off Points (COP 1 @ KM 10 $\le$ 06:05 WIB, COP 2 @ KM 20 $\le$ 07:35 WIB, and COP 3 @ KM 34.5 $\le$ 09:50 WIB — reaching `KM 34`, `KM 35`, or `KM 39.4`)** before the race was halted by **Black Flag at 09:45 WIB** (`2,346` runners — receive finisher medals 🏅) |
| `DNF` (`remark: "Did Not Pass COP"`) | Did Not Finish — did not pass COP 1 (`4`), COP 2 (`83`), or COP 3 (`97`), or dropped out early before the halt (`4`) (`188` runners in Marathon) |
| `DNS` | Did Not Start |
| `DQ` / `DSQ` | Disqualified |

---

## Data Source, Author & Copyright

- **Data Source:** [https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340](https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340)
- **Author & Copyright:** **© 2026 [@gbudidarma](https://www.instagram.com/gbudidarma/) All rights reserved.**

---

## Support & Buy Me a Coffee

If you found this race analytics dashboard, API datasets, or runner telemetry helpful, you can support the project here:

<a href='https://ko-fi.com/V7V2JM8S4' target='_blank'><img height='36' style='border:0px;height:36px;' src='https://storage.ko-fi.com/cdn/kofi5.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' /></a>
