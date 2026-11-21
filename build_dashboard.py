import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
ARTIFACT_PATH = Path(
    "/Users/gbudidarma/.gemini/antigravity/brain/aad5b712-7802-49b0-832a-dcc88605f985/bormar_race_dashboard.html"
)


def time_to_sec(t: str | None) -> int | None:
    if not t:
        return None
    parts = [int(x) for x in t.strip().split(":") if x.strip().isdigit()]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return None


def sec_to_hms(s: float | None) -> str:
    if s is None:
        return "-"
    sec = int(round(s))
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def sec_to_pace(s_per_km: float | None) -> str:
    if s_per_km is None:
        return "-"
    sec = int(round(s_per_km))
    return f"{sec // 60}:{sec % 60:02d} /km"


def compute_netto_sec(splits_dict: dict | None, split_cols: list[str], finish_time: str | None = None) -> int | None:
    f_sec = time_to_sec(finish_time) if finish_time else None
    if not splits_dict or not split_cols:
        return f_sec
    if "FINISH" not in split_cols and f_sec is not None:
        return f_sec
    vals = [time_to_sec(splits_dict.get(c)) for c in split_cols]
    if not vals or vals[-1] is None:
        return f_sec
    if any(v is None for v in vals):
        last_none = max(i for i, v in enumerate(vals) if v is None)
        tail = vals[last_none + 1 :]
        return sum(tail) if tail else f_sec
    return sum(vals)


CATEGORY_ORDER = [
    "TOP 8 OVERALL",
    "TOP 5 OVERALL",
    "TOP 3 OVERALL",
    "TOP 5 NATIONAL",
    "TOP 3 NATIONAL",
    "OPEN",
    "NATIONAL",
    "MASTER NATIONAL 40+",
    "PACER",
]

EVENT_BUCKET_CONFIG = {
    "marathon": {
        "start_sec": 2 * 3600,
        "cot_sec": 6 * 3600 + 30 * 60,
        "step_sec": 30 * 60,
        "cot_label": "06:30:00 (Black Flag @ 09:45 WIB)",
        "over_cot_label": "> 6:30:00",
        "step_label": "30-min range",
    },
    "half_marathon": {
        "start_sec": 1 * 3600,
        "cot_sec": 3 * 3600 + 40 * 60,
        "step_sec": 20 * 60,
        "cot_label": "03:40:00 (08:50 WIB)",
        "over_cot_label": "> 3:40:00",
        "step_label": "20-min range",
    },
    "10k": {
        "start_sec": 30 * 60,
        "cot_sec": 2 * 3600,
        "step_sec": 10 * 60,
        "cot_label": "02:00:00 (07:40 WIB)",
        "over_cot_label": "> 2:00:00",
        "step_label": "10-min range",
    },
}


def compute_dashboard_data() -> dict:
    raw = json.loads((WORKSPACE / "bormar_all_results.json").read_text(encoding="utf-8"))
    events_meta = raw["events"]
    all_results = raw["results"]

    events_analytics = []
    total_all = len(all_results)
    status_all = Counter(r["status"] for r in all_results)
    bf_all = sum(1 for r in all_results if r.get("remark") == "Finished Black Flag")
    all_paces = []

    event_lookup = []
    event_slug_to_idx = {}
    event_dist_by_idx = {}
    event_splits_by_idx = {}

    for idx, ev in enumerate(events_meta):
        slug = ev["event_slug"]
        clean_splits = [s for s in ev["split_checkpoints"] if s != "RTW"]
        event_slug_to_idx[slug] = idx
        event_dist_by_idx[idx] = float(ev["distance_km"])
        event_splits_by_idx[idx] = clean_splits
        event_lookup.append(
            {
                "slug": slug,
                "name": ev["event_name"],
                "day": ev["race_day"],
                "dist": float(ev["distance_km"]),
                "splits": clean_splits,
                "eid": idx + 1,
            }
        )

    for ev in events_meta:
        slug = ev["event_slug"]
        dist = float(ev["distance_km"])
        clean_splits = [s for s in ev["split_checkpoints"] if s != "RTW"]
        rows = [r for r in all_results if r["event_slug"] == slug]
        total = len(rows)
        counts = Counter(r["status"] for r in rows)

        fin_count = counts.get("FINISHED", 0)
        bf_count = counts.get("BLACK_FLAG", 0)
        fin_plus_bf = fin_count + bf_count
        dnf_count = counts.get("DNF", 0)
        cut_count = counts.get("CUT", 0)
        dns_count = counts.get("DNS", 0)
        dq_count = counts.get("DQ", 0) + counts.get("DSQ", 0)

        bf_cp_counts = Counter(r.get("last_checkpoint") or "Unknown" for r in rows if r["status"] == "BLACK_FLAG")

        fin_rows = [r for r in rows if r["status"] == "FINISHED" and time_to_sec(r["time"])]
        fin_secs = [time_to_sec(r["time"]) for r in fin_rows]
        netto_secs = [
            ns for ns in (compute_netto_sec(r.get("splits"), clean_splits, r.get("time")) for r in fin_rows) if ns is not None
        ]
        male_secs = [time_to_sec(r["time"]) for r in fin_rows if r.get("gender") == "Male"]
        female_secs = [time_to_sec(r["time"]) for r in fin_rows if r.get("gender") == "Female"]

        avg_sec = statistics.mean(fin_secs) if fin_secs else None
        med_sec = statistics.median(fin_secs) if fin_secs else None
        min_sec = min(fin_secs) if fin_secs else None

        avg_netto_sec = statistics.mean(netto_secs) if netto_secs else None
        med_netto_sec = statistics.median(netto_secs) if netto_secs else None
        min_netto_sec = min(netto_secs) if netto_secs else None

        avg_pace_sec = (avg_sec / dist) if avg_sec else None
        med_pace_sec = (med_sec / dist) if med_sec else None
        best_pace_sec = (min_sec / dist) if min_sec else None
        male_pace_sec = (statistics.mean(male_secs) / dist) if male_secs else None
        female_pace_sec = (statistics.mean(female_secs) / dist) if female_secs else None

        all_paces.extend([s / dist for s in fin_secs])

        buckets = []
        b_cfg = EVENT_BUCKET_CONFIG.get(slug)
        if fin_secs and b_cfg:
            b_start_sec = b_cfg["start_sec"]
            b_cot_sec = b_cfg["cot_sec"]
            b_step_sec = b_cfg["step_sec"]
            bucket_count = int((b_cot_sec - b_start_sec) // b_step_sec)
            for i in range(bucket_count):
                b_start = b_start_sec + i * b_step_sec
                b_end = b_start_sec + (i + 1) * b_step_sec
                min_s = 0 if i == 0 else b_start
                max_s = b_cot_sec if i == bucket_count - 1 else (b_end - 1)
                cnt = sum(1 for s in fin_secs if min_s <= s <= max_s)
                buckets.append(
                    {
                        "label": f"{sec_to_hms(b_start)[:5]}–{sec_to_hms(b_end)[:5]}",
                        "pace_label": f"{sec_to_pace(b_start / dist)} – {sec_to_pace(b_end / dist)}",
                        "count": cnt,
                        "pct": round(cnt * 100.0 / len(fin_secs), 1),
                        "min_sec": min_s,
                        "max_sec": max_s,
                        "is_over_cot": False,
                    }
                )
            over_min_s = b_cot_sec + 1
            over_max_s = 999999
            over_cnt = sum(1 for s in fin_secs if s >= over_min_s)
            buckets.append(
                {
                    "label": b_cfg["over_cot_label"],
                    "pace_label": f"> {sec_to_pace(b_cot_sec / dist)}",
                    "count": over_cnt,
                    "pct": round(over_cnt * 100.0 / len(fin_secs), 1),
                    "min_sec": over_min_s,
                    "max_sec": over_max_s,
                    "is_over_cot": True,
                }
            )

        cat_groups = defaultdict(list)
        cat_all_rows = defaultdict(list)
        cat_bf_rows = defaultdict(int)
        for r in rows:
            cat = r.get("category") or "Unknown"
            gen = r.get("gender") or "Unknown"
            if cat in ("Unknown", "PACER") or gen == "Unknown":
                continue
            cat_all_rows[(cat, gen)].append(r)
            if r["status"] == "BLACK_FLAG":
                cat_bf_rows[(cat, gen)] += 1
            if r["status"] == "FINISHED" and time_to_sec(r["time"]):
                cat_groups[(cat, gen)].append(r)

        def sort_key(cg):
            c, g = cg
            c_idx = CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99
            g_idx = 0 if g == "Male" else 1
            return (c_idx, c, g_idx)

        categories_data = []
        podium_bibs = set()
        cat_rank_by_bib = {}
        for cat, gen in sorted(cat_groups.keys(), key=sort_key):
            group_finishers = sorted(cat_groups[(cat, gen)], key=lambda x: time_to_sec(x["time"]) or 999999)
            group_total = len(cat_all_rows[(cat, gen)])
            group_bf = cat_bf_rows[(cat, gen)]
            group_secs = [time_to_sec(x["time"]) for x in group_finishers]
            g_avg_sec = statistics.mean(group_secs)
            for r_idx, runner in enumerate(group_finishers, start=1):
                cat_rank_by_bib[runner["bib_no"]] = r_idx
                if r_idx <= 3 or cat in ("TOP 8 OVERALL", "TOP 5 OVERALL", "TOP 3 OVERALL", "TOP 5 NATIONAL", "TOP 3 NATIONAL"):
                    podium_bibs.add(runner["bib_no"])
            podium = []
            for rank_idx, runner in enumerate(group_finishers[:3], start=1):
                r_sec = time_to_sec(runner["time"])
                r_netto_sec = compute_netto_sec(runner.get("splits"), clean_splits, runner.get("time"))
                podium.append(
                    {
                        "category_rank": rank_idx,
                        "overall_pos": runner["position"],
                        "bib_no": runner["bib_no"],
                        "aid": runner.get("aid"),
                        "result_url": runner.get("result_url"),
                        "name": runner["name"],
                        "country": runner.get("country") or "-",
                        "time": runner["time"],
                        "netto_time": sec_to_hms(r_netto_sec) if r_netto_sec is not None else runner["time"],
                        "pace": sec_to_pace(r_sec / dist) if r_sec else "-",
                        "netto_pace": sec_to_pace(r_netto_sec / dist) if r_netto_sec else (sec_to_pace(r_sec / dist) if r_sec else "-"),
                    }
                )
            categories_data.append(
                {
                    "category": cat,
                    "gender": gen,
                    "total_entered": group_total,
                    "finishers_count": len(group_finishers),
                    "black_flag_count": group_bf,
                    "finish_pct": round(len(group_finishers) * 100.0 / group_total, 1) if group_total else 0.0,
                    "finish_plus_bf_pct": round((len(group_finishers) + group_bf) * 100.0 / group_total, 1) if group_total else 0.0,
                    "avg_time": sec_to_hms(g_avg_sec),
                    "avg_pace": sec_to_pace(g_avg_sec / dist),
                    "winner": podium[0] if podium else None,
                    "podium": podium,
                }
            )

        ev["_podium_bibs"] = podium_bibs
        ev["_cat_rank_by_bib"] = cat_rank_by_bib

        events_analytics.append(
            {
                "event_slug": slug,
                "event_name": ev["event_name"],
                "race_day": ev["race_day"],
                "distance_km": dist,
                "total": total,
                "finished": fin_count,
                "finished_pct": round(fin_count * 100.0 / total, 2),
                "black_flag": bf_count,
                "black_flag_pct": round(bf_count * 100.0 / total, 2),
                "finished_plus_bf": fin_plus_bf,
                "finished_plus_bf_pct": round(fin_plus_bf * 100.0 / total, 2),
                "bf_checkpoints": [
                    {"cp": cp, "count": bf_cp_counts[cp], "pct": round(bf_cp_counts[cp] * 100.0 / bf_count, 1)}
                    for cp in ["KM 39.4", "KM 35", "KM 34", "KM 31.2", "KM 28.4"]
                    if bf_cp_counts.get(cp, 0) > 0
                ],
                "dnf": dnf_count,
                "dnf_pct": round(dnf_count * 100.0 / total, 2),
                "cut": cut_count,
                "cut_pct": round(cut_count * 100.0 / total, 2),
                "dnf_plus_cut": dnf_count + cut_count,
                "dnf_plus_cut_pct": round((dnf_count + cut_count) * 100.0 / total, 2),
                "dns": dns_count,
                "dns_pct": round(dns_count * 100.0 / total, 2),
                "dq": dq_count,
                "dq_pct": round(dq_count * 100.0 / total, 2),
                "other": dq_count,
                "other_pct": round(dq_count * 100.0 / total, 2),
                "avg_time": sec_to_hms(avg_sec),
                "median_time": sec_to_hms(med_sec),
                "best_time": sec_to_hms(min_sec),
                "avg_netto_time": sec_to_hms(avg_netto_sec),
                "median_netto_time": sec_to_hms(med_netto_sec),
                "best_netto_time": sec_to_hms(min_netto_sec),
                "avg_pace": sec_to_pace(avg_pace_sec),
                "median_pace": sec_to_pace(med_pace_sec),
                "best_pace": sec_to_pace(best_pace_sec),
                "male_avg_pace": sec_to_pace(male_pace_sec),
                "female_avg_pace": sec_to_pace(female_pace_sec),
                "male_finishers": len(male_secs),
                "female_finishers": len(female_secs),
                "cot_label": b_cfg["cot_label"] if b_cfg else "-",
                "step_label": b_cfg["step_label"] if b_cfg else "-",
                "buckets": buckets,
                "categories": categories_data,
            }
        )

    # Compact runner encoding:
    # [0: event_idx, 1: pos_or_null, 2: status_str, 3: bib_no, 4: name, 5: bruto_time_str,
    #  6: bruto_pace_str, 7: category, 8: gender, 9: country, 10: splits_array, 11: is_podium (1/0),
    #  12: cat_rank, 13: netto_time_str, 14: netto_pace_str, 15: remark_str, 16: class_or_last_cp_str,
    #  17: raw_status_str]
    compact_runners = []
    for r in all_results:
        ev_idx = event_slug_to_idx[r["event_slug"]]
        ev_obj = events_meta[ev_idx]
        dist = event_dist_by_idx[ev_idx]
        split_cols = event_splits_by_idx[ev_idx]
        t_str = r.get("time") or ""
        t_sec = time_to_sec(t_str) if r["status"] == "FINISHED" else None
        p_str = sec_to_pace(t_sec / dist).replace(" /km", "") if t_sec else ""
        netto_sec = compute_netto_sec(r.get("splits"), split_cols, t_str) if r["status"] == "FINISHED" else None
        netto_str = sec_to_hms(netto_sec) if netto_sec is not None else ""
        netto_p_str = sec_to_pace(netto_sec / dist).replace(" /km", "") if netto_sec else p_str
        splits_arr = [r["splits"].get(c) or "" for c in split_cols]
        bib = r["bib_no"]
        pos = r["position"]
        is_pod = 1 if (bib in ev_obj.get("_podium_bibs", set()) or (pos is not None and pos <= 3)) else 0
        cat_rk = ev_obj.get("_cat_rank_by_bib", {}).get(bib)
        remark_str = r.get("remark") or ""
        class_str = r.get("class") or r.get("last_checkpoint") or ""
        raw_st = r.get("raw_status") or r["status"]
        aid_val = r.get("aid")

        compact_runners.append(
            [
                ev_idx,
                pos,
                r["status"],
                bib,
                r["name"],
                t_str,
                p_str,
                r.get("category") or "Unknown",
                r.get("gender") or "Unknown",
                r.get("country") or "-",
                splits_arr,
                is_pod,
                cat_rk,
                netto_str,
                netto_p_str,
                remark_str,
                class_str,
                raw_st,
                aid_val,
            ]
        )

    fin_all = status_all.get("FINISHED", 0)
    fin_plus_bf_all = fin_all + bf_all
    dnf_all = status_all.get("DNF", 0)
    cut_all = status_all.get("CUT", 0)
    dns_all = status_all.get("DNS", 0)
    dq_all = status_all.get("DQ", 0) + status_all.get("DSQ", 0)

    return {
        "overall": {
            "total": total_all,
            "finished": fin_all,
            "finished_pct": round(fin_all * 100.0 / total_all, 2),
            "black_flag": bf_all,
            "black_flag_pct": round(bf_all * 100.0 / total_all, 2),
            "finished_plus_bf": fin_plus_bf_all,
            "finished_plus_bf_pct": round(fin_plus_bf_all * 100.0 / total_all, 2),
            "dnf": dnf_all,
            "dnf_pct": round(dnf_all * 100.0 / total_all, 2),
            "cut": cut_all,
            "cut_pct": round(cut_all * 100.0 / total_all, 2),
            "dnf_plus_cut": dnf_all + cut_all,
            "dnf_plus_cut_pct": round((dnf_all + cut_all) * 100.0 / total_all, 2),
            "dns": dns_all,
            "dns_pct": round(dns_all * 100.0 / total_all, 2),
            "dq": dq_all,
            "dq_pct": round(dq_all * 100.0 / total_all, 2),
            "other": dq_all,
            "other_pct": round(dq_all * 100.0 / total_all, 2),
            "avg_pace": sec_to_pace(statistics.mean(all_paces)),
            "median_pace": sec_to_pace(statistics.median(all_paces)),
        },
        "events": events_analytics,
        "event_lookup": event_lookup,
        "runners": compact_runners,
    }


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Borobudur Marathon 2026 — Race Analytics &amp; Runner Search Dashboard</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {
      color-scheme: dark;
    }
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    ::-webkit-scrollbar-track {
      background: var(--background);
    }
    ::-webkit-scrollbar-thumb {
      background: var(--border);
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: var(--muted-foreground);
    }
  </style>
</head>
<body class="bg-[var(--background)] text-[var(--foreground)] antialiased p-4 md:p-6 transition-colors duration-150">
  <div class="max-w-7xl mx-auto space-y-6">
    <!-- Header Banner -->
    <div id="topHeaderSection" class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div>
          <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-bold uppercase tracking-wider mb-2">
            Bank Jateng Borobudur Marathon 2026
          </div>
          <h1 class="text-2xl md:text-3xl font-bold tracking-tight text-[var(--foreground)]">
            Race Analytics &amp; Results Explorer
          </h1>
          <p class="text-sm text-[var(--muted-foreground)] mt-1">
            Full 42K Finishers (<strong>1,909</strong>), <strong>2,346 Finished Black Flag 🏅</strong> (passed COP 3 @ KM 34.5 before 09:45 WIB heat halt — get medals), <strong>188 DNF</strong> (did not pass COP), category podiums, and 12,800-runner search across Marathon, Half Marathon &amp; 10K. Data from <a href="https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340" target="_blank" rel="noopener noreferrer" class="font-medium text-red-500 hover:text-red-400 hover:underline">https://results.scorenow.co.id</a>
          </p>
        </div>
        <!-- Simple Light / Dark Mode Switcher -->
        <div class="inline-flex items-center rounded-lg border border-[var(--border)] p-0.5 bg-[var(--background)] self-start shrink-0" role="group" aria-label="Theme Switch">
          <button
            id="themeLightBtn"
            onclick="setTheme('light')"
            class="px-3 py-1 rounded-md text-xs font-medium transition"
          >
            Light
          </button>
          <button
            id="themeDarkBtn"
            onclick="setTheme('dark')"
            class="px-3 py-1 rounded-md text-xs font-medium transition"
          >
            Dark
          </button>
        </div>
      </div>
      <!-- Event Selector Bar -->
      <div class="pt-4 border-t border-[var(--border)] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <span class="text-xs font-semibold uppercase tracking-wider text-[var(--muted-foreground)] shrink-0">Race Event Filter</span>
        <div id="eventTabs" class="flex flex-wrap items-center gap-2"></div>
      </div>
    </div>

    <!-- Sticky Section Navigation Menu -->
    <div class="sticky top-2 z-40 flex flex-col items-end">
      <nav id="stickyNavExpanded" class="w-full bg-[var(--card)]/95 backdrop-blur-md border border-[var(--border)] rounded-xl px-3.5 py-2 shadow-sm flex flex-wrap items-center justify-between gap-2" aria-label="Section Navigation">
        <div class="flex flex-wrap items-center gap-1.5">
          <button
            data-nav-target="overviewSection"
            onclick="scrollToSection('overviewSection')"
            class="nav-jump-btn px-3 py-1.5 rounded-lg text-xs font-semibold transition bg-red-600 text-white shadow-sm hover:bg-red-500"
          >
            Overview &amp; Pace
          </button>
          <button
            data-nav-target="blackFlagSection"
            onclick="scrollToSection('blackFlagSection')"
            class="nav-jump-btn px-3 py-1.5 rounded-lg text-xs font-medium transition text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--background)]"
          >
            🏴 Black Flag Telemetry
          </button>
          <button
            data-nav-target="countrySection"
            onclick="scrollToSection('countrySection')"
            class="nav-jump-btn px-3 py-1.5 rounded-lg text-xs font-medium transition text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--background)]"
          >
            Country Joiners
          </button>
          <button
            data-nav-target="winnersSection"
            onclick="scrollToSection('winnersSection')"
            class="nav-jump-btn px-3 py-1.5 rounded-lg text-xs font-medium transition text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--background)]"
          >
            Category Winners &amp; Podiums
          </button>
          <button
            data-nav-target="runnerTableSection"
            onclick="scrollToSection('runnerTableSection')"
            class="nav-jump-btn px-3 py-1.5 rounded-lg text-xs font-medium transition text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--background)]"
          >
            All Runners Results
          </button>
          <a
            href='https://ko-fi.com/V7V2JM8S4'
            target='_blank'
            rel='noopener noreferrer'
            class='hover:opacity-90 transition inline-flex items-center shrink-0 ml-1'
            title='Support on Ko-fi'
          >
            <img height='32' style='border:0px;height:28px;' src='https://storage.ko-fi.com/cdn/kofi5.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' />
          </a>
        </div>
        <div class="flex items-center gap-1.5 ml-auto">
          <button
            onclick="scrollToSection('topHeaderSection')"
            class="px-2.5 py-1 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition"
            title="Scroll back to top"
          >
            ↑ Top
          </button>
          <button
            onclick="toggleNavMenu(true)"
            class="px-2.5 py-1 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition"
            title="Hide navigation menu"
          >
            Hide Menu
          </button>
        </div>
      </nav>
      <div id="stickyNavCollapsed" class="hidden inline-flex items-center gap-2 bg-[var(--card)]/95 backdrop-blur-md border border-[var(--border)] rounded-xl px-2.5 py-1.5 shadow-sm">
        <a href='https://ko-fi.com/V7V2JM8S4' target='_blank' rel='noopener noreferrer' class='hover:opacity-90 transition inline-flex items-center shrink-0' title='Support on Ko-fi'>
          <img height='36' style='border:0px;height:28px;' src='https://storage.ko-fi.com/cdn/kofi5.png?v=6' border='0' alt='Buy Me a Coffee at ko-fi.com' />
        </a>
        <button
          onclick="toggleNavMenu(false)"
          class="px-2.5 py-1 rounded-lg bg-red-600 text-white text-xs font-semibold shadow-sm transition hover:bg-red-500"
        >
          Menu
        </button>
        <button
          onclick="scrollToSection('topHeaderSection')"
          class="px-2.5 py-1 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition"
          title="Scroll back to top"
        >
          ↑ Top
        </button>
      </div>
    </div>

    <!-- Top KPI Cards -->
    <div id="overviewSection" class="scroll-mt-20 space-y-6">
      <div id="kpiGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4"></div>

      <!-- Status Breakdown Bar + Event Comparison Table -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <!-- Left: Status Breakdown & Pace Details -->
        <div class="lg:col-span-5 bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm flex flex-col justify-between space-y-4">
          <div>
            <h2 id="statusCardTitle" class="text-base font-semibold text-[var(--foreground)]">Completion &amp; Attrition Breakdown</h2>
            <p class="text-xs text-[var(--muted-foreground)] mt-0.5">Full Finishers, <strong>Finished Black Flag</strong> (09:45 WIB halt), DNF, DQ, and DNS</p>
          </div>
          <div id="statusVisual" class="space-y-4"></div>
          <div id="paceGenderCards" class="grid grid-cols-2 gap-3 pt-2 border-t border-[var(--border)]"></div>
        </div>

        <!-- Right: All 3 Events Comparison Matrix OR Finish Time Histogram -->
        <div class="lg:col-span-7 bg-[var(--card)] border border-[var(--border)] rounded-2xl p-5 shadow-sm space-y-4">
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <div>
              <h2 id="rightPanelTitle" class="text-base font-semibold text-[var(--foreground)]">Event-by-Event Performance Matrix</h2>
              <p id="rightPanelSubtitle" class="text-xs text-[var(--muted-foreground)] mt-0.5">Click any event row to filter the dashboard to that specific race</p>
            </div>
          </div>
          <div id="rightPanelContent"></div>
        </div>
      </div>
    </div>

    <!-- Black Flag Early Halt Notice & Official Cut-Off Points (COP) Telemetry Section -->
    <div id="blackFlagSection" class="scroll-mt-20 bg-[var(--card)] border border-sky-500/40 rounded-2xl p-6 shadow-sm space-y-5">
      <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 pb-4 border-b border-[var(--border)]">
        <div class="space-y-1">
          <div class="flex flex-wrap items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-md text-xs font-bold bg-sky-500/15 text-sky-400 border border-sky-500/30">🏴 OFFICIAL COP &amp; BLACK FLAG TELEMETRY — START 04:15 WIB</span>
            <h2 class="text-lg font-bold text-[var(--foreground)]">Full Marathon (42.195K) — Cut-Off Points (COP 1–3) &amp; Black Flag Medal Calculation</h2>
          </div>
          <p class="text-xs text-[var(--muted-foreground)] leading-relaxed">
            The <strong>Bank Jateng Borobudur Marathon 2026 (42.195K Full Marathon)</strong> started at <strong>04:15 WIB</strong> (Waves: W1 <code>04:15</code>, W2 <code>04:20</code>, W3 <code>04:25</code>, W4 <code>04:30 WIB</code>) using the same official race clock for every wave. Official Cut-Off Points are <strong>COP 1 at KM 10 (closes 06:05 WIB)</strong>, <strong>COP 2 at KM 20 (closes 07:35 WIB)</strong>, <strong>COP 3 at KM 34.5 (closes 09:50 WIB)</strong>, and <strong>FINISH at KM 42.195 (closes 11:00 WIB)</strong>. Due to high temperature/WBGT, the race was halted by the <strong>Black Flag at 09:45 WIB</strong>. Runners who <strong>passed COP 3 (KM 34 / KM 35 / KM 39.4 within 09:50 WIB)</strong> but did not finish due to the halt are classified as <strong>Finished Black Flag (<code>2,346</code> runners — get finisher medals 🏅)</strong>, bringing total recognized Marathon finishers to <strong>4,255 of 4,857 (87.61%)</strong>. Runners who <strong>did not pass COP 1, COP 2, or COP 3</strong> (including 76 stopped at KM 28.4–31.2 before COP 3 and 63 cut off at KM 19.6 / COP 2) are classified as <strong>DNF (<code>188</code> runners)</strong>.
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-2 shrink-0">
          <button
            onclick="filterBlackFlagRunners()"
            class="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-sm transition"
          >
            🏴🏅 View 2,346 Finished Black Flag (Get Medals) ↓
          </button>
          <button
            onclick="filterDnfByCop('Did Not Pass COP')"
            class="px-3 py-2 rounded-xl bg-amber-500/15 hover:bg-amber-500/25 border border-amber-500/40 text-amber-400 text-xs font-semibold transition"
          >
            ❌ View 188 DNF (Missed COP) ↓
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        <!-- Left: Official Cut-Off Times (COP 1, COP 2, COP 3, FINISH) Table -->
        <div class="lg:col-span-7 bg-[var(--background)] border border-[var(--border)] rounded-xl p-4 flex flex-col justify-between space-y-3">
          <div>
            <div class="text-sm font-bold text-[var(--foreground)]">1. Official Marathon Cut-Off Times (COP) &amp; Race Clock Rules (Start: 04:15 WIB)</div>
            <div class="text-xs text-[var(--muted-foreground)] mt-0.5">Same official race clock (WIB) for all waves (W1 04:15 • W2 04:20 • W3 04:25 • W4 04:30) • Miss any COP → DNF</div>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse text-xs">
              <thead>
                <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)]">
                  <th class="py-2 pr-2 font-semibold">Cut-Off Point</th>
                  <th class="py-2 px-2 font-semibold">Distance (Mat)</th>
                  <th class="py-2 px-2 font-semibold">Closes At (WIB)</th>
                  <th class="py-2 px-2 font-semibold">Max Elapsed (04:15 / W4)</th>
                  <th class="py-2 pl-2 font-semibold">COP Telemetry &amp; Medal Outcome</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--border)]">
                <tr>
                  <td class="py-2.5 pr-2 font-bold text-[var(--foreground)]">COP 1</td>
                  <td class="py-2.5 px-2 font-mono text-[var(--foreground)]">10.0 KM <span class="block text-[11px] text-[var(--muted-foreground)]">(Mat: KM 10)</span></td>
                  <td class="py-2.5 px-2 font-mono font-bold text-[var(--foreground)]">06:05 WIB</td>
                  <td class="py-2.5 px-2 font-mono text-[var(--muted-foreground)]">1h 50m <span class="block text-[11px]">(1h 35m from W4)</span></td>
                  <td class="py-2.5 pl-2 text-amber-400 font-semibold">4 DNF missed COP 1 <span class="block text-[11px] font-normal text-[var(--muted-foreground)]">4,439 active runners passed KM 10 ≤ 06:05 WIB</span></td>
                </tr>
                <tr>
                  <td class="py-2.5 pr-2 font-bold text-[var(--foreground)]">COP 2</td>
                  <td class="py-2.5 px-2 font-mono text-[var(--foreground)]">20.0 KM <span class="block text-[11px] text-[var(--muted-foreground)]">(Mat: KM 19.6)</span></td>
                  <td class="py-2.5 px-2 font-mono font-bold text-[var(--foreground)]">07:35 WIB</td>
                  <td class="py-2.5 px-2 font-mono text-[var(--muted-foreground)]">3h 20m <span class="block text-[11px]">(3h 05m from W4)</span></td>
                  <td class="py-2.5 pl-2 text-amber-400 font-semibold">83 DNF at/before COP 2 <span class="block text-[11px] font-normal text-[var(--muted-foreground)]">20 stopped at KM 10–15 + 63 cut off at KM 19.6</span></td>
                </tr>
                <tr>
                  <td class="py-2.5 pr-2 font-bold text-sky-400">COP 3 (Medal Gate)</td>
                  <td class="py-2.5 px-2 font-mono text-[var(--foreground)]">34.5 KM <span class="block text-[11px] text-[var(--muted-foreground)]">(Mats: KM 34 / 35)</span></td>
                  <td class="py-2.5 px-2 font-mono font-bold text-sky-400">09:50 WIB <span class="block text-[10px] font-normal text-[var(--muted-foreground)]">(Halt @ 09:45)</span></td>
                  <td class="py-2.5 px-2 font-mono text-[var(--muted-foreground)]">5h 35m <span class="block text-[11px]">(5h 20m from W4)</span></td>
                  <td class="py-2.5 pl-2 text-sky-400 font-semibold">🏅 2,346 Passed → Black Flag Medal <span class="block text-[11px] font-normal text-amber-400">❌ 97 DNF missed COP 3 (KM 21.1–31.2 + 1 &gt; 09:50)</span></td>
                </tr>
                <tr>
                  <td class="py-2.5 pr-2 font-bold text-red-400">FINISH</td>
                  <td class="py-2.5 px-2 font-mono text-[var(--foreground)]">42.195 KM <span class="block text-[11px] text-[var(--muted-foreground)]">(Finish Line)</span></td>
                  <td class="py-2.5 px-2 font-mono font-bold text-red-400">11:00 WIB</td>
                  <td class="py-2.5 px-2 font-mono text-[var(--muted-foreground)]">6h 45m <span class="block text-[11px]">(6h 30m from W4)</span></td>
                  <td class="py-2.5 pl-2 text-red-400 font-semibold">🏆 1,909 Full 42.195K Finishers <span class="block text-[11px] font-normal text-[var(--muted-foreground)]">Half Marathon (08:50) &amp; 10K (07:40) already finished</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Right: COP 3 Pass (Finished Black Flag Get Medals) vs Missed COP (DNF) -->
        <div class="lg:col-span-5 bg-[var(--background)] border border-[var(--border)] rounded-xl p-4 flex flex-col justify-between space-y-3">
          <div>
            <div class="text-sm font-bold text-[var(--foreground)]">2. COP Breakdown: Black Flag Medalists (2,346) vs. DNF (188)</div>
            <div class="text-xs text-[var(--muted-foreground)] mt-0.5">Click any group below to filter the runner table to that exact COP cohort</div>
          </div>
          <div class="space-y-2 my-auto">
            <div onclick="filterBlackFlagByCheckpoint('KM 39.4')" class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--border)] hover:border-sky-500/50 cursor-pointer transition">
              <div class="flex items-center justify-between text-xs">
                <span class="font-bold text-sky-400">🏅 Passed COP 3 — Reached KM 39.4 (~KM 39.4–41.9)</span>
                <span class="font-mono font-bold text-[var(--foreground)]">272 runners (11.6%)</span>
              </div>
              <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">Passed all 3 COPs, stopped &lt; 2.8 KM from finish at 09:45 WIB → <strong>Finished Black Flag (Get Medal)</strong></div>
            </div>
            <div onclick="filterBlackFlagByCheckpoint('KM 35')" class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--border)] hover:border-sky-500/50 cursor-pointer transition">
              <div class="flex items-center justify-between text-xs">
                <span class="font-bold text-sky-400">🏅 Passed COP 3 — Reached KM 35 (~KM 35.0–39.4)</span>
                <span class="font-mono font-bold text-[var(--foreground)]">1,451 runners (61.8%)</span>
              </div>
              <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">Passed COP 3 (KM 34.5 ≤ 09:50 WIB) &amp; KM 35 mat before halt → <strong>Finished Black Flag (Get Medal)</strong></div>
            </div>
            <div onclick="filterBlackFlagByCheckpoint('KM 34')" class="p-2.5 rounded-lg bg-[var(--card)] border border-[var(--border)] hover:border-sky-500/50 cursor-pointer transition">
              <div class="flex items-center justify-between text-xs">
                <span class="font-bold text-sky-400">🏅 Passed COP 3 — Reached KM 34 (≤ 09:50 WIB)</span>
                <span class="font-mono font-bold text-[var(--foreground)]">623 runners (26.6%)</span>
              </div>
              <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">Cleared KM 34 / COP 3 within 09:50 WIB cutoff when halted → <strong>Finished Black Flag (Get Medal)</strong></div>
            </div>
            <div onclick="filterDnfByCop('Did Not Pass COP')" class="p-2.5 rounded-lg bg-amber-500/5 border border-amber-500/30 hover:border-amber-500/60 cursor-pointer transition">
              <div class="flex items-center justify-between text-xs">
                <span class="font-bold text-amber-400">❌ Did Not Pass COP → Official DNF (No Medal)</span>
                <span class="font-mono font-bold text-amber-400">188 runners (3.87%)</span>
              </div>
              <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">4 missed COP 1 (KM 10) • 83 missed/cut at COP 2 (KM 20) • 97 missed COP 3 (KM 21.1–31.2 + 1 &gt; 09:50) • 4 early dropouts</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Country Joiners Pie Chart & Nationality Breakdown Section -->
    <div id="countrySection" class="scroll-mt-20 bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm space-y-5">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-4 border-b border-[var(--border)]">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h2 id="countrySectionTitle" class="text-lg font-bold text-[var(--foreground)]">Country Joiners — Participant Nationality Breakdown</h2>
            <span id="countryTotalBadge" class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20"></span>
          </div>
          <p class="text-xs text-[var(--muted-foreground)] mt-0.5">
            Distribution of registered runners by country (Overall Domestic vs International + Top International Countries Pie Chart) — click any country to filter the runner table
          </p>
        </div>
      </div>
      <div id="countryChartsContainer" class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch"></div>
    </div>

    <!-- Category Winners & Podium Section -->
    <div id="winnersSection" class="scroll-mt-20 bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm space-y-5">
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-4 border-b border-[var(--border)]">
        <div>
          <h2 class="text-lg font-bold text-[var(--foreground)]">Category Winners &amp; Podiums (All Events)</h2>
          <p class="text-xs text-[var(--muted-foreground)] mt-0.5">
            1st, 2nd, and 3rd place finishers for every race category &amp; gender division, plus category average pace and finish rate
          </p>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <!-- Gender Filter -->
          <div id="genderFilterBtns" class="inline-flex rounded-lg border border-[var(--border)] p-1 bg-[var(--background)]">
            <button data-gender="ALL" class="gender-btn px-3 py-1 rounded-md text-xs font-medium">All Genders</button>
            <button data-gender="Male" class="gender-btn px-3 py-1 rounded-md text-xs font-medium">Male</button>
            <button data-gender="Female" class="gender-btn px-3 py-1 rounded-md text-xs font-medium">Female</button>
          </div>
          <!-- View Mode Toggle -->
          <div id="viewModeBtns" class="inline-flex rounded-lg border border-[var(--border)] p-1 bg-[var(--background)]">
            <button data-mode="cards" class="mode-btn px-3 py-1 rounded-md text-xs font-medium">Podium Cards (Top 3)</button>
            <button data-mode="table" class="mode-btn px-3 py-1 rounded-md text-xs font-medium">Summary Table (#1 Winners)</button>
          </div>
          <!-- Expand / Collapse All Events -->
          <div class="inline-flex rounded-lg border border-[var(--border)] p-1 bg-[var(--background)]">
            <button onclick="expandAllWinnerEvents()" class="px-2.5 py-1 rounded-md text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition">Expand All</button>
            <button onclick="collapseAllWinnerEvents()" class="px-2.5 py-1 rounded-md text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition">Collapse All</button>
          </div>
          <!-- Search input -->
          <input
            id="winnerSearch"
            type="text"
            placeholder="Search winner, bib, category..."
            class="px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs focus:outline-none"
          />
        </div>
      </div>

      <div id="winnersContainer"></div>
    </div>

    <!-- All-Events Detailed Runner Search & Results Table -->
    <div id="runnerTableSection" class="scroll-mt-20 bg-[var(--card)] border border-[var(--border)] rounded-2xl p-6 shadow-sm space-y-4">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-[var(--border)]">
        <div>
          <div class="flex flex-wrap items-center gap-2">
            <h2 class="text-lg font-bold text-[var(--foreground)]">All-Events Race Results — All Runners (With Podium &amp; Black Flag Remark)</h2>
            <span id="runnerResultCountBadge" class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">12,800 runners</span>
            <span id="activeBucketFilterBadge" class="hidden inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-500/15 text-sky-500 border border-sky-500/30"></span>
          </div>
          <p class="text-xs text-[var(--muted-foreground)] mt-0.5">
            Search any runner by Name, Bib Number, or Country across all 3 events — filter by <strong>Finished Black Flag</strong> remark or click any row to inspect full checkpoint splits
          </p>
        </div>
        <button
          id="resetRunnerFiltersBtn"
          class="self-start lg:self-auto px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-medium text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition"
        >
          Reset Filters
        </button>
      </div>

      <!-- Search & Filter Controls Bar -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-7 gap-3">
        <div class="sm:col-span-2">
          <label class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Search Runner (Name, Bib No, Country)</label>
          <input
            id="runnerSearchInput"
            type="text"
            placeholder="e.g. WILSON, NURSHODIQ, CYNTHIA, Indonesia..."
            class="w-full px-3 py-2 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] text-xs focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500/30"
          />
        </div>
        <div>
          <label class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Event</label>
          <select
            id="runnerEventSelect"
            class="w-full px-3 py-2 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] text-xs focus:outline-none"
          >
            <option value="ALL">All 3 Events (12,800)</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Category</label>
          <select
            id="runnerCategorySelect"
            class="w-full px-3 py-2 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] text-xs focus:outline-none"
          >
            <option value="ALL">All Categories</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Gender</label>
          <select
            id="runnerGenderSelect"
            class="w-full px-3 py-2 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] text-xs focus:outline-none"
          >
            <option value="ALL">All Genders</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">Status</label>
          <select
            id="runnerStatusSelect"
            class="w-full px-3 py-2 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] text-xs focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="ALL_FINISHERS">All Finishers (42K + Black Flag)</option>
            <option value="FINISHED">FINISHED (Full Distance)</option>
            <option value="BLACK_FLAG">🏴 BLACK_FLAG (Finished Black Flag)</option>
            <option value="DNF">DNF (Did Not Finish)</option>
            <option value="DNS">DNS (Did Not Start)</option>
            <option value="DQ">DQ (Disqualified)</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-medium text-[var(--muted-foreground)] mb-1">COP &amp; Black Flag Filter</label>
          <select
            id="runnerRemarkSelect"
            class="w-full px-3 py-2 rounded-xl border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] text-xs focus:outline-none"
          >
            <option value="ALL">All COP &amp; Remarks</option>
            <option value="Finished Black Flag">🏴🏅 Finished Black Flag — Get Medal (2,346)</option>
            <option value="Passed COP 3 — Stopped at KM 39.4 (Get Medal)">↳ Passed COP 3 — Stopped @ KM 39.4 (272)</option>
            <option value="Passed COP 3 — Stopped at KM 35 (Get Medal)">↳ Passed COP 3 — Stopped @ KM 35 (1,451)</option>
            <option value="Passed COP 3 — Stopped at KM 34 (Get Medal)">↳ Passed COP 3 — Stopped @ KM 34 (623)</option>
            <option value="Did Not Pass COP">❌ DNF — All Did Not Pass COP (188)</option>
            <option value="Missed COP 3">↳ DNF — Missed COP 3 @ KM 34.5 (97)</option>
            <option value="Missed COP 2">↳ DNF — Missed COP 2 @ KM 20 (83)</option>
            <option value="Missed COP 1">↳ DNF — Missed COP 1 @ KM 10 (4)</option>
            <option value="Early Dropout">↳ DNF — Early Dropout Before Halt (4)</option>
          </select>
        </div>
      </div>

      <!-- Selected Runner Split Detail Drawer (shown when a runner row is clicked) -->
      <div id="runnerDetailDrawer" class="hidden rounded-xl border border-red-500/40 bg-red-500/5 p-4 space-y-3"></div>

      <!-- Detailed Runner Table -->
      <div class="overflow-x-auto border border-[var(--border)] rounded-xl">
        <table class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="bg-[var(--background)] border-b border-[var(--border)] text-[var(--muted-foreground)]">
              <th onclick="setRunnerSort('pos')" class="py-3 px-3 font-semibold cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Overall Position">
                <span class="inline-flex items-center gap-1">Overall Pos / Status <span id="sortIcon_pos" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('catRank')" class="py-3 px-2 font-semibold cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Category Rank">
                <span class="inline-flex items-center gap-1">Cat Rank <span id="sortIcon_catRank" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('bib')" class="py-3 px-2.5 font-semibold cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Bib Number">
                <span class="inline-flex items-center gap-1">Bib No <span id="sortIcon_bib" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('name')" class="py-3 px-3 font-semibold cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Runner Name">
                <span class="inline-flex items-center gap-1">Runner Name &amp; Remark <span id="sortIcon_name" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('event')" class="py-3 px-2.5 font-semibold cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Event">
                <span class="inline-flex items-center gap-1">Event <span id="sortIcon_event" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('category')" class="py-3 px-2.5 font-semibold cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Category">
                <span class="inline-flex items-center gap-1">Category <span id="sortIcon_category" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('gender')" class="py-3 px-2 font-semibold cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Gender">
                <span class="inline-flex items-center gap-1">Gender <span id="sortIcon_gender" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('country')" class="py-3 px-2.5 font-semibold cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Country">
                <span class="inline-flex items-center gap-1">Country <span id="sortIcon_country" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('bruto')" class="py-3 px-2.5 font-semibold text-right cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Finish Time">
                <span class="inline-flex items-center justify-end gap-1 w-full">Finish Time <span id="sortIcon_bruto" class="text-xs">↕</span></span>
              </th>
              <th onclick="setRunnerSort('pace')" class="py-3 px-2.5 font-semibold text-right cursor-pointer select-none hover:text-[var(--foreground)] transition whitespace-nowrap group" title="Click to sort by Average Pace">
                <span class="inline-flex items-center justify-end gap-1 w-full">Avg Pace <span id="sortIcon_pace" class="text-xs">↕</span></span>
              </th>
              <th class="py-3 px-3 font-semibold whitespace-nowrap">Checkpoint Splits</th>
            </tr>
          </thead>
          <tbody id="runnerTableBody" class="divide-y divide-[var(--border)]"></tbody>
        </table>
      </div>

      <!-- Pagination Controls -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2">
        <div id="runnerPaginationInfo" class="text-xs text-[var(--muted-foreground)]"></div>
        <div class="flex items-center gap-2">
          <label class="text-xs text-[var(--muted-foreground)]">Rows:</label>
          <select
            id="runnerPageSizeSelect"
            class="px-2 py-1 rounded-lg border border-[var(--border)] bg-[var(--background)] text-[var(--foreground)] text-xs"
          >
            <option value="10" selected>10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
          <button
            id="prevPageBtn"
            class="px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-medium disabled:opacity-40"
          >
            ← Prev
          </button>
          <span id="pageIndicator" class="text-xs font-semibold px-2"></span>
          <button
            id="nextPageBtn"
            class="px-3 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--background)] text-xs font-medium disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      </div>
    </div>

    <!-- Footer Copyright -->
    <footer class="bg-[var(--card)] border border-[var(--border)] rounded-2xl px-6 py-4 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[var(--muted-foreground)]">
      <div>
        Data from <a href="https://results.scorenow.co.id/Results.aspx?CId=19723&RId=340" target="_blank" rel="noopener noreferrer" class="font-semibold text-red-500 hover:text-red-400 hover:underline">https://results.scorenow.co.id</a>
      </div>
      <div class="font-medium text-[var(--foreground)]">
        &copy; 2026 <a href="https://www.instagram.com/gbudidarma/" target="_blank" rel="noopener noreferrer" class="font-bold text-red-500 hover:text-red-400 hover:underline">@gbudidarma</a> All rights reserved.
      </div>
    </footer>

  </div>

  <script>
    const THEME_PALETTES = {
      dark: {
        '--background': '#09090b',
        '--card': '#121215',
        '--foreground': '#f4f4f5',
        '--muted-foreground': '#a1a1aa',
        '--border': '#27272a',
        '--primary': '#ef4444',
        '--secondary': '#18181b'
      },
      light: {
        '--background': '#f8fafc',
        '--card': '#ffffff',
        '--foreground': '#09090b',
        '--muted-foreground': '#52525b',
        '--border': '#e4e4e7',
        '--primary': '#dc2626',
        '--secondary': '#f4f4f5'
      }
    };

    let currentTheme = 'dark';

    function setTheme(mode) {
      currentTheme = mode === 'light' ? 'light' : 'dark';
      const root = document.documentElement;
      root.classList.toggle('dark', currentTheme === 'dark');
      const palette = THEME_PALETTES[currentTheme];
      Object.entries(palette).forEach(([k, v]) => {
        root.style.setProperty(k, v);
        document.body.style.setProperty(k, v);
      });
      root.style.colorScheme = currentTheme;
      try {
        localStorage.setItem('bormar2026_theme', currentTheme);
      } catch (e) {}
      updateThemeButtons();
    }

    function updateThemeButtons() {
      const lightBtn = document.getElementById('themeLightBtn');
      const darkBtn = document.getElementById('themeDarkBtn');
      if (!lightBtn || !darkBtn) return;
      if (currentTheme === 'light') {
        lightBtn.className = 'px-3 py-1 rounded-md text-xs font-semibold transition bg-red-600 text-white shadow-sm';
        darkBtn.className = 'px-3 py-1 rounded-md text-xs font-medium transition text-[var(--muted-foreground)] hover:text-[var(--foreground)]';
      } else {
        darkBtn.className = 'px-3 py-1 rounded-md text-xs font-semibold transition bg-red-600 text-white shadow-sm';
        lightBtn.className = 'px-3 py-1 rounded-md text-xs font-medium transition text-[var(--muted-foreground)] hover:text-[var(--foreground)]';
      }
    }

    (function initTheme() {
      let saved = null;
      try {
        saved = localStorage.getItem('bormar2026_theme');
      } catch (e) {}
      if (saved === 'light' || saved === 'dark') {
        setTheme(saved);
        return;
      }
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light');
    })();

    const DASHBOARD_DATA = __DASHBOARD_JSON__;

    let selectedEventSlug = 'ALL';
    let selectedGender = 'ALL';
    let selectedViewMode = 'cards';
    let searchQuery = '';

    // Runner Table State
    let runnerQuery = '';
    let runnerEventFilter = 'ALL';
    let runnerCategoryFilter = 'ALL';
    let runnerGenderFilter = 'ALL';
    let runnerStatusFilter = 'ALL';
    let runnerRemarkFilter = 'ALL';
    let runnerPage = 1;
    let runnerPageSize = 10;
    let filteredRunners = [];
    let activeBucketFilter = null;
    let runnerSortCol = 'pos';
    let runnerSortDir = 'asc';
    const RUNNER_SORT_COLS = ['pos', 'catRank', 'bib', 'name', 'event', 'category', 'gender', 'country', 'bruto', 'pace'];

    function parseTimeSec(t) {
      if (!t) return null;
      const p = String(t).trim().split(':').map(Number);
      if (p.length === 3 && p.every(n => !isNaN(n))) return p[0] * 3600 + p[1] * 60 + p[2];
      if (p.length === 2 && p.every(n => !isNaN(n))) return p[0] * 60 + p[1];
      return null;
    }

    function updateBucketFilterBadge() {
      const badge = document.getElementById('activeBucketFilterBadge');
      if (!badge) return;
      if (!activeBucketFilter) {
        badge.classList.add('hidden');
        badge.innerHTML = '';
        return;
      }
      badge.classList.remove('hidden');
      badge.innerHTML = `
        <span>Finish Range: ${escapeHtml(activeBucketFilter.label)}</span>
        <button onclick="clearBucketFilter()" class="hover:opacity-75 font-bold" title="Clear Finish Time Range Filter">✕</button>
      `;
    }

    function selectBucketFilter(bucketIdx) {
      const { isAll, stats } = getActiveContext();
      if (isAll || !stats || !stats.buckets || !stats.buckets[bucketIdx]) return;
      const b = stats.buckets[bucketIdx];

      if (
        activeBucketFilter &&
        activeBucketFilter.eventSlug === stats.event_slug &&
        activeBucketFilter.bucketIdx === bucketIdx
      ) {
        clearBucketFilter();
        return;
      }

      const evIdx = DASHBOARD_DATA.event_lookup.findIndex(e => e.slug === stats.event_slug);
      activeBucketFilter = {
        eventSlug: stats.event_slug,
        eventIdx: evIdx,
        bucketIdx: bucketIdx,
        label: b.label,
        minSec: b.min_sec,
        maxSec: b.max_sec
      };
      if (evIdx >= 0) {
        runnerEventFilter = String(evIdx);
        document.getElementById('runnerEventSelect').value = runnerEventFilter;
      }
      runnerStatusFilter = 'FINISHED';
      document.getElementById('runnerStatusSelect').value = 'FINISHED';
      updateBucketFilterBadge();
      renderStatusAndRightPanel();
      filterRunnersList();
      document.getElementById('runnerTableSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function clearBucketFilter() {
      activeBucketFilter = null;
      updateBucketFilterBadge();
      renderStatusAndRightPanel();
      filterRunnersList();
    }

    function filterBlackFlagRunners() {
      runnerEventFilter = '0';
      runnerStatusFilter = 'BLACK_FLAG';
      runnerRemarkFilter = 'Finished Black Flag';
      document.getElementById('runnerEventSelect').value = '0';
      document.getElementById('runnerStatusSelect').value = 'BLACK_FLAG';
      document.getElementById('runnerRemarkSelect').value = 'Finished Black Flag';
      filterRunnersList();
      document.getElementById('runnerTableSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function filterBlackFlagByCheckpoint(cp) {
      runnerEventFilter = '0';
      runnerStatusFilter = 'BLACK_FLAG';
      runnerRemarkFilter = `Passed COP 3 — Stopped at ${cp} (Get Medal)`;
      document.getElementById('runnerEventSelect').value = '0';
      document.getElementById('runnerStatusSelect').value = 'BLACK_FLAG';
      document.getElementById('runnerRemarkSelect').value = `Passed COP 3 — Stopped at ${cp} (Get Medal)`;
      filterRunnersList();
      document.getElementById('runnerTableSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function filterDnfByCop(copFilter) {
      runnerEventFilter = '0';
      runnerStatusFilter = 'DNF';
      runnerRemarkFilter = copFilter || 'Did Not Pass COP';
      document.getElementById('runnerEventSelect').value = '0';
      document.getElementById('runnerStatusSelect').value = 'DNF';
      document.getElementById('runnerRemarkSelect').value = runnerRemarkFilter;
      filterRunnersList();
      document.getElementById('runnerTableSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function fmtNum(n) {
      return Number(n).toLocaleString('en-US');
    }

    function escapeHtml(str) {
      return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }

    function getActiveContext() {
      if (selectedEventSlug === 'ALL') {
        return { isAll: true, stats: DASHBOARD_DATA.overall, events: DASHBOARD_DATA.events };
      }
      const ev = DASHBOARD_DATA.events.find(e => e.event_slug === selectedEventSlug);
      return { isAll: false, stats: ev, events: [ev] };
    }

    function initRunnerFilterOptions() {
      const evOptions = `<option value="ALL">All 3 Events (${fmtNum(DASHBOARD_DATA.overall.total)})</option>` +
        DASHBOARD_DATA.event_lookup.map((ev, idx) =>
          `<option value="${idx}">${ev.name} (${ev.dist}K)</option>`
        ).join('');
      document.getElementById('runnerEventSelect').innerHTML = evOptions;

      const cats = new Set();
      DASHBOARD_DATA.runners.forEach(r => {
        if (r[7] && r[7] !== 'Unknown') {
          cats.add(r[7]);
        }
      });
      document.getElementById('runnerCategorySelect').innerHTML = `<option value="ALL">All Categories</option>` +
        Array.from(cats).map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join('');
    }

    function catRankBadgeHtml(catRank) {
      if (!catRank) return '<span class="text-[var(--muted-foreground)]">—</span>';
      if (catRank <= 3) {
        const medal = catRank === 1 ? '🥇 ' : catRank === 2 ? '🥈 ' : '🥉 ';
        return `<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-mono bg-red-500/15 text-red-400 border border-red-500/30 font-bold">${medal}#${fmtNum(catRank)}</span>`;
      }
      return `<span class="font-mono text-xs text-sky-500 font-semibold">#${fmtNum(catRank)}</span>`;
    }

    function remarkBadgeHtml(r) {
      const rem = r[15];
      const cls = r[16];
      if (!rem) return '';
      if (rem === 'Finished Black Flag') {
        return `
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold bg-sky-500/15 text-sky-400 border border-sky-500/30" title="Passed COP 3 (KM 34.5 ≤ 09:50 WIB) before 09:45 WIB Black Flag halt — Eligible for Finisher Medal">
            🏴🏅 ${escapeHtml(rem)}${cls ? ` <span class="font-mono text-[11px] opacity-85">(${escapeHtml(cls)})</span>` : ''}
          </span>
        `;
      }
      return `
        <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold bg-amber-500/15 text-amber-400 border border-amber-500/30" title="Did not pass Cut-Off Point (COP) — Official DNF">
          ❌ ${escapeHtml(rem)}${cls ? ` <span class="font-mono text-[11px] opacity-85">(${escapeHtml(cls)})</span>` : ''}
        </span>
      `;
    }

    function updateRunnerSortIcons() {
      RUNNER_SORT_COLS.forEach(col => {
        const icon = document.getElementById('sortIcon_' + col);
        if (!icon) return;
        if (runnerSortCol === col) {
          icon.textContent = runnerSortDir === 'asc' ? '▲' : '▼';
          icon.className = 'text-xs text-red-500 font-bold';
        } else {
          icon.textContent = '↕';
          icon.className = 'text-xs opacity-30 group-hover:opacity-75';
        }
      });
    }

    function sortRunnersList() {
      if (!runnerSortCol) return;
      const dir = runnerSortDir === 'desc' ? -1 : 1;

      filteredRunners.sort((a, b) => {
        switch (runnerSortCol) {
          case 'pos': {
            const isFinA = a[2] === 'FINISHED' && a[1] !== null;
            const isFinB = b[2] === 'FINISHED' && b[1] !== null;
            if (isFinA && isFinB) return (a[1] - b[1]) * dir;
            if (isFinA && !isFinB) return -1;
            if (!isFinA && isFinB) return 1;
            const isBfA = a[2] === 'BLACK_FLAG';
            const isBfB = b[2] === 'BLACK_FLAG';
            if (isBfA && !isBfB) return -1;
            if (!isBfA && isBfB) return 1;
            const sComp = (a[2] || '').localeCompare(b[2] || '');
            if (sComp !== 0) return sComp * dir;
            return (a[3] || '').localeCompare(b[3] || '', undefined, { numeric: true }) * dir;
          }
          case 'catRank': {
            const hasRkA = a[12] !== null && a[12] !== undefined && a[12] > 0;
            const hasRkB = b[12] !== null && b[12] !== undefined && b[12] > 0;
            if (hasRkA && hasRkB) return (a[12] - b[12]) * dir;
            if (hasRkA && !hasRkB) return -1;
            if (!hasRkA && hasRkB) return 1;
            return ((a[1] || 9999999) - (b[1] || 9999999)) * dir;
          }
          case 'bib':
            return (a[3] || '').localeCompare(b[3] || '', undefined, { numeric: true, sensitivity: 'base' }) * dir;
          case 'name': {
            const hasA = Boolean(a[4] && a[4].trim());
            const hasB = Boolean(b[4] && b[4].trim());
            if (hasA && hasB) return a[4].trim().localeCompare(b[4].trim()) * dir;
            if (hasA && !hasB) return -1;
            if (!hasA && hasB) return 1;
            return 0;
          }
          case 'event': {
            const evA = DASHBOARD_DATA.event_lookup[a[0]] ? DASHBOARD_DATA.event_lookup[a[0]].name : '';
            const evB = DASHBOARD_DATA.event_lookup[b[0]] ? DASHBOARD_DATA.event_lookup[b[0]].name : '';
            const c = evA.localeCompare(evB);
            if (c !== 0) return c * dir;
            return ((a[1] || 9999999) - (b[1] || 9999999)) * dir;
          }
          case 'category': {
            const hasA = Boolean(a[7] && a[7] !== 'Unknown');
            const hasB = Boolean(b[7] && b[7] !== 'Unknown');
            if (hasA && hasB) return a[7].localeCompare(b[7]) * dir;
            if (hasA && !hasB) return -1;
            if (!hasA && hasB) return 1;
            return 0;
          }
          case 'gender':
            return (a[8] || '').localeCompare(b[8] || '') * dir;
          case 'country': {
            const hasA = Boolean(a[9] && a[9] !== '-' && a[9] !== 'Unknown');
            const hasB = Boolean(b[9] && b[9] !== '-' && b[9] !== 'Unknown');
            if (hasA && hasB) return a[9].localeCompare(b[9]) * dir;
            if (hasA && !hasB) return -1;
            if (!hasA && hasB) return 1;
            return 0;
          }
          case 'bruto': {
            const secA = parseTimeSec(a[5]);
            const secB = parseTimeSec(b[5]);
            const hasA = secA !== null && a[2] === 'FINISHED';
            const hasB = secB !== null && b[2] === 'FINISHED';
            if (hasA && hasB) return (secA - secB) * dir;
            if (hasA && !hasB) return -1;
            if (!hasA && hasB) return 1;
            return (a[3] || '').localeCompare(b[3] || '', undefined, { numeric: true }) * dir;
          }
          case 'pace': {
            const pStrA = a[14] || a[6] || '';
            const pStrB = b[14] || b[6] || '';
            const secA = parseTimeSec(pStrA);
            const secB = parseTimeSec(pStrB);
            const hasA = secA !== null && a[2] === 'FINISHED';
            const hasB = secB !== null && b[2] === 'FINISHED';
            if (hasA && hasB) return (secA - secB) * dir;
            if (hasA && !hasB) return -1;
            if (!hasA && hasB) return 1;
            return (a[3] || '').localeCompare(b[3] || '', undefined, { numeric: true }) * dir;
          }
          default:
            return 0;
        }
      });
    }

    function setRunnerSort(col) {
      if (runnerSortCol === col) {
        runnerSortDir = runnerSortDir === 'asc' ? 'desc' : 'asc';
      } else {
        runnerSortCol = col;
        runnerSortDir = 'asc';
      }
      sortRunnersList();
      runnerPage = 1;
      updateRunnerSortIcons();
      renderRunnerTable();
    }

    function filterRunnersList() {
      const q = runnerQuery.trim().toLowerCase();
      const evIdx = runnerEventFilter === 'ALL' ? null : Number(runnerEventFilter);

      filteredRunners = DASHBOARD_DATA.runners.filter(r => {
        if (evIdx !== null && r[0] !== evIdx) return false;
        if (runnerCategoryFilter !== 'ALL' && r[7] !== runnerCategoryFilter) return false;
        if (runnerGenderFilter !== 'ALL' && r[8] !== runnerGenderFilter) return false;
        if (runnerStatusFilter !== 'ALL') {
          if (runnerStatusFilter === 'ALL_FINISHERS') {
            if (r[2] !== 'FINISHED' && r[2] !== 'BLACK_FLAG') return false;
          } else if (r[2] !== runnerStatusFilter) {
            return false;
          }
        }
        if (runnerRemarkFilter !== 'ALL') {
          if (runnerRemarkFilter === 'Finished Black Flag') {
            if (r[15] !== 'Finished Black Flag') return false;
          } else if (runnerRemarkFilter === 'Did Not Pass COP') {
            if (r[15] !== 'Did Not Pass COP') return false;
          } else if (runnerRemarkFilter.startsWith('Missed COP') || runnerRemarkFilter === 'Early Dropout') {
            if (!(r[16] || '').startsWith(runnerRemarkFilter)) return false;
          } else if (r[16] !== runnerRemarkFilter) {
            return false;
          }
        }
        if (activeBucketFilter) {
          if (r[2] !== 'FINISHED') return false;
          if (activeBucketFilter.eventIdx >= 0 && r[0] !== activeBucketFilter.eventIdx) return false;
          const bSec = parseTimeSec(r[5]);
          if (bSec === null || bSec < activeBucketFilter.minSec || bSec > activeBucketFilter.maxSec) return false;
        }
        if (q) {
          const bib = (r[3] || '').toLowerCase();
          const name = (r[4] || '').toLowerCase();
          const country = (r[9] || '').toLowerCase();
          const rem = (r[15] || '').toLowerCase();
          const cls = (r[16] || '').toLowerCase();
          if (!bib.includes(q) && !name.includes(q) && !country.includes(q) && !rem.includes(q) && !cls.includes(q)) return false;
        }
        return true;
      });

      sortRunnersList();
      runnerPage = 1;
      updateRunnerSortIcons();
      renderRunnerTable();
    }

    function statusBadgeHtml(pos, status, remark) {
      if (status === 'FINISHED' && pos !== null) {
        const medal = pos === 1 ? '🥇 ' : pos === 2 ? '🥈 ' : pos === 3 ? '🥉 ' : '#';
        const cls = pos <= 3
          ? 'bg-red-500/15 text-red-400 border border-red-500/30 font-bold'
          : 'bg-[var(--background)] text-[var(--foreground)] border border-[var(--border)] font-semibold';
        return `<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-mono ${cls}">${medal}${fmtNum(pos)}</span>`;
      }
      if (status === 'BLACK_FLAG' || remark === 'Finished Black Flag') {
        return `<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold border bg-sky-500/15 text-sky-400 border-sky-500/30" title="Finished Black Flag (Passed COP 3 before 09:45 WIB halt — Get Finisher Medal)">🏴🏅 BLACK FLAG</span>`;
      }
      const colors = {
        DNF: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
        CUT: 'bg-orange-500/15 text-orange-500 border-orange-500/30',
        DNS: 'bg-rose-500/15 text-rose-500 border-rose-500/30',
        DQ: 'bg-purple-500/15 text-purple-500 border-purple-500/30',
        QRY: 'bg-sky-500/15 text-sky-400 border-sky-500/30'
      };
      const c = colors[status] || 'bg-[var(--background)] text-[var(--muted-foreground)] border-[var(--border)]';
      return `<span class="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold border ${c}">${escapeHtml(status)}</span>`;
    }

    function cumSplitSecAt(splitsArr, maxIdx) {
      if (!splitsArr || maxIdx < 0 || maxIdx >= splitsArr.length) return null;
      const vals = [];
      for (let i = 0; i <= maxIdx; i++) {
        vals.push(parseTimeSec(splitsArr[i]));
      }
      if (vals[maxIdx] === null) return null;
      let lastNull = -1;
      for (let i = 0; i <= maxIdx; i++) {
        if (vals[i] === null) lastNull = i;
      }
      let sum = 0;
      for (let i = lastNull + 1; i <= maxIdx; i++) {
        sum += vals[i] || 0;
      }
      return sum;
    }

    function secToClockWib(elapsedSec) {
      if (elapsedSec === null || elapsedSec === undefined) return '—';
      const total = (4 * 3600 + 15 * 60) + Math.round(elapsedSec);
      const h = Math.floor(total / 3600) % 24;
      const m = Math.floor((total % 3600) / 60);
      const s = total % 60;
      return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')} WIB`;
    }

    function buildMarathonCopSectionHtml(r) {
      if (r[0] !== 0) return '';
      const sp = r[10] || [];
      let lastIdx = -1;
      for (let i = 0; i < sp.length; i++) {
        if (parseTimeSec(sp[i]) !== null) lastIdx = i;
      }
      const t10 = cumSplitSecAt(sp, 0);
      const t19 = cumSplitSecAt(sp, 2);
      const t34 = cumSplitSecAt(sp, 7);
      const t35 = cumSplitSecAt(sp, 8);
      const t39 = cumSplitSecAt(sp, 9);
      const tCop3 = t34 !== null ? t34 : (t35 !== null ? t35 : t39);

      const pass1 = r[2] === 'FINISHED' || (t10 !== null && t10 <= 6600) || (t10 === null && lastIdx >= 1);
      const pass2 = r[2] === 'FINISHED' || (pass1 && ((t19 !== null && t19 <= 12000 && lastIdx >= 3) || (r[2] === 'BLACK_FLAG') || (t19 === null && lastIdx >= 3)));
      const pass3 = r[2] === 'FINISHED' || r[2] === 'BLACK_FLAG' || (lastIdx >= 7 && tCop3 !== null && tCop3 <= 20100);

      const cardCls = ok => ok
        ? 'bg-sky-500/10 border-sky-500/30 text-sky-300'
        : 'bg-amber-500/10 border-amber-500/30 text-amber-300';

      const finishCardHtml = r[2] === 'FINISHED'
        ? `<div class="p-2.5 rounded-xl border bg-red-500/10 border-red-500/30 text-xs">
             <div class="font-bold text-red-400">FINISH (42.195K • 11:00 WIB)</div>
             <div class="font-mono font-bold text-[var(--foreground)] mt-0.5">🏆 Finished (${escapeHtml(r[5])})</div>
             <div class="text-[11px] text-red-300 mt-0.5">🏅 Full 42.195K Finisher Medal</div>
           </div>`
        : r[2] === 'BLACK_FLAG'
        ? `<div class="p-2.5 rounded-xl border bg-sky-500/15 border-sky-500/40 text-xs">
             <div class="font-bold text-sky-400">BLACK FLAG HALT (09:45 WIB)</div>
             <div class="font-mono font-bold text-[var(--foreground)] mt-0.5">🏴🏅 Finished Black Flag</div>
             <div class="text-[11px] text-sky-300 mt-0.5">Passed All COPs → Get Finisher Medal</div>
           </div>`
        : `<div class="p-2.5 rounded-xl border bg-amber-500/10 border-amber-500/30 text-xs">
             <div class="font-bold text-amber-400">OUTCOME (COT 11:00 WIB)</div>
             <div class="font-mono font-bold text-amber-300 mt-0.5">❌ ${escapeHtml(r[2])} (${escapeHtml(r[16] || 'Missed COP')})</div>
             <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">Did Not Pass COP → No Finisher Medal</div>
           </div>`;

      return `
        <div>
          <div class="text-xs font-semibold text-[var(--muted-foreground)] mb-2">Official Cut-Off Points (COP) Verification &amp; Medal Eligibility (Start: 04:15 WIB)</div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            <div class="p-2.5 rounded-xl border ${cardCls(pass1)} text-xs">
              <div class="font-bold">COP 1 (KM 10 • Closes 06:05 WIB)</div>
              <div class="font-mono font-bold text-[var(--foreground)] mt-0.5">${pass1 ? '✓ Passed' : '✕ Missed'} ${t10 !== null ? `@ ${secToClockWib(t10)}` : ''}</div>
              <div class="text-[11px] opacity-80 mt-0.5">Max Elapsed: 01:50:00 (1h 35m W4)</div>
            </div>
            <div class="p-2.5 rounded-xl border ${cardCls(pass2)} text-xs">
              <div class="font-bold">COP 2 (KM 20 • Closes 07:35 WIB)</div>
              <div class="font-mono font-bold text-[var(--foreground)] mt-0.5">${pass2 ? '✓ Passed' : '✕ Missed / Cut Off'} ${t19 !== null ? `@ ${secToClockWib(t19)}` : ''}</div>
              <div class="text-[11px] opacity-80 mt-0.5">Max Elapsed: 03:20:00 (3h 05m W4)</div>
            </div>
            <div class="p-2.5 rounded-xl border ${cardCls(pass3)} text-xs">
              <div class="font-bold">COP 3 (KM 34.5 • Closes 09:50 WIB)</div>
              <div class="font-mono font-bold text-[var(--foreground)] mt-0.5">${pass3 ? '✓ Passed' : '✕ Missed'} ${tCop3 !== null ? `@ ${secToClockWib(tCop3)}` : ''}</div>
              <div class="text-[11px] opacity-80 mt-0.5">Max Elapsed: 05:35:00 (5h 20m W4)</div>
            </div>
            ${finishCardHtml}
          </div>
        </div>
      `;
    }

    function showRunnerDetail(idxInFiltered) {
      const r = filteredRunners[idxInFiltered];
      if (!r) return;
      const ev = DASHBOARD_DATA.event_lookup[r[0]];
      const drawer = document.getElementById('runnerDetailDrawer');
      drawer.classList.remove('hidden');

      const splitsHtml = ev.splits.map((label, sIdx) => {
        const val = r[10][sIdx] || '—';
        return `
          <div class="p-2.5 rounded-xl bg-[var(--card)] border border-[var(--border)] text-center">
            <div class="text-xs text-[var(--muted-foreground)] font-medium">${escapeHtml(label)}</div>
            <div class="text-sm font-mono font-bold text-[var(--foreground)] mt-0.5">${escapeHtml(val)}</div>
          </div>
        `;
      }).join('');

      const blackFlagNotice = (r[2] === 'BLACK_FLAG' || r[15] === 'Finished Black Flag') ? `
        <div class="p-3 rounded-xl bg-sky-500/10 border border-sky-500/30 text-xs text-sky-300 flex flex-wrap items-center justify-between gap-2">
          <div>
            <strong>🏴🏅 Finished Black Flag (Passed COP 3 @ KM 34.5 — Get Finisher Medal):</strong> This runner passed all 3 Cut-Off Points (COP 1 @ KM 10 ≤ 06:05 WIB, COP 2 @ KM 20 ≤ 07:35 WIB, and COP 3 @ KM 34.5 ≤ 09:50 WIB: <strong>${escapeHtml(r[16] || 'Passed COP 3')}</strong>) before the race was halted by the Black Flag at 09:45 WIB due to extreme heat/WBGT.
          </div>
          <span class="px-2 py-0.5 rounded bg-sky-500/20 font-mono font-semibold text-sky-300">Raw ScoreNow Code: ${escapeHtml(r[17] || 'QRY')}</span>
        </div>
      ` : (r[0] === 0 && r[2] === 'DNF') ? `
        <div class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-300 flex flex-wrap items-center justify-between gap-2">
          <div>
            <strong>❌ Official DNF (Did Not Pass Cut-Off Point):</strong> This runner did not pass the required Cut-Off Point (<strong>${escapeHtml(r[16] || 'Missed COP')}</strong>, start clock 04:15 WIB) and is classified as DNF.
          </div>
          <span class="px-2 py-0.5 rounded bg-amber-500/20 font-mono font-semibold text-amber-300">Raw ScoreNow Code: ${escapeHtml(r[17] || 'DNF')}</span>
        </div>
      ` : '';

      const copVerificationHtml = buildMarathonCopSectionHtml(r);

      const eid = ev.eid || (r[0] + 1);
      const resultUrl = r[18] ? `https://results.scorenow.co.id/myresults.aspx?CId=19723&RId=340&EId=${eid}&AId=${r[18]}` : '';
      const bibBadgeHtml = resultUrl
        ? `<a href="${resultUrl}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-[var(--card)] border border-red-500/40 hover:border-red-500 hover:bg-red-500/10 font-mono text-xs font-semibold text-red-400 hover:underline transition" title="Open official ScoreNow result &amp; certificate page in a new tab">Bib: ${escapeHtml(r[3])} ↗</a>`
        : `<span class="px-2 py-0.5 rounded bg-[var(--card)] border border-[var(--border)] font-mono text-xs text-[var(--muted-foreground)]">Bib: ${escapeHtml(r[3])}</span>`;

      drawer.innerHTML = `
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div class="flex flex-wrap items-center gap-2">
              ${statusBadgeHtml(r[1], r[2], r[15])}
              ${r[12] ? `<span class="px-2 py-0.5 rounded bg-sky-500/10 text-sky-500 border border-sky-500/30 font-mono text-xs font-semibold">Cat Rank #${fmtNum(r[12])}</span>` : ''}
              <span class="text-base font-bold text-[var(--foreground)]">${escapeHtml(r[4] || '(No Name)')}</span>
              ${remarkBadgeHtml(r)}
              ${bibBadgeHtml}
            </div>
            <div class="text-xs text-[var(--muted-foreground)] mt-1">
              <strong>${escapeHtml(ev.name)}</strong> (${ev.dist} KM) • Category: <strong>${escapeHtml(r[7])}</strong> • Gender: <strong>${escapeHtml(r[8])}</strong> • Country: <strong>${escapeHtml(r[9])}</strong>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-4">
            <div class="text-right px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/30">
              <div class="text-xs text-red-400 font-medium">Official Finish Time</div>
              <div class="text-sm font-mono font-bold text-red-400">${escapeHtml(r[5] || (r[2] === 'BLACK_FLAG' ? 'Halted @ 09:45 (🏅 Medal)' : '—'))} ${r[6] ? `<span class="text-xs font-normal text-sky-400">(${escapeHtml(r[6])} /km)</span>` : ''}</div>
            </div>
            <button
              onclick="document.getElementById('runnerDetailDrawer').classList.add('hidden')"
              class="px-2.5 py-1 rounded-lg border border-[var(--border)] bg-[var(--card)] text-xs text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
            >
              ✕ Close
            </button>
          </div>
        </div>
        ${blackFlagNotice}
        ${copVerificationHtml}
        <div>
          <div class="text-xs font-semibold text-[var(--muted-foreground)] mb-2">Checkpoint Split Times (Segment Intervals)</div>
          <div class="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-2">${splitsHtml}</div>
        </div>
      `;
    }

    function renderRunnerTable() {
      const total = filteredRunners.length;
      const totalPages = Math.max(1, Math.ceil(total / runnerPageSize));
      if (runnerPage > totalPages) runnerPage = totalPages;

      const startIdx = (runnerPage - 1) * runnerPageSize;
      const endIdx = Math.min(startIdx + runnerPageSize, total);
      const pageSlice = filteredRunners.slice(startIdx, endIdx);

      document.getElementById('runnerResultCountBadge').textContent = `${fmtNum(total)} runners`;
      document.getElementById('runnerPaginationInfo').textContent =
        total > 0
          ? `Showing ${fmtNum(startIdx + 1)}–${fmtNum(endIdx)} of ${fmtNum(total)} matching runners`
          : 'No matching runners found';
      document.getElementById('pageIndicator').textContent = `Page ${fmtNum(runnerPage)} of ${fmtNum(totalPages)}`;
      document.getElementById('prevPageBtn').disabled = runnerPage <= 1;
      document.getElementById('nextPageBtn').disabled = runnerPage >= totalPages;

      const tbody = document.getElementById('runnerTableBody');
      if (!pageSlice.length) {
        tbody.innerHTML = `
          <tr>
            <td colspan="11" class="py-8 text-center text-sm text-[var(--muted-foreground)]">
              No runners match your search filters. Try clearing or adjusting the search terms.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = pageSlice.map((r, idx) => {
        const globalFilteredIdx = startIdx + idx;
        const ev = DASHBOARD_DATA.event_lookup[r[0]];
        const nonEmptySplits = ev.splits
          .map((lbl, i) => (r[10][i] ? `<span class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-[var(--background)] border border-[var(--border)] font-mono text-xs"><span class="text-[var(--muted-foreground)]">${escapeHtml(lbl)}:</span>${escapeHtml(r[10][i])}</span>` : ''))
          .filter(Boolean);
        const splitsPreview = nonEmptySplits.length
          ? nonEmptySplits.slice(0, 4).join(' ') + (nonEmptySplits.length > 4 ? ` <span class="text-xs text-red-400 font-medium">+${nonEmptySplits.length - 4} more</span>` : '')
          : '<span class="text-[var(--muted-foreground)]">—</span>';

        const eid = ev.eid || (r[0] + 1);
        const resultUrl = r[18] ? `https://results.scorenow.co.id/myresults.aspx?CId=19723&RId=340&EId=${eid}&AId=${r[18]}` : '';
        const bibCellHtml = resultUrl
          ? `<a href="${resultUrl}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()" class="inline-flex items-center gap-0.5 text-red-500 hover:text-red-400 hover:underline font-semibold" title="Open ScoreNow result page for Bib ${escapeHtml(r[3])}">${escapeHtml(r[3])} <span class="text-[10px] opacity-75">↗</span></a>`
          : escapeHtml(r[3]);

        return `
          <tr onclick="showRunnerDetail(${globalFilteredIdx})" class="hover:bg-[var(--background)] cursor-pointer transition">
            <td class="py-2.5 px-3 whitespace-nowrap">${statusBadgeHtml(r[1], r[2], r[15])}</td>
            <td class="py-2.5 px-2 whitespace-nowrap">${catRankBadgeHtml(r[12])}</td>
            <td class="py-2.5 px-2.5 font-mono font-semibold text-[var(--foreground)] whitespace-nowrap">${bibCellHtml}</td>
            <td class="py-2.5 px-3 font-semibold text-[var(--foreground)]">
              <div class="flex flex-wrap items-center gap-1.5">
                <span>${escapeHtml(r[4] || '—')}</span>
                ${remarkBadgeHtml(r)}
              </div>
            </td>
            <td class="py-2.5 px-2.5 whitespace-nowrap">
              <span class="text-[var(--foreground)] font-medium">${escapeHtml(ev.name)}</span>
            </td>
            <td class="py-2.5 px-2.5 text-[var(--muted-foreground)] whitespace-nowrap">${escapeHtml(r[7])}</td>
            <td class="py-2.5 px-2 whitespace-nowrap">
              <span class="px-2 py-0.5 rounded text-xs font-medium ${
                r[8] === 'Male' ? 'bg-sky-500/10 text-sky-500' : r[8] === 'Female' ? 'bg-pink-500/10 text-pink-500' : 'text-[var(--muted-foreground)]'
              }">${escapeHtml(r[8])}</span>
            </td>
            <td class="py-2.5 px-2.5 text-[var(--muted-foreground)] whitespace-nowrap">${escapeHtml(r[9])}</td>
            <td class="py-2.5 px-2.5 text-right font-mono font-bold ${r[5] ? 'text-red-400' : 'text-sky-400'} whitespace-nowrap">${escapeHtml(r[5] || (r[2] === 'BLACK_FLAG' ? 'Black Flag' : '—'))}</td>
            <td class="py-2.5 px-2.5 text-right font-mono text-sky-500 whitespace-nowrap">${r[6] ? `${escapeHtml(r[6])} /km` : '—'}</td>
            <td class="py-2.5 px-3"><div class="flex flex-wrap gap-1">${splitsPreview}</div></td>
          </tr>
        `;
      }).join('');
    }

    function renderTabs() {
      const container = document.getElementById('eventTabs');
      const tabs = [
        { slug: 'ALL', label: `All Events (${fmtNum(DASHBOARD_DATA.overall.total)})` },
        ...DASHBOARD_DATA.events.map(e => ({
          slug: e.event_slug,
          label: `${e.event_name} (${e.distance_km}K) · ${fmtNum(e.total)}`
        }))
      ];
      container.innerHTML = tabs.map(t => {
        const active = t.slug === selectedEventSlug;
        return `
          <button
            onclick="selectEvent('${t.slug}')"
            class="px-3.5 py-2 rounded-xl text-xs font-semibold transition border ${
              active
                ? 'bg-red-600 text-white border-red-600 shadow-sm'
                : 'bg-[var(--background)] text-[var(--foreground)] border-[var(--border)] hover:border-red-500/50'
            }"
          >
            ${t.label}
          </button>
        `;
      }).join('');
    }

    function renderKPIs() {
      const { isAll, stats } = getActiveContext();
      const grid = document.getElementById('kpiGrid');
      const hasBf = stats.black_flag > 0;

      const cards = [
        {
          title: hasBf ? 'Total Finishers (Incl. Black Flag)' : 'Finish Rate (FINISHED)',
          value: `${stats.finished_plus_bf_pct}%`,
          sub: hasBf
            ? `${fmtNum(stats.finished_plus_bf)} of ${fmtNum(stats.total)} (${fmtNum(stats.finished)} Full + ${fmtNum(stats.black_flag)} Black Flag)`
            : `${fmtNum(stats.finished)} of ${fmtNum(stats.total)} runners`,
          badge: hasBf ? `Full 42K: ${stats.finished_pct}%` : 'Official Finishers',
          color: 'text-red-400',
          barColor: 'bg-red-500',
          pct: stats.finished_plus_bf_pct
        },
        {
          title: '🏴🏅 Finished Black Flag (Medal)',
          value: `${stats.black_flag_pct}%`,
          sub: hasBf
            ? `${fmtNum(stats.black_flag)} passed COP 3 (KM 34.5 ≤ 09:50 WIB) → get medals`
            : 'No Black Flag halt (Finished before 09:45)',
          badge: hasBf ? 'Passed COP 3' : 'Concluded',
          color: 'text-sky-400',
          barColor: 'bg-sky-500',
          pct: stats.black_flag_pct
        },
        {
          title: 'Did Not Finish (Missed COP)',
          value: `${stats.dnf_pct}%`,
          sub: `${fmtNum(stats.dnf)} missed COP / DNF (${fmtNum(stats.dq)} DQ)`,
          badge: `DQ: ${stats.dq_pct}%`,
          color: 'text-amber-500',
          barColor: 'bg-amber-500',
          pct: stats.dnf_pct
        },
        {
          title: 'Did Not Start (DNS)',
          value: `${stats.dns_pct}%`,
          sub: `${fmtNum(stats.dns)} registered no-shows`,
          badge: 'Pre-race attrition',
          color: 'text-rose-500',
          barColor: 'bg-rose-500',
          pct: stats.dns_pct
        },
        {
          title: isAll ? 'Average Pace (Full Finishers)' : 'Avg Finish Time & Pace',
          value: isAll ? stats.avg_pace : stats.avg_time,
          sub: isAll ? `Median Pace: ${stats.median_pace} (${fmtNum(stats.finished)} timed)` : `Avg Pace: ${stats.avg_pace} • Best: ${stats.best_time}`,
          badge: isAll ? 'BORMAR 2026' : `${stats.distance_km} KM`,
          color: 'text-indigo-500',
          barColor: 'bg-indigo-500',
          pct: 100
        }
      ];

      grid.innerHTML = cards.map(c => `
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-2xl p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div class="flex items-center justify-between gap-2">
              <span class="text-xs font-medium text-[var(--muted-foreground)]">${c.title}</span>
              <span class="text-xs px-2 py-0.5 rounded-md bg-[var(--background)] border border-[var(--border)] text-[var(--muted-foreground)]">${c.badge}</span>
            </div>
            <div class="text-2xl font-bold mt-2 ${c.color}">${c.value}</div>
            <div class="text-xs text-[var(--muted-foreground)] mt-1">${c.sub}</div>
          </div>
          <div class="w-full h-1.5 bg-[var(--background)] rounded-full overflow-hidden mt-3">
            <div class="h-full ${c.barColor} rounded-full" style="width: ${Math.min(100, Math.max(4, c.pct))}%"></div>
          </div>
        </div>
      `).join('');
    }

    function renderStatusAndRightPanel() {
      const { isAll, stats } = getActiveContext();
      const statusVisual = document.getElementById('statusVisual');
      const paceGenderCards = document.getElementById('paceGenderCards');

      const segments = [
        { label: 'Finished (Full Distance)', count: stats.finished, pct: stats.finished_pct, color: 'bg-red-500', dot: 'bg-red-500' },
      ];
      if (stats.black_flag > 0) {
        segments.push({ label: '🏴 Finished Black Flag (09:45 Halt)', count: stats.black_flag, pct: stats.black_flag_pct, color: 'bg-sky-500', dot: 'bg-sky-500' });
      }
      segments.push(
        { label: 'DNF (Stopped before Halt)', count: stats.dnf, pct: stats.dnf_pct, color: 'bg-amber-500', dot: 'bg-amber-500' },
        { label: 'DNS (Did Not Start)', count: stats.dns, pct: stats.dns_pct, color: 'bg-rose-500', dot: 'bg-rose-500' },
      );
      if (stats.dq > 0) {
        segments.push({ label: 'DQ (Disqualified)', count: stats.dq, pct: stats.dq_pct, color: 'bg-purple-500', dot: 'bg-purple-500' });
      }

      statusVisual.innerHTML = `
        <div class="w-full h-4 rounded-xl overflow-hidden flex bg-[var(--background)] border border-[var(--border)]">
          ${segments.map(s => `<div class="${s.color} h-full" style="width:${s.pct}%" title="${s.label}: ${s.pct}% (${fmtNum(s.count)})"></div>`).join('')}
        </div>
        <div class="space-y-2.5">
          ${segments.map(s => `
            <div class="flex items-center justify-between text-xs">
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full ${s.dot}"></span>
                <span class="font-medium text-[var(--foreground)]">${s.label}</span>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-[var(--muted-foreground)]">${fmtNum(s.count)} runners</span>
                <span class="font-semibold text-[var(--foreground)] w-14 text-right">${s.pct}%</span>
              </div>
            </div>
          `).join('')}
        </div>
      `;

      if (isAll) {
        paceGenderCards.innerHTML = `
          <div class="p-3 rounded-xl bg-[var(--background)] border border-[var(--border)]">
            <div class="text-xs text-[var(--muted-foreground)]">Total Finishers (Full + Black Flag)</div>
            <div class="text-base font-bold text-red-400 mt-0.5">${fmtNum(stats.finished_plus_bf)} (${stats.finished_plus_bf_pct}%)</div>
            <div class="text-xs text-[var(--muted-foreground)]">${fmtNum(stats.finished)} Full + ${fmtNum(stats.black_flag)} Black Flag</div>
          </div>
          <div class="p-3 rounded-xl bg-[var(--background)] border border-[var(--border)]">
            <div class="text-xs text-[var(--muted-foreground)]">Overall Mean Pace</div>
            <div class="text-base font-bold text-sky-500 mt-0.5">${stats.avg_pace}</div>
            <div class="text-xs text-[var(--muted-foreground)]">Median: ${stats.median_pace}</div>
          </div>
        `;
      } else {
        paceGenderCards.innerHTML = `
          <div class="p-3 rounded-xl bg-[var(--background)] border border-[var(--border)]">
            <div class="text-xs text-[var(--muted-foreground)]">Male Avg Pace (Full Distance)</div>
            <div class="text-base font-bold text-sky-500 mt-0.5">${stats.male_avg_pace}</div>
            <div class="text-xs text-[var(--muted-foreground)]">${fmtNum(stats.male_finishers)} Male full finishers</div>
          </div>
          <div class="p-3 rounded-xl bg-[var(--background)] border border-[var(--border)]">
            <div class="text-xs text-[var(--muted-foreground)]">Female Avg Pace (Full Distance)</div>
            <div class="text-base font-bold text-pink-500 mt-0.5">${stats.female_avg_pace}</div>
            <div class="text-xs text-[var(--muted-foreground)]">${fmtNum(stats.female_finishers)} Female full finishers</div>
          </div>
        `;
      }

      const rightTitle = document.getElementById('rightPanelTitle');
      const rightSubtitle = document.getElementById('rightPanelSubtitle');
      const rightContent = document.getElementById('rightPanelContent');

      if (isAll) {
        rightTitle.textContent = 'Event-by-Event Finish, Black Flag, DNF, DNS & Pace Comparison';
        rightSubtitle.textContent = 'Click any event row to filter the dashboard to that specific race';
        rightContent.innerHTML = `
          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-[var(--border)] text-xs text-[var(--muted-foreground)]">
                  <th class="py-2.5 pr-3 font-semibold">Event</th>
                  <th class="py-2.5 px-2 font-semibold text-right">Total</th>
                  <th class="py-2.5 px-2 font-semibold text-right text-red-400">Full Finish</th>
                  <th class="py-2.5 px-2 font-semibold text-right text-sky-400">🏴 Black Flag</th>
                  <th class="py-2.5 px-2 font-semibold text-right text-red-300">Total Finish %</th>
                  <th class="py-2.5 px-2 font-semibold text-right text-amber-500">DNF %</th>
                  <th class="py-2.5 px-2 font-semibold text-right text-rose-500">DNS %</th>
                  <th class="py-2.5 px-2 font-semibold text-right text-red-400">Avg Time</th>
                  <th class="py-2.5 pl-2 font-semibold text-right text-sky-500">Avg Pace</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--border)] text-xs">
                ${DASHBOARD_DATA.events.map(ev => `
                  <tr onclick="selectEvent('${ev.event_slug}')" class="hover:bg-[var(--background)] cursor-pointer transition">
                    <td class="py-3 pr-3">
                      <div class="font-semibold text-[var(--foreground)]">${ev.event_name}</div>
                      <div class="text-xs text-[var(--muted-foreground)]">${ev.distance_km} KM</div>
                    </td>
                    <td class="py-3 px-2 text-right font-medium">${fmtNum(ev.total)}</td>
                    <td class="py-3 px-2 text-right">
                      <span class="font-semibold text-red-400">${ev.finished_pct}%</span>
                      <div class="text-xs text-[var(--muted-foreground)]">${fmtNum(ev.finished)}</div>
                    </td>
                    <td class="py-3 px-2 text-right">
                      <span class="font-semibold text-sky-400">${ev.black_flag_pct}%</span>
                      <div class="text-xs text-[var(--muted-foreground)]">${fmtNum(ev.black_flag)}</div>
                    </td>
                    <td class="py-3 px-2 text-right">
                      <span class="font-bold text-red-300">${ev.finished_plus_bf_pct}%</span>
                      <div class="text-xs text-[var(--muted-foreground)]">${fmtNum(ev.finished_plus_bf)}</div>
                    </td>
                    <td class="py-3 px-2 text-right">
                      <span class="font-semibold text-amber-500">${ev.dnf_pct}%</span>
                      <div class="text-xs text-[var(--muted-foreground)]">${fmtNum(ev.dnf)}</div>
                    </td>
                    <td class="py-3 px-2 text-right">
                      <span class="font-semibold text-rose-500">${ev.dns_pct}%</span>
                      <div class="text-xs text-[var(--muted-foreground)]">${fmtNum(ev.dns)}</div>
                    </td>
                    <td class="py-3 px-2 text-right font-mono font-bold text-red-400">${ev.avg_time}</td>
                    <td class="py-3 pl-2 text-right font-mono font-semibold text-sky-500">${ev.avg_pace}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `;
      } else {
        rightTitle.textContent = `${stats.event_name} — Finish Time & Pace Distribution`;
        rightSubtitle.textContent = `Official COT: ${stats.cot_label} (${stats.step_label}) • Click any bar to filter runners in that finish time range`;
        const maxBucket = Math.max(...stats.buckets.map(b => b.count), 1);
        const hasActiveBar = activeBucketFilter && activeBucketFilter.eventSlug === stats.event_slug;
        const bfRowHtml = stats.black_flag > 0 ? `
          <div
            onclick="filterBlackFlagRunners()"
            class="grid grid-cols-12 items-center gap-2 text-xs cursor-pointer transition select-none bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/30 rounded-lg px-2 py-1.5 mt-2"
            title="Click to view all ${fmtNum(stats.black_flag)} Finished Black Flag runners who passed COP 3 (get medals)"
          >
            <div class="col-span-4 font-mono font-bold text-sky-400">🏴🏅 Black Flag (09:45 WIB)</div>
            <div class="col-span-5 text-sky-300 text-[11px]">Passed COP 3 @ KM 34.5 → Get Medal</div>
            <div class="col-span-3 text-right">
              <span class="font-bold text-sky-400">${fmtNum(stats.black_flag)}</span>
              <span class="text-sky-300/80 ml-1">(${stats.black_flag_pct}%)</span>
            </div>
          </div>
        ` : '';
        rightContent.innerHTML = `
          ${hasActiveBar ? `
            <div class="flex items-center justify-between px-3 py-1.5 mb-2 rounded-lg bg-red-500/10 border border-red-500/30 text-xs">
              <span class="font-medium text-red-400">Active Filter: <strong>${escapeHtml(activeBucketFilter.label)}</strong></span>
              <button onclick="clearBucketFilter()" class="px-2 py-0.5 rounded bg-[var(--card)] border border-[var(--border)] text-[var(--foreground)] font-medium hover:opacity-80">Clear Filter ✕</button>
            </div>
          ` : ''}
          <div class="space-y-1.5">
            ${stats.buckets.map((b, bIdx) => {
              const isSelected = hasActiveBar && activeBucketFilter.bucketIdx === bIdx;
              const rowCls = isSelected
                ? 'bg-red-500/15 ring-1 ring-red-500 rounded-lg px-2 py-1'
                : 'hover:bg-[var(--background)] rounded-lg px-2 py-1';
              const barColor = b.is_over_cot
                ? (isSelected ? 'bg-amber-500' : 'bg-amber-500/80')
                : (isSelected ? 'bg-red-500' : 'bg-red-500/80');
              const labelColor = b.is_over_cot ? 'text-amber-500 font-semibold' : 'text-[var(--foreground)] font-medium';
              return `
                <div
                  onclick="selectBucketFilter(${bIdx})"
                  class="grid grid-cols-12 items-center gap-2 text-xs cursor-pointer transition select-none ${rowCls}"
                  title="Click to filter runners in ${b.label} (${b.pace_label}): ${fmtNum(b.count)} runners (${b.pct}%)"
                >
                  <div class="col-span-3 font-mono ${labelColor}">${escapeHtml(b.label)}</div>
                  <div class="col-span-6">
                    <div class="w-full h-4 bg-[var(--background)] rounded-lg overflow-hidden border border-[var(--border)]">
                      <div class="h-full ${barColor} rounded-lg transition-all" style="width: ${b.count > 0 ? Math.max(2, (b.count / maxBucket) * 100) : 0}%"></div>
                    </div>
                  </div>
                  <div class="col-span-3 text-right">
                    <span class="font-semibold text-[var(--foreground)]">${fmtNum(b.count)}</span>
                    <span class="text-[var(--muted-foreground)] ml-1">(${b.pct}%)</span>
                  </div>
                </div>
              `;
            }).join('')}
            ${bfRowHtml}
          </div>
        `;
      }
    }

    let collapsedWinnerEvents = new Set();

    function toggleWinnerEvent(slug) {
      if (collapsedWinnerEvents.has(slug)) {
        collapsedWinnerEvents.delete(slug);
      } else {
        collapsedWinnerEvents.add(slug);
      }
      renderWinners();
    }

    function expandAllWinnerEvents() {
      collapsedWinnerEvents.clear();
      renderWinners();
    }

    function collapseAllWinnerEvents() {
      DASHBOARD_DATA.events.forEach(ev => collapsedWinnerEvents.add(ev.event_slug));
      renderWinners();
    }

    function renderWinners() {
      const { events } = getActiveContext();
      const container = document.getElementById('winnersContainer');
      const q = searchQuery.trim().toLowerCase();

      document.querySelectorAll('.gender-btn').forEach(btn => {
        const active = btn.dataset.gender === selectedGender;
        btn.className = `gender-btn px-3 py-1 rounded-md text-xs font-medium transition ${
          active ? 'bg-red-600 text-white shadow-sm' : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
        }`;
      });
      document.querySelectorAll('.mode-btn').forEach(btn => {
        const active = btn.dataset.mode === selectedViewMode;
        btn.className = `mode-btn px-3 py-1 rounded-md text-xs font-medium transition ${
          active ? 'bg-red-600 text-white shadow-sm' : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
        }`;
      });

      const sectionsHtml = events.map(ev => {
        const isCollapsed = collapsedWinnerEvents.has(ev.event_slug);
        const filteredCats = ev.categories.filter(c => {
          if (selectedGender !== 'ALL' && c.gender !== selectedGender) return false;
          if (!q) return true;
          const matchCat = c.category.toLowerCase().includes(q) || c.gender.toLowerCase().includes(q);
          const matchRunner = c.podium.some(
            p =>
              p.name.toLowerCase().includes(q) ||
              p.bib_no.toLowerCase().includes(q) ||
              p.country.toLowerCase().includes(q)
          );
          return matchCat || matchRunner;
        });

        if (!filteredCats.length) return '';

        if (selectedViewMode === 'table') {
          return `
            <div class="space-y-3 mb-5 last:mb-0">
              <div
                onclick="toggleWinnerEvent('${ev.event_slug}')"
                class="flex flex-wrap items-center justify-between gap-2 bg-[var(--background)] px-4 py-2.5 rounded-xl border border-[var(--border)] hover:border-red-500/40 cursor-pointer select-none transition"
              >
                <div class="flex items-center gap-2.5">
                  <span class="inline-flex items-center justify-center w-5 h-5 rounded bg-[var(--card)] border border-[var(--border)] text-xs font-bold text-[var(--foreground)]">${isCollapsed ? '▶' : '▼'}</span>
                  <span class="text-sm font-bold text-[var(--foreground)]">${ev.event_name}</span>
                  <span class="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-400 font-semibold">${ev.distance_km} KM</span>
                  <span class="text-xs text-[var(--muted-foreground)]">(${filteredCats.length} categories)</span>
                </div>
                <div class="flex items-center gap-3 text-xs text-[var(--muted-foreground)]">
                  <span>Full Finish: <strong class="text-red-400">${ev.finished_pct}%</strong>${ev.black_flag > 0 ? ` • 🏴 Black Flag: <strong class="text-sky-400">${ev.black_flag_pct}%</strong>` : ''} • Avg Pace: <strong class="text-sky-500">${ev.avg_pace}</strong></span>
                  <span class="px-2 py-0.5 rounded border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)] font-medium">${isCollapsed ? 'Expand' : 'Collapse'}</span>
                </div>
              </div>
              <div class="${isCollapsed ? 'hidden' : 'overflow-x-auto'}">
                <table class="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr class="border-b border-[var(--border)] text-[var(--muted-foreground)]">
                      <th class="py-2.5 px-3 font-semibold">Category</th>
                      <th class="py-2.5 px-2 font-semibold">Gender</th>
                      <th class="py-2.5 px-2 font-semibold">#1 Winner Name</th>
                      <th class="py-2.5 px-2 font-semibold">Bib No</th>
                      <th class="py-2.5 px-2 font-semibold">Country</th>
                      <th class="py-2.5 px-2 font-semibold text-right">Finish Time</th>
                      <th class="py-2.5 px-2 font-semibold text-right">Winner Pace</th>
                      <th class="py-2.5 px-2 font-semibold text-right">Cat Finishers</th>
                      <th class="py-2.5 px-3 font-semibold text-right">Cat Avg Pace</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-[var(--border)]">
                    ${filteredCats.map(c => {
                      const w = c.winner;
                      return `
                        <tr class="hover:bg-[var(--background)]">
                          <td class="py-2.5 px-3 font-semibold text-[var(--foreground)]">${c.category}</td>
                          <td class="py-2.5 px-2">
                            <span class="px-2 py-0.5 rounded text-xs font-medium ${
                              c.gender === 'Male' ? 'bg-sky-500/10 text-sky-500' : 'bg-pink-500/10 text-pink-500'
                            }">${c.gender}</span>
                          </td>
                          <td class="py-2.5 px-2 font-bold text-[var(--foreground)]">🏆 ${w ? w.name : '-'}</td>
                          <td class="py-2.5 px-2 font-mono text-[var(--muted-foreground)]">${w ? (w.result_url ? `<a href="${w.result_url}" target="_blank" rel="noopener noreferrer" class="text-red-500 hover:text-red-400 hover:underline font-semibold" title="Open ScoreNow result page">${w.bib_no} ↗</a>` : w.bib_no) : '-'}</td>
                          <td class="py-2.5 px-2 text-[var(--muted-foreground)]">${w ? w.country : '-'}</td>
                          <td class="py-2.5 px-2 text-right font-mono font-bold text-red-400">${w ? w.time : '-'}</td>
                          <td class="py-2.5 px-2 text-right font-mono text-sky-500">${w ? w.pace : '-'}</td>
                          <td class="py-2.5 px-2 text-right text-[var(--muted-foreground)]">${fmtNum(c.finishers_count)}${c.black_flag_count > 0 ? ` (+${fmtNum(c.black_flag_count)} 🏴)` : ''} / ${fmtNum(c.total_entered)}</td>
                          <td class="py-2.5 px-3 text-right font-mono text-[var(--muted-foreground)]">${c.avg_pace}</td>
                        </tr>
                      `;
                    }).join('')}
                  </tbody>
                </table>
              </div>
            </div>
          `;
        }

        return `
          <div class="space-y-4 mb-5 last:mb-0">
            <div
              onclick="toggleWinnerEvent('${ev.event_slug}')"
              class="flex flex-wrap items-center justify-between gap-2 bg-[var(--background)] px-4 py-3 rounded-xl border border-[var(--border)] hover:border-red-500/40 cursor-pointer select-none transition"
            >
              <div class="flex items-center gap-2.5">
                <span class="inline-flex items-center justify-center w-5 h-5 rounded bg-[var(--card)] border border-[var(--border)] text-xs font-bold text-[var(--foreground)]">${isCollapsed ? '▶' : '▼'}</span>
                <span class="text-base font-bold text-[var(--foreground)]">${ev.event_name}</span>
                <span class="text-xs px-2.5 py-0.5 rounded-full bg-red-500/10 text-red-400 font-semibold">${ev.distance_km} KM</span>
                <span class="text-xs text-[var(--muted-foreground)]">(${filteredCats.length} categories)</span>
              </div>
              <div class="flex flex-wrap items-center gap-4 text-xs text-[var(--muted-foreground)]">
                <span>Full Finish: <strong class="text-red-400">${ev.finished_pct}%</strong> (${fmtNum(ev.finished)})</span>
                ${ev.black_flag > 0 ? `<span>🏴 Black Flag: <strong class="text-sky-400">${ev.black_flag_pct}%</strong> (${fmtNum(ev.black_flag)})</span>` : ''}
                <span>DNF: <strong class="text-amber-500">${ev.dnf_pct}%</strong> (${fmtNum(ev.dnf)})</span>
                <span>DNS: <strong class="text-rose-500">${ev.dns_pct}%</strong> (${fmtNum(ev.dns)})</span>
                <span>Avg Pace: <strong class="text-sky-500">${ev.avg_pace}</strong></span>
                <span class="px-2.5 py-0.5 rounded-md border border-[var(--border)] bg-[var(--card)] text-[var(--foreground)] font-medium">${isCollapsed ? 'Expand' : 'Collapse'}</span>
              </div>
            </div>
            <div class="${isCollapsed ? 'hidden' : 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4'}">
              ${filteredCats.map(c => `
                <div class="rounded-xl border border-[var(--border)] bg-[var(--background)] p-4 flex flex-col justify-between space-y-3">
                  <div class="flex items-start justify-between gap-2 border-b border-[var(--border)] pb-2.5">
                    <div>
                      <div class="flex items-center gap-2">
                        <span class="text-xs font-bold text-[var(--foreground)]">${c.category}</span>
                        <span class="px-2 py-0.5 rounded text-xs font-semibold ${
                          c.gender === 'Male' ? 'bg-sky-500/10 text-sky-500' : 'bg-pink-500/10 text-pink-500'
                        }">${c.gender}</span>
                      </div>
                      <div class="text-xs text-[var(--muted-foreground)] mt-0.5">
                        ${fmtNum(c.finishers_count)} full finishers${c.black_flag_count > 0 ? ` + <span class="text-sky-400 font-medium">${fmtNum(c.black_flag_count)} Black Flag</span>` : ''} (${c.finish_plus_bf_pct}% of ${fmtNum(c.total_entered)})
                      </div>
                    </div>
                    <div class="text-right">
                      <div class="text-xs text-[var(--muted-foreground)]">Cat Avg Pace</div>
                      <div class="text-xs font-mono font-semibold text-sky-500">${c.avg_pace}</div>
                    </div>
                  </div>
                  <div class="space-y-2">
                    ${c.podium.map((p, idx) => {
                      const medals = ['🥇 1st', '🥈 2nd', '🥉 3rd'];
                      const highlight = idx === 0 ? 'bg-red-500/10 border-red-500/30' : 'bg-[var(--card)] border-[var(--border)]';
                      return `
                        <div class="p-2.5 rounded-lg border ${highlight} flex items-center justify-between gap-2 text-xs">
                          <div class="min-w-0">
                            <div class="flex items-center gap-1.5">
                              <span class="font-bold text-[var(--foreground)]">${medals[idx] || '#' + p.category_rank}</span>
                              <span class="font-semibold text-[var(--foreground)] truncate">${p.name}</span>
                            </div>
                            <div class="text-xs text-[var(--muted-foreground)] mt-0.5">
                              Bib: ${p.result_url ? `<a href="${p.result_url}" target="_blank" rel="noopener noreferrer" class="font-mono font-semibold text-red-500 hover:text-red-400 hover:underline" title="Open ScoreNow result page">${p.bib_no} ↗</a>` : `<span class="font-mono">${p.bib_no}</span>`} • ${p.country} ${p.overall_pos ? '• Overall #' + p.overall_pos : ''}
                            </div>
                          </div>
                          <div class="text-right shrink-0 space-y-0.5">
                            <div class="font-mono text-xs font-bold text-red-400">${p.time}</div>
                            <div class="font-mono text-xs text-sky-500">${p.pace}</div>
                          </div>
                        </div>
                      `;
                    }).join('')}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      }).join('');

      container.innerHTML = sectionsHtml || `
        <div class="text-center py-8 text-sm text-[var(--muted-foreground)]">
          No category winners match your current filter criteria.
        </div>
      `;
    }

    function selectEvent(slug) {
      selectedEventSlug = slug;
      activeBucketFilter = null;
      updateBucketFilterBadge();
      if (slug === 'ALL') {
        runnerEventFilter = 'ALL';
      } else {
        const idx = DASHBOARD_DATA.event_lookup.findIndex(e => e.slug === slug);
        const val = idx >= 0 ? String(idx) : 'ALL';
        runnerEventFilter = val;
      }
      document.getElementById('runnerEventSelect').value = runnerEventFilter;
      renderAll();
      filterRunnersList();
    }

    const PIE_COLORS = [
      '#0ea5e9', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4',
      '#f97316', '#6366f1', '#10b981', '#84cc16', '#64748b'
    ];

    function buildPieSvg(slices, total, centerLabelTop, centerLabelBottom) {
      if (!total || !slices.length) {
        return `<div class="text-xs text-[var(--muted-foreground)] py-8 text-center">No country data</div>`;
      }
      const cx = 90, cy = 90, r = 74, innerR = 44;
      let cumAngle = -Math.PI / 2;
      const paths = slices.map((s, idx) => {
        const frac = s.count / total;
        const angle = frac * Math.PI * 2;
        const startAngle = cumAngle;
        const endAngle = cumAngle + angle;
        cumAngle = endAngle;
        const color = s.color || PIE_COLORS[idx % PIE_COLORS.length];

        if (frac >= 0.9999) {
          return `
            <circle cx="${cx}" cy="${cy}" r="${(r + innerR) / 2}" fill="none" stroke="${color}" stroke-width="${r - innerR}">
              <title>${escapeHtml(s.label)}: ${fmtNum(s.count)} (${s.pct}%)</title>
            </circle>
          `;
        }
        const x1 = cx + r * Math.cos(startAngle);
        const y1 = cy + r * Math.sin(startAngle);
        const x2 = cx + r * Math.cos(endAngle);
        const y2 = cy + r * Math.sin(endAngle);
        const ix1 = cx + innerR * Math.cos(endAngle);
        const iy1 = cy + innerR * Math.sin(endAngle);
        const ix2 = cx + innerR * Math.cos(startAngle);
        const iy2 = cy + innerR * Math.sin(startAngle);
        const largeArc = angle > Math.PI ? 1 : 0;
        const d = [
          `M ${x1.toFixed(2)} ${y1.toFixed(2)}`,
          `A ${r} ${r} 0 ${largeArc} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`,
          `L ${ix1.toFixed(2)} ${iy1.toFixed(2)}`,
          `A ${innerR} ${innerR} 0 ${largeArc} 0 ${ix2.toFixed(2)} ${iy2.toFixed(2)}`,
          'Z'
        ].join(' ');
        const clickAttr = s.clickable ? `onclick="filterByCountry('${escapeHtml(s.label)}')" class="cursor-pointer hover:opacity-85 transition"` : '';
        return `<path d="${d}" fill="${color}" stroke="var(--card)" stroke-width="1.5" ${clickAttr}><title>${escapeHtml(s.label)}: ${fmtNum(s.count)} runners (${s.pct}%)</title></path>`;
      }).join('');

      return `
        <svg viewBox="0 0 180 180" class="w-44 h-44 shrink-0 mx-auto">
          ${paths}
          <text x="${cx}" y="${cy - 4}" text-anchor="middle" fill="var(--foreground)" class="text-sm font-bold" style="font-size:14px;font-weight:700;">${escapeHtml(centerLabelTop)}</text>
          <text x="${cx}" y="${cy + 13}" text-anchor="middle" fill="var(--muted-foreground)" class="text-xs" style="font-size:10px;">${escapeHtml(centerLabelBottom)}</text>
        </svg>
      `;
    }

    function filterByCountry(countryName) {
      if (!countryName || countryName === 'Other Countries' || countryName === 'International') return;
      runnerQuery = countryName;
      document.getElementById('runnerSearchInput').value = countryName;
      filterRunnersList();
      document.getElementById('runnerSearchInput').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function renderCountryJoiners() {
      const { isAll, stats } = getActiveContext();
      const evIdx = isAll ? null : DASHBOARD_DATA.event_lookup.findIndex(e => e.slug === selectedEventSlug);
      const rows = evIdx === null
        ? DASHBOARD_DATA.runners
        : DASHBOARD_DATA.runners.filter(r => r[0] === evIdx);

      const total = rows.length;
      const counts = {};
      rows.forEach(r => {
        const c = (r[9] && r[9] !== '-') ? r[9] : 'Unknown';
        counts[c] = (counts[c] || 0) + 1;
      });

      const knownCountries = Object.entries(counts)
        .filter(([country]) => country !== 'Unknown')
        .map(([country, count]) => ({
          country,
          count,
          pct: total ? Number((count * 100 / total).toFixed(2)) : 0
        }))
        .sort((a, b) => b.count - a.count);

      const distinctCountriesCount = knownCountries.length;
      const idnCount = counts['Indonesia'] || 0;
      const intlCountries = knownCountries.filter(c => c.country !== 'Indonesia');
      const intlKnownTotal = intlCountries.reduce((acc, c) => acc + c.count, 0);
      const unknownCount = counts['Unknown'] || 0;
      const knownTotal = idnCount + intlKnownTotal;

      const idnPct = knownTotal ? (idnCount * 100 / knownTotal).toFixed(2) : '0.00';
      const intlPct = knownTotal ? (intlKnownTotal * 100 / knownTotal).toFixed(2) : '0.00';

      document.getElementById('countrySectionTitle').textContent = isAll
        ? 'Country Joiners — Participant Nationality Breakdown (All Events)'
        : `Country Joiners — ${stats.event_name}`;
      document.getElementById('countryTotalBadge').textContent = `${distinctCountriesCount} Countries • ${fmtNum(intlKnownTotal)} International (${intlPct}%)`;

      const overallSlices = [
        { label: 'Indonesia', count: idnCount, pct: idnPct, color: '#ef4444', clickable: true },
        { label: 'International', count: intlKnownTotal, pct: intlPct, color: '#0ea5e9', clickable: false }
      ].filter(s => s.count > 0);

      const topIntl = intlCountries.slice(0, 8).map((c, idx) => ({
        label: c.country,
        count: c.count,
        pct: intlKnownTotal ? (c.count * 100 / intlKnownTotal).toFixed(1) : '0.0',
        color: PIE_COLORS[(idx + 1) % PIE_COLORS.length],
        clickable: true
      }));
      const otherIntlCount = intlCountries.slice(8).reduce((acc, c) => acc + c.count, 0);
      if (otherIntlCount > 0) {
        topIntl.push({
          label: 'Other Countries',
          count: otherIntlCount,
          pct: intlKnownTotal ? (otherIntlCount * 100 / intlKnownTotal).toFixed(1) : '0.0',
          color: '#64748b',
          clickable: false
        });
      }

      const pie1Html = buildPieSvg(overallSlices, knownTotal, `${idnPct}%`, 'Indonesia');
      const pie2Html = buildPieSvg(topIntl, intlKnownTotal, fmtNum(intlKnownTotal), 'Foreign Joiners');

      const topTableRows = knownCountries.slice(0, 10).map((c, idx) => {
        const badgeColor = c.country === 'Indonesia' ? '#ef4444' : PIE_COLORS[idx % PIE_COLORS.length];
        return `
          <tr onclick="filterByCountry('${escapeHtml(c.country)}')" class="hover:bg-[var(--card)] cursor-pointer transition">
            <td class="py-1.5 px-2.5 text-xs font-mono text-[var(--muted-foreground)]">#${idx + 1}</td>
            <td class="py-1.5 px-2.5 text-xs font-semibold text-[var(--foreground)]">
              <div class="flex items-center gap-2">
                <span class="w-2.5 h-2.5 rounded-full shrink-0" style="background:${badgeColor}"></span>
                <span class="truncate">${escapeHtml(c.country)}</span>
              </div>
            </td>
            <td class="py-1.5 px-2.5 text-xs text-right font-mono font-semibold text-[var(--foreground)]">${fmtNum(c.count)}</td>
            <td class="py-1.5 px-2.5 text-xs text-right font-mono text-red-400 font-semibold">${c.pct.toFixed(2)}%</td>
          </tr>
        `;
      }).join('');

      document.getElementById('countryChartsContainer').innerHTML = `
        <!-- Left: Pie 1 (All Joiners: Indonesia vs International) -->
        <div class="lg:col-span-3 h-full bg-[var(--background)] border border-[var(--border)] rounded-xl p-5 flex flex-col justify-between">
          <div class="text-center border-b border-[var(--border)] pb-3">
            <div class="text-sm font-bold text-[var(--foreground)]">All Joiners (Domestic vs Foreign)</div>
            <div class="text-xs text-[var(--muted-foreground)] mt-0.5">${fmtNum(total)} total participants</div>
          </div>
          <div class="my-auto py-3 flex items-center justify-center">
            ${pie1Html}
          </div>
          <div class="w-full space-y-2 text-xs border-t border-[var(--border)] pt-3">
            <div onclick="filterByCountry('Indonesia')" class="flex items-center justify-between cursor-pointer hover:opacity-80">
              <span class="flex items-center gap-2 font-medium text-[var(--foreground)]"><span class="w-2.5 h-2.5 rounded-full bg-red-500 shrink-0"></span>Indonesia</span>
              <span class="font-mono font-semibold text-[var(--foreground)]">${fmtNum(idnCount)} (${idnPct}%)</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="flex items-center gap-2 font-medium text-[var(--foreground)]"><span class="w-2.5 h-2.5 rounded-full bg-sky-500 shrink-0"></span>International (${Math.max(0, distinctCountriesCount - 1)} nations)</span>
              <span class="font-mono font-semibold text-[var(--foreground)]">${fmtNum(intlKnownTotal)} (${intlPct}%)</span>
            </div>
            ${unknownCount > 0 ? `
              <div class="flex items-center justify-between text-[var(--muted-foreground)]">
                <span class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-full bg-slate-400 shrink-0"></span>Unspecified / Other</span>
                <span class="font-mono">${fmtNum(unknownCount)}</span>
              </div>
            ` : ''}
          </div>
        </div>

        <!-- Middle: Pie 2 (International Joiners by Country Pie Chart) -->
        <div class="lg:col-span-5 h-full bg-[var(--background)] border border-[var(--border)] rounded-xl p-5 flex flex-col justify-between">
          <div class="text-center border-b border-[var(--border)] pb-3">
            <div class="text-sm font-bold text-[var(--foreground)]">International Joiners Pie Chart</div>
            <div class="text-xs text-[var(--muted-foreground)] mt-0.5">Share among ${fmtNum(intlKnownTotal)} foreign runners (${Math.max(0, distinctCountriesCount - 1)} countries)</div>
          </div>
          <div class="my-auto py-3 flex flex-col sm:flex-row items-center justify-center gap-5">
            ${pie2Html}
            <div class="w-full flex-1 space-y-1.5 text-xs">
              ${topIntl.map(s => `
                <div ${s.clickable ? `onclick="filterByCountry('${escapeHtml(s.label)}')" class="flex items-center justify-between gap-2 py-0.5 px-1.5 rounded hover:bg-[var(--card)] cursor-pointer transition"` : 'class="flex items-center justify-between gap-2 py-0.5 px-1.5"'}>
                  <span class="flex items-center gap-2 min-w-0">
                    <span class="w-2.5 h-2.5 rounded-full shrink-0" style="background:${s.color}"></span>
                    <span class="font-medium text-[var(--foreground)] truncate">${escapeHtml(s.label)}</span>
                  </span>
                  <span class="font-mono font-semibold text-[var(--foreground)] whitespace-nowrap shrink-0">${fmtNum(s.count)} <span class="text-[var(--muted-foreground)]">(${s.pct}%)</span></span>
                </div>
              `).join('')}
            </div>
          </div>
          <div class="text-center text-xs text-[var(--muted-foreground)] border-t border-[var(--border)] pt-3">
            Click any slice or country name to filter runner results below
          </div>
        </div>

        <!-- Right: Top 10 Countries Table -->
        <div class="lg:col-span-4 h-full bg-[var(--background)] border border-[var(--border)] rounded-xl p-5 flex flex-col justify-between">
          <div class="flex items-center justify-between border-b border-[var(--border)] pb-3">
            <div>
              <div class="text-sm font-bold text-[var(--foreground)]">Top 10 Countries by Runner Count</div>
              <div class="text-xs text-[var(--muted-foreground)] mt-0.5">Click any country row to search</div>
            </div>
          </div>
          <div class="overflow-x-auto my-auto py-1">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-[var(--border)] text-xs text-[var(--muted-foreground)]">
                  <th class="py-1.5 px-2.5 font-semibold">Rank</th>
                  <th class="py-1.5 px-2.5 font-semibold">Country</th>
                  <th class="py-1.5 px-2.5 font-semibold text-right">Runners</th>
                  <th class="py-1.5 px-2.5 font-semibold text-right">Share %</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-[var(--border)]">
                ${topTableRows}
              </tbody>
            </table>
          </div>
        </div>
      `;
    }

    function renderAll() {
      renderTabs();
      renderKPIs();
      renderStatusAndRightPanel();
      renderCountryJoiners();
      renderWinners();
    }

    document.querySelectorAll('.gender-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        selectedGender = btn.dataset.gender;
        renderWinners();
      });
    });

    document.querySelectorAll('.mode-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        selectedViewMode = btn.dataset.mode;
        renderWinners();
      });
    });

    document.getElementById('winnerSearch').addEventListener('input', e => {
      searchQuery = e.target.value;
      renderWinners();
    });

    // Runner Table Event Listeners
    document.getElementById('runnerSearchInput').addEventListener('input', e => {
      runnerQuery = e.target.value;
      filterRunnersList();
    });
    document.getElementById('runnerEventSelect').addEventListener('change', e => {
      runnerEventFilter = e.target.value;
      if (activeBucketFilter && String(activeBucketFilter.eventIdx) !== runnerEventFilter) {
        activeBucketFilter = null;
        updateBucketFilterBadge();
        renderStatusAndRightPanel();
      }
      filterRunnersList();
    });
    document.getElementById('runnerCategorySelect').addEventListener('change', e => {
      runnerCategoryFilter = e.target.value;
      filterRunnersList();
    });
    document.getElementById('runnerGenderSelect').addEventListener('change', e => {
      runnerGenderFilter = e.target.value;
      filterRunnersList();
    });
    document.getElementById('runnerStatusSelect').addEventListener('change', e => {
      runnerStatusFilter = e.target.value;
      filterRunnersList();
    });
    document.getElementById('runnerRemarkSelect').addEventListener('change', e => {
      runnerRemarkFilter = e.target.value;
      filterRunnersList();
    });
    document.getElementById('runnerPageSizeSelect').addEventListener('change', e => {
      runnerPageSize = Number(e.target.value);
      runnerPage = 1;
      renderRunnerTable();
    });
    document.getElementById('prevPageBtn').addEventListener('click', () => {
      if (runnerPage > 1) {
        runnerPage--;
        renderRunnerTable();
      }
    });
    document.getElementById('nextPageBtn').addEventListener('click', () => {
      const totalPages = Math.max(1, Math.ceil(filteredRunners.length / runnerPageSize));
      if (runnerPage < totalPages) {
        runnerPage++;
        renderRunnerTable();
      }
    });
    document.getElementById('resetRunnerFiltersBtn').addEventListener('click', () => {
      runnerQuery = '';
      runnerEventFilter = 'ALL';
      runnerCategoryFilter = 'ALL';
      runnerGenderFilter = 'ALL';
      runnerStatusFilter = 'ALL';
      runnerRemarkFilter = 'ALL';
      runnerSortCol = 'pos';
      runnerSortDir = 'asc';
      activeBucketFilter = null;
      updateBucketFilterBadge();
      document.getElementById('runnerSearchInput').value = '';
      document.getElementById('runnerEventSelect').value = 'ALL';
      document.getElementById('runnerCategorySelect').value = 'ALL';
      document.getElementById('runnerGenderSelect').value = 'ALL';
      document.getElementById('runnerStatusSelect').value = 'ALL';
      document.getElementById('runnerRemarkSelect').value = 'ALL';
      document.getElementById('runnerDetailDrawer').classList.add('hidden');
      renderStatusAndRightPanel();
      filterRunnersList();
    });

    const NAV_SECTION_IDS = [
      'overviewSection',
      'blackFlagSection',
      'countrySection',
      'winnersSection',
      'runnerTableSection'
    ];

    function setActiveNavBtn(targetId) {
      document.querySelectorAll('.nav-jump-btn').forEach(btn => {
        const active = btn.dataset.navTarget === targetId;
        btn.className = active
          ? 'nav-jump-btn px-3 py-1.5 rounded-lg text-xs font-semibold transition bg-red-600 text-white shadow-sm hover:bg-red-500'
          : 'nav-jump-btn px-3 py-1.5 rounded-lg text-xs font-medium transition text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--background)]';
      });
    }

    let navMenuHidden = false;

    function toggleNavMenu(hide) {
      navMenuHidden = Boolean(hide);
      const expanded = document.getElementById('stickyNavExpanded');
      const collapsed = document.getElementById('stickyNavCollapsed');
      if (!expanded || !collapsed) return;
      if (navMenuHidden) {
        expanded.classList.add('hidden');
        collapsed.classList.remove('hidden');
      } else {
        expanded.classList.remove('hidden');
        collapsed.classList.add('hidden');
      }
    }

    function scrollToSection(sectionId) {
      const el = document.getElementById(sectionId);
      if (!el) return;
      if (NAV_SECTION_IDS.includes(sectionId)) {
        setActiveNavBtn(sectionId);
      } else {
        setActiveNavBtn('overviewSection');
      }
      if (window.innerWidth < 640 && sectionId !== 'topHeaderSection') {
        toggleNavMenu(true);
      }
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    window.addEventListener('scroll', () => {
      let current = NAV_SECTION_IDS[0];
      for (const id of NAV_SECTION_IDS) {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 140) {
            current = id;
          }
        }
      }
      setActiveNavBtn(current);
    }, { passive: true });

    initRunnerFilterOptions();
    renderAll();
    filterRunnersList();
  </script>
</body>
</html>
"""


def main():
    data = compute_dashboard_data()
    html = HTML_TEMPLATE.replace("__DASHBOARD_JSON__", json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    out_file = WORKSPACE / "dashboard.html"
    out_file.write_text(html, encoding="utf-8")
    print(f"Created {out_file} ({len(html)} bytes)")
    index_file = WORKSPACE / "index.html"
    index_file.write_text(html, encoding="utf-8")
    print(f"Created {index_file} ({len(html)} bytes)")
    if ARTIFACT_PATH.parent.exists():
        ARTIFACT_PATH.write_text(html, encoding="utf-8")
        print(f"Updated artifact {ARTIFACT_PATH} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
