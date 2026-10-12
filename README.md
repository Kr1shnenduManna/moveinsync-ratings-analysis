# ratings_pipeline.py — MoveInSync Play Store Ratings Analysis

## What it does
Fetches English reviews for the MoveInSync Play Store app, tags complaint themes with keyword rules, computes monthly and per-version averages, and produces a repeatable report with candidate fix tickets.

## Requirements
```bash
pip install google-play-scraper pandas matplotlib tabulate
```

## Setup
1. Open the app's Play Store URL (e.g., `https://play.google.com/store/apps/details?id=com.moveinsync.app`).
2. Copy the value after `id=` (here `com.moveinsync.app`).
3. Set `APP_ID = "com.moveinsync.app"` at the top of `ratings_pipeline.py`.

## How to run
```bash
# Fresh scrape (13 Oct 2025 → 11 Oct 2026)
python ratings_pipeline.py

# Re-analyze existing CSV
python ratings_pipeline.py --from-csv reviews.csv
```

## Outputs
- `reviews.csv` — raw reviews with theme tags
- `report.md` — one-page summary (monthly trend, version table ≥50 reviews, themes, reply rate, candidate tickets)
- `charts/trend.png` — monthly average rating line
- `charts/dist.png` — star distribution histogram
- `charts/themes.png` — theme share bar chart (1–2 star reviews only)

## Reading the report
1. **Monthly trend** — spots dips (e.g., Jun 3.56, Aug 3.65).
2. **Version table** — versions with ≥50 reviews; flags 12.13.1 (3.68), 12.19.0 (3.62).
3. **Themes** — top 4 engineering-owned themes + shares.
4. **Reply rate** — % of 1–2 star reviews with developer reply.
5. **Candidate tickets** — 5 concrete day-one fixes pulled from review quotes.

## Adjusting themes
Edit the `THEMES` dictionary in `ratings_pipeline.py`; keys are theme names, values are regex patterns (case-insensitive). Re-run with `--from-csv` to re-tag without re-scraping.

## Monthly drop alert
The script exits non-zero if the latest month's average drops ≥0.3 stars vs. prior month — hook this into CI/Slack for automatic alerts.

## Known limitations
- Keyword tagging is approximate (spot-checked ~**[N]** reviews, ~**[X]%** agreement).
- 55% of reviews ≤3 words; short reviews often missed.
- English only — Hindi/Hinglish under-represented.
- Self-selection bias (only reviewers who write).
- Average is of scraped reviews (3.84), not store cumulative rating **[STORE_RATING]**.