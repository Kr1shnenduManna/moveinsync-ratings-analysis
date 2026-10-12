"""
MoveInSync Play Store ratings pipeline v2 (repeatable).
  pip install google-play-scraper pandas matplotlib tabulate
  python ratings_pipeline.py              # scrape last DAYS days, then analyze
  python ratings_pipeline.py --from-csv   # re-analyze existing reviews.csv (no scraping)
Outputs: reviews.csv, report.md, charts/*.png
"""
import os, re, sys
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

APP_ID = "com.moveinsync.ets"      # package id only: text after id= and before any &
DAYS, COUNTRY, LANG = 365, "in", "en"
MIN_VERSION_N = 50                    # ignore versions with fewer reviews (too noisy)
DROP_ALERT = 0.3                      # alert if monthly avg falls by more than this

# theme -> (regex, journey stage, owner). Multi-label. Tuned on real 1-2 star reviews; extend as needed.
THEMES = {
 "Crash / slow / app down":   (r"\bcrash|\bhang|\bslow|\bbug|glitch|not working|doesn.?t work|\berror|freez|loading|server|app (is )?down|not opening|won.?t open", "App stability", "Engineering"),
 "Booking / roster / cancel": (r"\bbook|roster|schedule|\bslot|cancel|waitlist|wait list|unable to|not able to|2 step|two step", "Self-booking", "Engineering"),
 "Login / OTP / session":     (r"\blogin|log in|\botp|sign in|password|verif|logs? out|logged out|session|reinstall", "Onboarding / session", "Engineering"),
 "Tracking / ETA / location": (r"\btrack|\bgps|\beta\b|location|address|\bmap|zoom|pickup point|pick up point", "Live tracking", "Engineering"),
 "Support unreachable":       (r"help ?desk|customer (care|support)|\bsupport\b|no response|complaint|escalat|call (back|center)|no calling", "Issue resolution", "Support"),
 "Cab late / not assigned / no-show": (r"\bnot assign|no cab|\blate\b|delay|\bwait|no.?show|missed|didn.?t come|not come|not arrive|cab not", "Pickup", "Operations"),
 "Safety / driver conduct":   (r"unsafe|safety|harass|\brude|misbehav|rash|drunk|women safe|behaviou?r", "Boarding / ride", "Operations"),
 "Routing / pickup time":     (r"\broute|pickup time|pick up time|detour|clubbed|pooling|drop sequence", "Routing", "Product / Ops"),
 "UX friction / forced prompts": (r"user.?friendly|\bux\b|\bui\b|dropdown|drop down|too many|confus|complicat|disclaimer|policy|permission|microphone|feedback|rate the|seat ?belt|new update|old version", "UX", "Product"),
 "Notifications":             (r"notification|\balert|\bsms\b|reminder", "Pre-ride", "Engineering"),
}
CONTENTLESS = "Contentless (short, no specific issue)"

def tag(text):
    t = (text or "").lower()
    hits = [k for k, (rx, _, _) in THEMES.items() if re.search(rx, t)]
    if not hits:
        hits = [CONTENTLESS if len(t.split()) <= 4 else "Other (specific, untagged)"]
    return hits

def collect():
    import time
    from google_play_scraper import reviews, Sort
    cutoff = datetime.now() - timedelta(days=DAYS)
    out, token, fails = [], None, 0
    while True:
        try:
            batch, token = reviews(APP_ID, lang=LANG, country=COUNTRY, sort=Sort.NEWEST,
                                   count=200, continuation_token=token)
        except Exception as e:                      # blocked, rate-limited, or wrong app id
            fails += 1
            print(f"Scrape error ({fails}/3): {type(e).__name__}: {e}")
            if fails >= 3: break
            time.sleep(5 * fails); continue
        if not batch: break
        out += batch
        if batch[-1]["at"] < cutoff or token is None: break
    print(f"Fetched {len(out)} reviews from the Play Store for APP_ID={APP_ID!r}")
    if not out:
        print("No reviews returned. Check: (1) APP_ID is exact, (2) internet/VPN, (3) try again later (rate limit), "
              "(4) pip install -U google-play-scraper")
        return pd.DataFrame()                       # caller decides what to do
    df = pd.DataFrame(out)
    df = df.rename(columns={"score": "rating", "content": "text", "at": "date",
                            "reviewCreatedVersion": "version", "thumbsUpCount": "thumbs"})
    return df[df["date"] >= cutoff].copy()

def prepare(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["version"] = df["version"].fillna("unknown").astype(str).replace({"nan": "unknown"})
    df["text"] = df["text"].fillna("")
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["themes"] = df["text"].apply(tag)
    if "replyContent" not in df: df["replyContent"] = None
    # privacy: never write reviewer identities to disk (safe to publish the CSV)
    df = df.drop(columns=[c for c in ("userName", "userImage", "reviewId") if c in df.columns])
    df.to_csv("reviews.csv", index=False)
    return df

def analyze(df):
    os.makedirs("charts", exist_ok=True)
    neg = df[df["rating"] <= 2]
    monthly = df.groupby("month")["rating"].agg(["mean", "count"]).round(2)
    dist = df["rating"].value_counts().sort_index()
    ver = (df[df["version"] != "unknown"].groupby("version")["rating"].agg(["mean", "count"])
             .query(f"count >= {MIN_VERSION_N}").sort_values("mean").round(2))
    rows = []
    for theme in list(THEMES) + [CONTENTLESS, "Other (specific, untagged)"]:
        has = lambda x: theme in x
        s, n = df[df["themes"].apply(has)], neg[neg["themes"].apply(has)]
        if len(n) == 0: continue
        meta = THEMES.get(theme, ("", "-", "-"))
        rows.append({"Theme": theme, "Stage": meta[1], "Owner": meta[2], "Mentions": len(s),
                     "1-2 star reviews": len(n), "Share of 1-2 star %": round(100 * len(n) / len(neg), 1),
                     "Avg stars when mentioned": round(s["rating"].mean(), 2)})
    themes = pd.DataFrame(rows).sort_values("1-2 star reviews", ascending=False)
    # theme x month for trend of the top 3 themes
    top3 = themes[~themes["Theme"].isin([CONTENTLESS, "Other (specific, untagged)"])]["Theme"].head(3).tolist()
    # reply rate
    replied = neg["replyContent"].notna().sum()
    reply = {"neg_total": len(neg), "neg_replied": int(replied),
             "pct": round(100 * replied / max(len(neg), 1), 1)}
    # charts
    ax = monthly["mean"].plot(marker="o", title="Average rating by month"); ax.set_ylim(1, 5)
    plt.tight_layout(); plt.savefig("charts/trend.png", dpi=150); plt.clf()
    dist.plot(kind="bar", title="Star distribution"); plt.tight_layout(); plt.savefig("charts/dist.png", dpi=150); plt.clf()
    real = themes[~themes["Theme"].isin([CONTENTLESS, "Other (specific, untagged)"])].sort_values("1-2 star reviews")
    colors = real["Owner"].map({"Engineering": "#1f77b4", "Operations": "#ff7f0e", "Support": "#2ca02c", "Product / Ops": "#9467bd", "Product": "#d62728"}).fillna("#7f7f7f")
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(real["Theme"], real["Share of 1-2 star %"], color=colors)
    for b, n, p in zip(bars, real["1-2 star reviews"], real["Share of 1-2 star %"]):
        ax.text(p + 0.2, b.get_y() + b.get_height() / 2, f"{p}% ({n})", va="center", fontsize=9)
    ax.set_xlabel(f"% of {len(neg)} one- and two-star reviews mentioning the theme (themes overlap)")
    ax.set_title("What 1-2 star reviewers complain about (colour = owner)")
    ax.set_xlim(0, real["Share of 1-2 star %"].max() + 4)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=c, label=o) for o, c in [("Engineering", "#1f77b4"), ("Operations", "#ff7f0e"), ("Support", "#2ca02c"), ("Product / Ops", "#9467bd"), ("Product", "#d62728")]], loc="lower right")
    fig.text(0.01, 0.01, f"Not shown: {int(themes[themes['Theme']==CONTENTLESS]['1-2 star reviews'].sum())} contentless reviews (e.g. 'worst app') and {int(themes[themes['Theme']=='Other (specific, untagged)']['1-2 star reviews'].sum())} specific-but-untagged.", fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig("charts/themes.png", dpi=150); plt.close(fig)
    return monthly, dist, ver, themes, neg, reply, top3

def report(df, monthly, dist, ver, themes, neg, reply, top3):
    alert = ""
    if len(monthly) >= 3 and monthly["mean"].iloc[-2] < monthly["mean"].iloc[-3] - DROP_ALERT:
        alert = f"**ALERT: last full month fell by more than {DROP_ALERT} stars.**\n\n"
    q = neg[neg["text"].str.split().str.len() >= 12].sort_values("thumbs", ascending=False).head(8)
    stale = "**NOTE: the scrape returned no reviews this run, so this report re-uses the previously saved reviews.csv.**\n\n" if STALE else ""
    md = f"""# Play Store ratings report ({datetime.now():%d %b %Y})
{stale}{alert}Reviews analysed: {len(df)} (last {DAYS} days). Average of these reviews: {df['rating'].mean():.2f}. 1-2 star share: {100*len(neg)/len(df):.1f}%.
Note: this is the average of scraped reviews, not Play Store's cumulative rating. Cite the store figure separately.

## Monthly trend
{monthly.to_markdown()}

## Star distribution
{dist.to_markdown()}

## Versions with >= {MIN_VERSION_N} reviews, lowest first
{ver.head(8).to_markdown()}

## Themes in 1-2 star reviews (multi-label, so shares overlap)
{themes.to_markdown(index=False)}

## Developer replies to 1-2 star reviews
{reply['neg_replied']} of {reply['neg_total']} replied ({reply['pct']}%).

## Detailed negative reviews with most upvotes (candidate tickets)
""" + "\n".join(f"- ({r.rating}*, v{r.version}) {r.text[:350]}" for r in q.itertuples())
    open("report.md", "w", encoding="utf-8").write(md)
    print(md[:2500])

STALE = False

if __name__ == "__main__":
    if "--from-csv" in sys.argv:
        raw = pd.read_csv("reviews.csv")
    else:
        if APP_ID.startswith("PASTE"):
            sys.exit("Set APP_ID at the top of ratings_pipeline.py (text after 'id=' in the Play Store URL).")
        raw = collect()
        if raw.empty:
            if os.path.exists("reviews.csv"):
                print("::warning::Scrape returned no reviews (blocked, rate-limited or wrong APP_ID). Re-using saved reviews.csv.")
                STALE = True
                raw = pd.read_csv("reviews.csv")
            else:
                sys.exit("Scrape returned no reviews and there is no saved reviews.csv. Check APP_ID and network, or run locally.")
    data = prepare(raw)
    report(data, *analyze(data))
