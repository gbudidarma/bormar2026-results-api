# Bank Jateng Borobudur Marathon (BORMAR) 2026 — Race Analytics Dashboard & Results API

[![Live Demo](https://img.shields.io/badge/Live%20Dashboard-GitHub%20Pages-dc2626?style=for-the-badge&logo=github)](https://gbudidarma.github.io/bormar2026-results-api/)
[![Runners](https://img.shields.io/badge/Runners-12%2C800-09090b?style=for-the-badge)](https://gbudidarma.github.io/bormar2026-results-api/)
[![Total Finishers](https://img.shields.io/badge/Total%20Finishers-11%2C144%20(Incl.%20Black%20Flag)-dc2626?style=for-the-badge)](https://gbudidarma.github.io/bormar2026-results-api/)
[![Black Flag](https://img.shields.io/badge/Finished%20Black%20Flag-2%2C420-38bdf8?style=for-the-badge)](https://gbudidarma.github.io/bormar2026-results-api/)
[![OpenAPI 3.0](https://img.shields.io/badge/API%20Spec-OpenAPI%203.0-6366f1?style=for-the-badge&logo=openapiinitiative)](openapi.json)
[![Support on Ko-fi](https://img.shields.io/badge/Support-Buy%20Me%20a%20Coffee-ff5e5b?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/V7V2JM8S4)

Complete official race telemetry, interactive HTML analytics dashboard, and OpenAPI 3.0.0 JSON datasets for **Bank Jateng Borobudur Marathon 2026** — covering **12,800 registered runners** and **11,144 total recognized finishers** (**8,724 full-distance finishers** + **2,420 `Finished Black Flag` Marathon runners** halted on course at 09:45 WIB due to extreme heat/WBGT) across all 3 distance categories (**Marathon 42.195K**, **Half Marathon 21.1K**, and **10K**).

🌐 **Live Interactive Dashboard:** **[https://gbudidarma.github.io/bormar2026-results-api/](https://gbudidarma.github.io/bormar2026-results-api/)**

> **Data Source:** All official race results and checkpoint split timings are sourced from **[https://results.scorenow.co.id](https://results.scorenow.co.id)**
> - **Borobudur Marathon 2026 (`Marathon`, `Half Marathon`, `10K`):** [https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340](https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340)

---

## 🏴 Official Race Notice: Full Marathon Black Flag Halt (09:45 WIB)

The **Bank Jateng Borobudur Marathon 2026 (42.195K Full Marathon)** started at **04:15 WIB** (Waves at 04:15, 04:20, 04:25, and 04:30 WIB), was scheduled to end at **11:00 WIB (6 hours 30 minutes Cut-Off Time)**, and was halted early by the **Black Flag at 09:45 WIB** due to dangerously high temperature/WBGT—cutting the race short by **1 hour and 15 minutes** (or up to **1 hour and 30 minutes** for the final starting wave).

### 1. Scheduled Start vs. Black Flag Time
By the time the Black Flag was raised at **09:45 WIB**, the **Half Marathon** (COT 08:50 WIB) and **10K** (COT 07:40 WIB) had already concluded, meaning the halt directly impacted runners still on the Full Marathon course:

| Race Category | Scheduled Flag-Off (Waves) | Official Cut-Off Time (COT) | Actual Black Flag Halt | Time Cut Short |
| :--- | :--- | :--- | :--- | :--- |
| **Marathon (42.195K)** | `04:15 WIB` (Waves: 04:15, 04:20, 04:25, 04:30) | `11:00 WIB` (6 hrs 30 mins) | **`09:45 WIB`** | **1 hr 15 mins** (up to 1 hr 30 mins for Wave 4) |
| **Half Marathon (21.1K)** | `04:55 WIB` (Waves: 04:55–05:10) | `08:50 WIB` (3 hrs 40 mins) | Already finished | — |
| **10K (10.0K)** | `05:40 WIB` (Mass start) | `07:40 WIB` (2 hrs 00 mins) | Already finished | — |

### 2. Where the 2,420 `Finished Black Flag` Runners Were on the Course
In the raw ScoreNow results, the **2,420 Full Marathon runners** who were still actively running on the late course checkpoints within official COT limits when halted at 09:45 WIB were split across two raw ScoreNow codes (`2,092` coded as `QRY` + `328` late-checkpoint runners at `KM 28.4`–`KM 39.4` with elapsed time $\ge$ `03:30:00` coded as `DNF` who reached late checkpoints like KM 35 before the halt). In all JSON datasets (`marathon_results.json` and `bormar_all_results.json`) and in the interactive dashboard, all **2,420** runners are unified under:
- `"status": "BLACK_FLAG"` (with original ScoreNow code preserved in `"raw_status"`)
- `"remark": "Finished Black Flag"`
- `"class": "Stopped at KM <last_checkpoint>"`
- `"last_checkpoint": "<last_checkpoint>"`

| Pack Position on Course at 09:45 WIB | Last Timing Mat Reached | Approximate Course Range | Runners (`%` of Black Flag) | Telemetry Notes |
| :--- | :---: | :---: | ---: | :--- |
| **Front-End of Remaining Pack** | **`KM 39.4`** | `~KM 39.4 – KM 41.9` | **`272`** (`11.2%`) | Pacing right around the 5:30–5:45 finish mark in the final stretch near Borobudur, stopped < 2.8 KM shy of the finish line. |
| **Main Pack on Course** | **`KM 35`** | `~KM 35.0 – KM 40.0` | **`1,451`** (`60.0%`) | Largest group of active Marathon runners on course between KM 35 and KM 40 when the Black Flag was raised (`1,195` raw `QRY` + `256` raw `DNF`). |
| **Back-End Within COT** | **`KM 34`** | `~KM 34.0 – KM 35.0` | **`624`** (`25.8%`) | Pacing within the 6h30m COT limit (~9:14/km max pace) at the 5h15m–5h30m mark passing through KM 34. |
| **Approaching KM 32–34** | **`KM 28.4` / `KM 31.2`** | `~KM 28.4 – KM 33.9` | **`73`** (`3.0%`) | `46` runners past `KM 31.2` + `27` runners past `KM 28.4` actively on course at the 09:45 WIB halt. |
| **Total `Finished Black Flag`** | **All Checkpoints** | **`~KM 28.4 – KM 41.9`** | **`2,420`** (`100.0%`) | Combined with **`1,909` full 42.195K finishers**, **`4,329` of `4,857` (`89.13%`)** Marathon runners finished or were halted by Black Flag (leaving only `114` true early `DNF` runners). |

---

## Race Telemetry Summary

| Event | Distance | Total Registered | Full Finishers (`%`) | 🏴 Finished Black Flag (`%`) | Total Finishers Incl. Black Flag (`%`) | True DNF (`%`) | DQ (`%`) | DNS (`%`) | Avg Finish Time | Best Finish Time | Avg Pace |
| :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :---: | :---: |
| **Marathon** | `42.195 KM` | `4,857` | `1,909` (`39.30%`) | **`2,420` (`49.82%`)** | **`4,329` (`89.13%`)** | `114` (`2.35%`) | `24` (`0.49%`) | `390` (`8.03%`) | `04:50:49` | `02:20:23` | `6:54 /km` |
| **Half Marathon** | `21.1 KM` | `4,508` | `4,129` (`91.59%`) | `0` (`0.00%`) | `4,129` (`91.59%`) | `54` (`1.20%`) | `1` (`0.02%`) | `324` (`7.19%`) | `02:51:03` | `01:05:08` | `8:06 /km` |
| **10K** | `10.0 KM` | `3,435` | `2,686` (`78.20%`) | `0` (`0.00%`) | `2,686` (`78.20%`) | `257` (`7.48%`) | `8` (`0.23%`) | `484` (`14.09%`) | `01:28:02` | `00:32:20` | `8:48 /km` |
| **All 3 Events Combined** | **—** | **`12,800`** | **`8,724` (`68.16%`)** | **`2,420` (`18.91%`)** | **`11,144` (`87.06%`)** | **`425` (`3.32%`)** | **`33` (`0.26%`)** | **`1,198` (`9.36%`)** | **—** | **—** | **`8:03 /km`** |

---

## 🚀 Live Interactive Dashboard

Explore the full interactive race analytics, search all 12,800 runners, view podium finishers, inspect checkpoint split times, and analyze Black Flag telemetry:

👉 **[Launch Live Borobudur Marathon 2026 Dashboard (GitHub Pages)](https://gbudidarma.github.io/bormar2026-results-api/)** 👈

### Dashboard Key Features:
- 🎨 **Borobudur Red & Black Theme:** Modern, athletic brand styling calibrated for high contrast and readability in both **Dark Mode** (carbon charcoal `#09090b` + vibrant crimson accents) and **Light Mode**.
- 🔍 **Instant 12,800-Runner Search:** Instant multi-parameter filtering by Name, Bib Number, Country, Gender, Category, and Status.
- 🔗 **Direct ScoreNow Bib Hyperlinks:** Click any runner's Bib Number to open their official certificate and timing page on ScoreNow (`https://results.scorenow.co.id/myresults.aspx?CId=19723&RId=340&EId={eid}&AId={aid}`).
- 🏴 **Black Flag (09:45 WIB) Telemetry:** Interactive analysis of the 2,420 Marathon runners halted on late checkpoints (`KM 28.4` to `KM 41.9`) within COT limits.
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
| `FINISHED` | Official full-distance finisher with recorded finish time and `position` rank |
| `BLACK_FLAG` (`remark: "Finished Black Flag"`) | Full Marathon runner actively on course (`KM 28.4`–`KM 41.9`) within 6h30m COT when the race was halted by **Black Flag at 09:45 WIB** due to high heat/WBGT (`2,420` runners: `2,092` raw `QRY` + `328` late-checkpoint raw `DNF`) |
| `DNF` | Did Not Finish (stopped at early checkpoints $\le$ `KM 26.2` or dropped out early before the Black Flag halt — `114` runners in Marathon) |
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
