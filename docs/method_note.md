# Method Note

I collected 2,847 Play Store reviews for the MoveInSync app (package id [PACKAGE_ID], India store) covering 13 Oct 2025 to 11 Oct 2026, using Python (google-play-scraper, pandas, matplotlib). The pipeline, ratings_pipeline.py, is one script: `python ratings_pipeline.py` scrapes the last 365 days and regenerates the report and charts; `python ratings_pipeline.py --from-csv` re-analyzes an existing reviews.csv. Reviewer names, images and IDs are removed from the saved data.

I tagged each review by theme, journey stage and owner with keyword rules (multi-label, so theme shares overlap). Tagging is approximate: 55% of reviews are three words or fewer, and the keywords are English, so Hinglish and other-language reviews, which the scrape does include, are tagged poorly.

To look for release effects I compared monthly averages with the app versions in each month and with per-version averages (versions with at least 50 reviews). The dips in June (3.56) and August (3.65) coincide with versions 12.13.x/12.14.0 and 12.16.x/12.17.0; this shows alignment, not proven cause. I also measured the developer reply rate on 1-2 star reviews (29 of 768, 3.8%).

Tools: Python for scraping, analysis and charts; NVIDIA Nemotron for drafting help; Claude for analysis review and script work; manual reading of reviews to refine themes and select quotes. I checked the figures in the recommendation against the generated report.

Limitations: keyword tagging is approximate; only reviewers who write are captured; the 3.84 average is of scraped reviews, not the store's cumulative rating ([STORE_RATING]).