# Bank Jateng Borobudur Marathon 2026 Race Results & Split Times API

Access the complete official race results, rankings, athlete profiles, and checkpoint split times from **Bank Jateng Borobudur Marathon 2026** — covering **12,800 participants** and **11,144 total recognized finishers** (including **2,420 `Finished Black Flag` Marathon runners** halted at 09:45 WIB) across 3 major distance categories:

- **Marathon (42.195 KM)** — `4,857` participants (`1,909` full-distance finishers + `2,420` `Finished Black Flag` = `4,329` total finishers / `89.13%`)
- **Half Marathon (21.1 KM)** — `4,508` participants (`4,129` finishers / `91.59%`)
- **10K (10.0 KM)** — `3,435` participants (`2,686` finishers / `78.20%`)

---

## Key Features
- **`Finished Black Flag` Telemetry (09:45 WIB Early Halt):** Explicitly identifies all `2,420` Full Marathon runners who were actively running on the late course checkpoints within the 6h30m Cut-Off Time when the Black Flag was raised at 09:45 WIB (`"status": "BLACK_FLAG"`, `"remark": "Finished Black Flag"`, `"class": "Stopped at KM 39.4" / "Stopped at KM 35" / "Stopped at KM 34"`, `"last_checkpoint"`).
- **Complete Participant Coverage:** Includes all official finishers, `Finished Black Flag` runners, and non-finisher statuses (`DNS`, `DNF`, `DQ`).
- **Detailed Checkpoint Splits:** Every event includes intermediate timing mat splits (`KM 10`, `KM 15`, `KM 19.6`, `KM 21.1`, `KM 26.2`, `KM 28.4`, `KM 31.2`, `KM 34`, `KM 35`, `KM 39.4` for Marathon; `KM 4.4`, `KM 10.5`, `KM 14.9`, `KM 17.2` for Half Marathon; `KM 3.5`, `KM 7.9` for 10K).

---

## Available Endpoints

| Method | Endpoint | Description | Records |
| :--- | :--- | :--- | ---: |
| `GET` | `/events.json` | Summary of all 3 race events, distances, full finishers, Black Flag finishers, and checkpoint lists | 3 events |
| `GET` | `/{event_slug}_results.json` | Fetch results by event slug (`marathon`, `half_marathon`, `10k`) | Varies |
| `GET` | `/marathon_results.json` | Full Marathon (42.195K) results (`1,909` full + `2,420` `Finished Black Flag`) & 10 split checkpoints | 4,857 |
| `GET` | `/half_marathon_results.json` | Half Marathon (21.1K) results & 4 split checkpoints | 4,508 |
| `GET` | `/10k_results.json` | 10K race results & split checkpoints | 3,435 |
| `GET` | `/bormar_all_results.json` | Complete combined dataset across all 3 events | 12,800 |
