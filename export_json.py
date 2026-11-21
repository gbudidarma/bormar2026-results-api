import csv
import json
import re
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent

EVENTS_CONFIG = [
    {
        "event_slug": "marathon",
        "event_name": "Marathon",
        "race_day": "Day 1",
        "cid": 19723,
        "rid": 340,
        "eid": 1,
        "distance_km": 42.195,
        "csv_file": "marathon_results.csv",
        "json_file": "marathon_results.json",
        "split_columns": [
            "KM 10",
            "KM 15",
            "KM 19.6",
            "KM 21.1",
            "KM 26.2",
            "KM 28.4",
            "KM 31.2",
            "KM 34",
            "KM 35",
            "KM 39.4",
        ],
    },
    {
        "event_slug": "half_marathon",
        "event_name": "Half Marathon",
        "race_day": "Day 1",
        "cid": 19723,
        "rid": 340,
        "eid": 2,
        "distance_km": 21.1,
        "csv_file": "half_marathon_results.csv",
        "json_file": "half_marathon_results.json",
        "split_columns": [
            "KM 4.4",
            "KM 10.5",
            "KM 14.9",
            "KM 17.2",
        ],
    },
    {
        "event_slug": "10k",
        "event_name": "10K",
        "race_day": "Day 1",
        "cid": 19723,
        "rid": 340,
        "eid": 3,
        "distance_km": 10.0,
        "csv_file": "10k_results.csv",
        "json_file": "10k_results.json",
        "split_columns": [
            "KM 3.5",
            "KM 7.9",
        ],
    },
]

# Official Bank Jateng Borobudur Marathon 2026 (42.195 KM) Cut-Off Points (COP)
# Based on official race clock starting at 04:15 WIB:
# - COP 1 (KM 10): Closes at 06:05 WIB (max elapsed 01:50:00 from 04:15 WIB / 1h 35m from W4 04:30 WIB)
# - COP 2 (KM 20 / mat KM 19.6): Closes at 07:35 WIB (max elapsed 03:20:00 from 04:15 WIB / 3h 05m from W4 04:30 WIB)
# - COP 3 (KM 34.5 / mats KM 34 & KM 35): Closes at 09:50 WIB (max elapsed 05:35:00 from 04:15 WIB / 5h 20m from W4 04:30 WIB)
# - FINISH (KM 42.195): Closes at 11:00 WIB (max elapsed 06:45:00 from 04:15 WIB / 6h 30m from W4 04:30 WIB)
# - Actual Black Flag Halt: 09:45 WIB (05:30:00 from 04:15 WIB)
MARATHON_START_CLOCK_SEC = 4 * 3600 + 15 * 60       # 04:15:00 WIB
COP1_CLOSE_CLOCK_SEC = 6 * 3600 + 5 * 60            # 06:05:00 WIB
COP2_CLOSE_CLOCK_SEC = 7 * 3600 + 35 * 60           # 07:35:00 WIB
COP3_CLOSE_CLOCK_SEC = 9 * 3600 + 50 * 60           # 09:50:00 WIB
FINISH_CLOSE_CLOCK_SEC = 11 * 3600                  # 11:00:00 WIB
BLACK_FLAG_MIN_ELAPSED_SEC = 3 * 3600 + 30 * 60     # 03:30:00 (07:45 WIB)
COP3_PASSED_CHECKPOINTS = {"KM 34", "KM 35", "KM 39.4"}


def time_to_sec(t: str | None) -> int | None:
    if not t:
        return None
    parts = [int(x) for x in t.strip().split(":") if x.strip().isdigit()]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return None


def sec_to_hms(s: int | None) -> str | None:
    if s is None or s <= 0:
        return None
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def compute_netto_time(splits: dict, split_cols: list[str], finish_time: str | None) -> str | None:
    clean_cols = [c for c in split_cols if c != "RTW"]
    vals = [time_to_sec(splits.get(c)) for c in clean_cols]
    if not vals or vals[-1] is None:
        return finish_time
    if "FINISH" not in clean_cols and finish_time:
        return finish_time
    if any(v is None for v in vals):
        last_none = max(i for i, v in enumerate(vals) if v is None)
        tail = vals[last_none + 1 :]
        return sec_to_hms(sum(tail)) if tail else finish_time
    return sec_to_hms(sum(vals))


def compute_cum_split_at(splits: dict, split_cols: list[str], target_cp: str) -> int | None:
    """Compute cumulative elapsed split time at a specific checkpoint."""
    if target_cp not in split_cols:
        return None
    idx = split_cols.index(target_cp)
    sub_cols = split_cols[: idx + 1]
    vals = [time_to_sec(splits.get(c)) for c in sub_cols]
    if not vals or vals[-1] is None:
        return None
    if any(v is None for v in vals):
        last_none = max(i for i, v in enumerate(vals) if v is None)
        return sum(vals[last_none + 1 :])
    return sum(vals)


def compute_elapsed_to_last_cp(splits: dict, split_cols: list[str]) -> int:
    """Compute cumulative elapsed time up to the runner's last recorded checkpoint."""
    vals = [time_to_sec(splits.get(c)) for c in split_cols]
    while vals and vals[-1] is None:
        vals.pop()
    if not vals:
        return 0
    if any(v is None for v in vals):
        last_none = max(i for i, v in enumerate(vals) if v is None)
        return sum(vals[last_none + 1 :])
    return sum(vals)


def parse_position_and_status(raw_pos: str, finish_time: str) -> tuple[int | None, str]:
    """Convert raw Pos value ('1', '1,000', 'DNS', 'DNF', 'CUT', 'DQ', 'QRY') into (position_int, status_str)."""
    cleaned = raw_pos.replace(",", "").strip()
    if cleaned.isdigit():
        return int(cleaned), "FINISHED"
    if cleaned in {"DNS", "DNF", "CUT", "DQ", "DSQ", "QRY"}:
        return None, cleaned
    return (None, "FINISHED" if finish_time else "UNKNOWN")


def clean_category(raw_cat: str | None) -> str | None:
    """Strip trailing '1 of 8' / '1 of 1,247' rank text from RaceTec v3 category cells and uppercase."""
    if not raw_cat:
        return None
    cleaned = re.sub(r"\d[\d,]*\s+of\s+\d[\d,]*$", "", raw_cat.strip()).strip()
    return cleaned.upper() if cleaned else None


def get_last_checkpoint(splits: dict, split_cols: list[str]) -> str | None:
    reached = [c for c in split_cols if splits.get(c)]
    return reached[-1] if reached else None


def evaluate_marathon_cop(
    event_slug: str,
    raw_status: str,
    last_cp: str | None,
    splits: dict,
    split_cols: list[str],
) -> tuple[str, str | None, str | None]:
    """
    Evaluate Full Marathon (42.195K) runners against official Cut-Off Points (COP) starting at 04:15 WIB:
    - COP 1 (KM 10): Closes at 06:05 WIB (max elapsed 01:50:00 from 04:15 WIB)
    - COP 2 (KM 20 / mat KM 19.6): Closes at 07:35 WIB (max elapsed 03:20:00 from 04:15 WIB)
    - COP 3 (KM 34.5 / mats KM 34 & KM 35): Closes at 09:50 WIB (max elapsed 05:35:00 from 04:15 WIB)
    - FINISH (KM 42.195): Closes at 11:00 WIB (max elapsed 06:45:00 from 04:15 WIB)
    Runners who passed COP 3 (KM 34 / KM 35 / KM 39.4 within 09:50 WIB) but did not finish due to the
    09:45 WIB Black Flag halt are classified as BLACK_FLAG ('Finished Black Flag', get finisher medals).
    Runners who did not pass COP 1, COP 2, or COP 3 (or dropped out early) are classified as DNF.
    """
    if event_slug != "marathon":
        return raw_status, None, None
    if raw_status == "FINISHED":
        return "FINISHED", None, None
    if raw_status in {"DNS", "DQ", "DSQ"}:
        return raw_status, None, None

    cop1_max = COP1_CLOSE_CLOCK_SEC - MARATHON_START_CLOCK_SEC  # 01:50:00
    cop3_max = COP3_CLOSE_CLOCK_SEC - MARATHON_START_CLOCK_SEC  # 05:35:00

    t10 = compute_cum_split_at(splits, split_cols, "KM 10")
    t34 = compute_cum_split_at(splits, split_cols, "KM 34")
    t35 = compute_cum_split_at(splits, split_cols, "KM 35")
    t39 = compute_cum_split_at(splits, split_cols, "KM 39.4")
    t_last = compute_elapsed_to_last_cp(splits, split_cols)

    if last_cp in COP3_PASSED_CHECKPOINTS:
        t_cop3 = t34 if t34 is not None else (t35 if t35 is not None else t39)
        if t_last < BLACK_FLAG_MIN_ELAPSED_SEC:
            return "DNF", "Did Not Pass COP", f"Early Dropout at {last_cp} (Before 09:45 WIB Halt)"
        if t_cop3 is not None and t_cop3 <= cop3_max:
            return "BLACK_FLAG", "Finished Black Flag", f"Passed COP 3 — Stopped at {last_cp} (Get Medal)"
        return "DNF", "Did Not Pass COP", "Missed COP 3 @ KM 34.5 (Closes 09:50 WIB)"

    if last_cp is None:
        return "DNF", "Did Not Pass COP", "Missed COP 1 @ KM 10 (Closes 06:05 WIB)"
    if last_cp in {"KM 10", "KM 15"}:
        if t10 is not None and t10 > cop1_max:
            return "DNF", "Did Not Pass COP", "Missed COP 1 @ KM 10 (Closes 06:05 WIB)"
        return "DNF", "Did Not Pass COP", f"Missed COP 2 @ KM 20 (Stopped at {last_cp})"
    if last_cp == "KM 19.6":
        return "DNF", "Did Not Pass COP", "Missed COP 2 @ KM 20 (Closes 07:35 WIB)"
    if last_cp in {"KM 21.1", "KM 26.2", "KM 28.4", "KM 31.2"}:
        return "DNF", "Did Not Pass COP", f"Missed COP 3 @ KM 34.5 (Stopped at {last_cp})"
    return "DNF", "Did Not Pass COP", "Did Not Pass COP"


NAME_OVERRIDES = {
    "CUT NOISY": "CUT NOOSY KEUMALA FAJRI",
}


def convert_csv_to_records(cfg: dict) -> list[dict]:
    csv_path = WORKSPACE / cfg["csv_file"]
    records = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_pos = (row.get("Pos") or "").strip()
            finish_time = (row.get("Time") or "").strip() or None
            pos_int, raw_status = parse_position_and_status(raw_pos, finish_time or "")

            splits = {}
            for col in cfg["split_columns"]:
                val = (row.get(col) or "").strip()
                splits[col] = val if val else None

            last_cp = get_last_checkpoint(splits, cfg["split_columns"])
            status, remark, class_val = evaluate_marathon_cop(
                cfg["event_slug"], raw_status, last_cp, splits, cfg["split_columns"]
            )

            netto_time = compute_netto_time(splits, cfg["split_columns"], finish_time) if status == "FINISHED" else None
            bib_no = (row.get("Bib No") or "").strip()
            raw_name = (row.get("Name") or row.get("First Name") or "").strip()
            name = NAME_OVERRIDES.get(raw_name.upper(), raw_name)
            category = clean_category(row.get("Category"))
            aid_raw = (row.get("AId") or "").strip()
            aid_int = int(aid_raw) if aid_raw.isdigit() else None
            result_url = (
                f"https://results.scorenow.co.id/myresults.aspx?CId={cfg['cid']}&RId={cfg['rid']}&EId={cfg['eid']}&AId={aid_int}"
                if aid_int
                else None
            )

            record = {
                "event_slug": cfg["event_slug"],
                "event_name": cfg["event_name"],
                "race_day": cfg["race_day"],
                "position": pos_int,
                "status": status,
                "raw_status": raw_status,
                "bib_no": bib_no,
                "aid": aid_int,
                "result_url": result_url,
                "name": name,
                "time": finish_time,
                "bruto_time": finish_time,
                "netto_time": netto_time,
                "category": category,
                "gender": (row.get("Gender") or "").strip() or None,
                "country": (row.get("Country") or "").strip() or None,
                "class": class_val,
                "remark": remark,
                "last_checkpoint": last_cp,
                "splits": splits,
            }
            records.append(record)
    return records


def build_openapi_spec(event_summaries: list[dict], sample_runner: dict) -> dict:
    event_slugs = [e["event_slug"] for e in event_summaries]
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Borobudur Marathon 2026 Race Results API",
            "description": (
                "Official race results and split timings dataset for Borobudur Marathon 2026, "
                "covering the Marathon (42.195K, including 2,346 'Finished Black Flag' runners who passed COP 3 @ KM 34.5 before the 09:45 WIB halt), "
                "Half Marathon (21.1K), and 10K."
            ),
            "version": "1.0.0",
            "contact": {
                "name": "Borobudur Marathon Results API Support",
            },
        },
        "servers": [
            {
                "url": "https://raw.githubusercontent.com/gbudidarma/bormar2026-results-api/main",
                "description": "GitHub Raw Static JSON Server",
            }
        ],
        "tags": [
            {"name": "Events", "description": "Race events metadata and participant counts"},
            {"name": "Results", "description": "Event race results and split times"},
        ],
        "paths": {
            "/events.json": {
                "get": {
                    "operationId": "listEvents",
                    "tags": ["Events"],
                    "summary": "List all race events and participant counts",
                    "description": "Returns metadata and total participant counts for all 3 Borobudur Marathon 2026 race events.",
                    "responses": {
                        "200": {
                            "description": "List of race events",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "competition": {"type": "string", "example": "Borobudur Marathon 2026"},
                                            "cid": {"type": "integer", "example": 19723},
                                            "rid": {"type": "integer", "example": 340},
                                            "total_events": {"type": "integer", "example": 3},
                                            "total_participants": {"type": "integer", "example": 12800},
                                            "total_finishers": {"type": "integer", "example": 8724},
                                            "total_black_flag_finishers": {"type": "integer", "example": 2420},
                                            "total_finishers_including_black_flag": {"type": "integer", "example": 11144},
                                            "events": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/EventSummary"},
                                            },
                                        },
                                    },
                                    "example": {
                                        "competition": "Borobudur Marathon 2026",
                                        "cid": 19723,
                                        "rid": 340,
                                        "total_events": len(event_summaries),
                                        "total_participants": sum(e["total_participants"] for e in event_summaries),
                                        "total_finishers": sum(e["finishers_count"] for e in event_summaries),
                                        "total_black_flag_finishers": sum(e["black_flag_finishers_count"] for e in event_summaries),
                                        "total_finishers_including_black_flag": sum(e["total_finishers_including_black_flag"] for e in event_summaries),
                                        "events": event_summaries,
                                    },
                                }
                            },
                        }
                    },
                }
            },
            "/{event_slug}_results.json": {
                "get": {
                    "operationId": "getEventResultsBySlug",
                    "tags": ["Results"],
                    "summary": "Get results by event slug",
                    "description": "Fetches the complete results dataset for the selected event slug.",
                    "parameters": [
                        {
                            "name": "event_slug",
                            "in": "path",
                            "required": True,
                            "description": "Event slug identifier",
                            "schema": {
                                "type": "string",
                                "enum": event_slugs,
                                "default": "marathon",
                            },
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Event results dataset",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EventDatasetResponse"},
                                }
                            },
                        }
                    },
                }
            },
            "/marathon_results.json": {
                "get": {
                    "operationId": "getMarathonResults",
                    "tags": ["Results"],
                    "summary": "Get Marathon (42.195K) results",
                    "description": "Returns all 4,857 participant results and split times for the Marathon (including 2,420 'Finished Black Flag' runners).",
                    "responses": {
                        "200": {
                            "description": "Marathon results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EventDatasetResponse"},
                                }
                            },
                        }
                    },
                }
            },
            "/half_marathon_results.json": {
                "get": {
                    "operationId": "getHalfMarathonResults",
                    "tags": ["Results"],
                    "summary": "Get Half Marathon (21.1K) results",
                    "description": "Returns all 4,508 participant results and split times for the Half Marathon.",
                    "responses": {
                        "200": {
                            "description": "Half Marathon results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EventDatasetResponse"},
                                }
                            },
                        }
                    },
                }
            },
            "/10k_results.json": {
                "get": {
                    "operationId": "get10KResults",
                    "tags": ["Results"],
                    "summary": "Get 10K results",
                    "description": "Returns all 3,435 participant results and split times for the 10K.",
                    "responses": {
                        "200": {
                            "description": "10K results",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/EventDatasetResponse"},
                                }
                            },
                        }
                    },
                }
            },
            "/bormar_all_results.json": {
                "get": {
                    "operationId": "getAllBormarResults",
                    "tags": ["Results"],
                    "summary": "Get all 12,800 results across all 3 events",
                    "description": "Returns the complete combined dataset for all 3 Borobudur Marathon 2026 events.",
                    "responses": {
                        "200": {
                            "description": "Combined results dataset",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "competition": {"type": "string", "example": "Borobudur Marathon 2026"},
                                            "cid": {"type": "integer", "example": 19723},
                                            "rid": {"type": "integer", "example": 340},
                                            "total_events": {"type": "integer", "example": 3},
                                            "total_participants": {"type": "integer", "example": 12800},
                                            "events": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/EventSummary"},
                                            },
                                            "results": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/RunnerResult"},
                                            },
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
        "components": {
            "schemas": {
                "EventSummary": {
                    "type": "object",
                    "required": [
                        "event_slug",
                        "event_name",
                        "race_day",
                        "distance_km",
                        "total_participants",
                        "finishers_count",
                        "black_flag_finishers_count",
                        "total_finishers_including_black_flag",
                        "split_checkpoints",
                    ],
                    "properties": {
                        "event_slug": {"type": "string", "example": "marathon"},
                        "event_name": {"type": "string", "example": "Marathon"},
                        "race_day": {"type": "string", "example": "Day 1"},
                        "distance_km": {"type": "number", "format": "float", "example": 42.195},
                        "total_participants": {"type": "integer", "example": 4857},
                        "finishers_count": {"type": "integer", "example": 1909},
                        "black_flag_finishers_count": {"type": "integer", "example": 2420},
                        "total_finishers_including_black_flag": {"type": "integer", "example": 4329},
                        "split_checkpoints": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": ["KM 10", "KM 15", "KM 19.6", "KM 21.1", "KM 26.2", "KM 28.4", "KM 31.2", "KM 34", "KM 35", "KM 39.4"],
                        },
                    },
                },
                "RunnerResult": {
                    "type": "object",
                    "required": ["event_slug", "event_name", "race_day", "status", "bib_no", "name", "splits"],
                    "properties": {
                        "event_slug": {"type": "string", "example": "marathon"},
                        "event_name": {"type": "string", "example": "Marathon"},
                        "race_day": {"type": "string", "example": "Day 1"},
                        "position": {"type": "integer", "nullable": True, "example": 1},
                        "status": {
                            "type": "string",
                            "enum": ["FINISHED", "BLACK_FLAG", "DNS", "DNF", "CUT", "DQ", "DSQ", "QRY", "UNKNOWN"],
                            "example": "FINISHED",
                        },
                        "raw_status": {
                            "type": "string",
                            "enum": ["FINISHED", "DNS", "DNF", "CUT", "DQ", "DSQ", "QRY", "UNKNOWN"],
                            "example": "FINISHED",
                        },
                        "bib_no": {"type": "string", "example": "6"},
                        "name": {"type": "string", "example": "WILSON CHERUIYOT"},
                        "time": {"type": "string", "nullable": True, "example": "02:20:23"},
                        "bruto_time": {"type": "string", "nullable": True, "example": "02:20:23"},
                        "netto_time": {"type": "string", "nullable": True, "example": "02:20:23"},
                        "category": {"type": "string", "nullable": True, "example": "TOP 8 OVERALL"},
                        "gender": {"type": "string", "nullable": True, "example": "Male"},
                        "country": {"type": "string", "nullable": True, "example": "Kenya"},
                        "class": {"type": "string", "nullable": True, "example": "Stopped at KM 35"},
                        "remark": {"type": "string", "nullable": True, "example": "Finished Black Flag"},
                        "last_checkpoint": {"type": "string", "nullable": True, "example": "KM 39.4"},
                        "splits": {
                            "type": "object",
                            "example": sample_runner["splits"],
                        },
                    },
                },
                "EventDatasetResponse": {
                    "type": "object",
                    "required": ["metadata", "results"],
                    "properties": {
                        "metadata": {"$ref": "#/components/schemas/EventSummary"},
                        "results": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/RunnerResult"},
                        },
                    },
                },
            }
        },
    }


def main():
    all_events_summary = []
    all_records = []
    events_payload = {}

    for cfg in EVENTS_CONFIG:
        records = convert_csv_to_records(cfg)
        finishers = sum(1 for r in records if r["status"] == "FINISHED")
        bf_finishers = sum(1 for r in records if r.get("remark") == "Finished Black Flag")
        summary = {
            "event_slug": cfg["event_slug"],
            "event_name": cfg["event_name"],
            "race_day": cfg["race_day"],
            "distance_km": cfg["distance_km"],
            "total_participants": len(records),
            "finishers_count": finishers,
            "black_flag_finishers_count": bf_finishers,
            "total_finishers_including_black_flag": finishers + bf_finishers,
            "split_checkpoints": cfg["split_columns"],
        }
        all_events_summary.append(summary)
        all_records.extend(records)
        events_payload[cfg["event_slug"]] = {
            "metadata": summary,
            "results": records,
        }

        out_json = WORKSPACE / cfg["json_file"]
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(events_payload[cfg["event_slug"]], f, ensure_ascii=False, indent=2)
        print(
            f"Created {out_json.name} ({len(records)} records, {finishers} full finishers, "
            f"{bf_finishers} Finished Black Flag)"
        )

    total_fin = sum(e["finishers_count"] for e in all_events_summary)
    total_bf = sum(e["black_flag_finishers_count"] for e in all_events_summary)

    # Write events summary JSON
    events_summary_path = WORKSPACE / "events.json"
    events_summary_data = {
        "competition": "Borobudur Marathon 2026",
        "cid": 19723,
        "rid": 340,
        "total_events": len(all_events_summary),
        "total_participants": len(all_records),
        "total_finishers": total_fin,
        "total_black_flag_finishers": total_bf,
        "total_finishers_including_black_flag": total_fin + total_bf,
        "events": all_events_summary,
    }
    with open(events_summary_path, "w", encoding="utf-8") as f:
        json.dump(events_summary_data, f, ensure_ascii=False, indent=2)
    print(f"Created {events_summary_path.name} (summary of {len(all_events_summary)} events)")

    # Write combined JSON dataset
    combined_path = WORKSPACE / "bormar_all_results.json"
    combined_data = {
        **events_summary_data,
        "results": all_records,
    }
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=2)
    print(f"Created {combined_path.name} ({len(all_records)} total records)")

    sample_runner = events_payload["marathon"]["results"][0]
    openapi_spec = build_openapi_spec(all_events_summary, sample_runner)
    openapi_path = WORKSPACE / "openapi.json"
    with open(openapi_path, "w", encoding="utf-8") as f:
        json.dump(openapi_spec, f, ensure_ascii=False, indent=2)
    print(f"Created {openapi_path.name} (OpenAPI 3.0.0 specification)")


if __name__ == "__main__":
    main()
