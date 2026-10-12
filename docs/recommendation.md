# MoveInSync Play Store Rating Improvement Recommendation

## Headline

The Play Store average of scraped reviews is 3.84 with 27% at 1–2 stars; ratings are polarized (64% five-star, 24% one-star) and dips follow specific releases. The top four complaint themes—booking failures, crashes, login/OTP issues, and tracking inaccuracies—are all engineering-owned, yet only 3.8% of negative reviews receive a reply. **Top three actions:** enforce a release quality gate with staged rollout, fix login/session persistence during active trips, and make booking flow one-step with visible waitlist status.

## Why the Rating Is Where It Is

1. **Polarized distribution** — 768 reviews (27%) are 1–2 star while 1,827 (64%) are 5-star; the average masks two distinct user populations.
2. **Dips follow releases** — June 2026 average fell to 3.56 on versions 12.13.x/12.14.0; August fell to 3.65 on 12.16.x/12.17.0. Months near 4.0 (Apr, May, Jul) ran stable versions 12.11.x–12.15.
3. **Top four themes are engineering-owned** — Booking/roster/cancel failures 15.8% (121 reviews), Crash/slow/app down 14.5% (111), Login/OTP/session 14.1% (108), Tracking/ETA/location 11.8% (91).
4. **Almost no developer replies** — Only 29 of 768 negative reviews (3.8%) received a reply; one reply stated the company "only builds the app and is not responsible for daily operations."
5. **Specific UX regressions in latest version** — v12.19.0 introduced a seat-belt pop-up before OTP (extra click), forced post-ride rating with no skip, silent waitlist booking, ETA shorter than Google Maps, tracking only near pickup, and repeated logouts.

> "Map zoom resets every 30 seconds and keeps the destination in view while waiting for the cab" (v12.6)  
> "OTP not received at login, and no message about whether the phone/email is registered" (v12.8.3)  
> "User logged out while the cab is waiting, losing cab number, OTP and helpdesk access" (v12.8.2)  
> "After a UI update, booking a shuttle became a 2-step process (was 1); a user thought they had booked but had not" (v12.14.1)  
> "In v12.19.0: viewing the OTP now first shows a seat-belt pop-up (extra click); a forced post-ride rating with no skip; app books without telling the user they are on a waitlist" (v12.19.0)

## Priority Table

| Rank | Problem | Evidence | Fix | Owner | Success Metric |
|------|---------|----------|-----|-------|----------------|
| 1 | Release quality gate and staged rollout | June dip (3.56) on 12.13.x/12.14.0; Aug dip (3.65) on 12.16.x/12.17.0; 12.19.0 at 3.62 (105 reviews) | Mandatory 5%→25%→100% staged rollout; block rollout if 1-2 star rate >15% or crash rate >0.5% in first 48h | Engineering Lead | Zero monthly average dips below 3.8 for two consecutive quarters |
| 2 | Login/OTP/session persistence (no logout during active trip) | 108 reviews (14.1%); "User logged out while the cab is waiting, losing cab number, OTP and helpdesk access" (v12.8.2); "OTP not received at login" (v12.8.3) | Persist session for trip duration + 30 min; show registered phone/email on OTP screen; add resend timer | Mobile Engineering | Login/OTP/session complaints down by half within two releases |
| 3 | Booking flow clarity (one-step, show waitlist) | 121 reviews (15.8%) on booking/roster/cancel; "Booking became a 2-step process; user thought they had booked but had not" (v12.14.1); "App books without telling the user they are on a waitlist" (v12.19.0) | Revert to single-tap booking; show waitlist badge + position; confirm booking with toast + push | Product + Mobile | Booking failure theme share drops below 8% of negative reviews |
| 4 | ETA and tracking accuracy (include zoom bug) | 91 reviews (11.8%); "GPS shows driver in wrong location; ETA and pickup time often not synchronized" (v12.13.1); "Map zoom resets every 30 seconds" (v12.6); "Tracking only available close to pickup" (v12.19.0) | Fix zoom reset; poll driver location every 10s; show Google Maps ETA delta; enable tracking from booking confirmation | Mobile + Backend | Tracking/ETA complaints down by half within two releases |
| 5 | Remove forced prompts | "Seat-belt pop-up before OTP (extra click)"; "Forced post-ride rating with no skip"; "Repeated policy/disclaimer and microphone permission prompts every open" (v12.19.0) | One-tap OTP (no pre-prompt); post-ride rating dismissible; policy/mic prompt once per version | Product + Mobile | UX friction theme share drops below 5% of negative reviews |
| 6 | Reply to every 1-2 star review within 48h with specific answer | Only 29/768 (3.8%) replied; generic replies; one deflects ops responsibility | Auto-assign by theme; template per theme with ticket link; escalate ops themes to Support/Operations | Support Lead + Engineering | Negative-review reply rate above 80% within 30 days |

## Day-One Tickets (Engineer-Pickup Ready)

1. **Add check-in reminder notification 5 minutes before pickup and again when vehicle crosses pickup geofence** — from "Users who miss check-in are marked 'No show' with no reminder; asks for a notification after the vehicle crosses the pickup point" (v12.14.1).
2. **Persist session token for the duration of an active trip plus 30 minutes; suppress logout API calls while trip state = ON_TRIP** — from "User logged out while the cab is waiting, losing cab number, OTP and helpdesk access" (v12.8.2).
3. **Revert shuttle booking to single-tap; add waitlist banner with position number on booking screen** — from "Booking became a 2-step process; user thought they had booked but had not" (v12.14.1) and "App books without telling the user they are on a waitlist" (v12.19.0).
4. **Fix map zoom reset: store camera position in ViewModel; restore on location update instead of animating to destination** — from "Map zoom resets every 30 seconds and keeps the destination in view while waiting for the cab" (v12.6).
5. **Remove seat-belt pop-up before OTP screen; make post-ride rating dismissible with "Not now"; show policy/disclaimer and mic permission once per app version** — from v12.19.0 evidence on extra clicks and forced prompts.

## What the App Cannot Fix

Operations-owned issues appear in reviews but require ops/transport-desk action: cab late/not assigned/no-show (8.3%, 64 reviews), safety/driver conduct (4.2%, 32), routing/pickup time (4.0%, 31). **Recommendation:** Export tagged reviews weekly to the Operations lead and each transport desk with volume, sample quotes, and version tags so they can correlate with vendor SLAs and driver rosters. Engineering should not own fixes for vendor dispatch or driver behavior.

## Expected Impact (Estimate)

**Assumptions:** (a) The four engineering themes (56% of negative reviews) are addressable in-app; (b) staged rollout prevents regression dips; (c) reply rate improvement lifts sentiment by ~0.1–0.15 stars per quarter (industry benchmark).  
**Range:** If all six fixes ship within two quarters, the scraped-review average could move from 3.84 to **3.95–4.10** and the 1-2 star share from 27% to **15–18%**. The store's cumulative rating ([STORE_RATING]) will lag by 1–2 quarters. Do not target a precise number; track the weekly scraped average and the 1-2 star share as leading indicators.

## How We Will Keep Answering "How Are Our Ratings?"

1. **ratings_pipeline.py** — repeatable script (Python, google-play-scraper, pandas) that fetches reviews, tags themes via keyword rules, computes version/month averages, and outputs CSV + charts. Supports `--from-csv` for backfill.
2. **Monthly alert** — GitHub Action / cron runs the script on the 1st of each month; posts a one-page summary (average, 1-2 star count, top 3 themes, version breakdown) to the #play-store-ratings Slack channel and emails the PM/Eng lead.
3. **Optional weekly scheduled run** — Same script on Mondays; only posts if 1-2 star count >20% of weekly reviews or a new version crosses 50 reviews, so the team gets early warning without noise.

## Limitations

- Keyword tagging spot-checked on ~**[N]** reviews with ~**[X]%** agreement; theme shares are approximate.
- 55% of reviews are ≤3 words; short reviews may be mis-tagged or missed.
- Scrape used English only; Hindi/Hinglish reviews are under-represented.
- Only reviewers who write are captured (self-selection bias).
- Average is of scraped reviews (3.84), not the store's cumulative rating ([STORE_RATING]).