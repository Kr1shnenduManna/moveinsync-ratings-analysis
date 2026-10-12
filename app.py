"""
MoveInSync Play Store ratings dashboard.
Run locally:  pip install streamlit pandas altair
              streamlit run app.py
Reads reviews.csv produced by ratings_pipeline.py (no scraping here).
"""
import ast
import altair as alt
import pandas as pd
import streamlit as st

st.set_page_config(page_title="MoveInSync Ratings", page_icon="⭐", layout="wide")

OWNER = {
    "Crash / slow / app down": "Engineering", "Booking / roster / cancel": "Engineering",
    "Login / OTP / session": "Engineering", "Tracking / ETA / location": "Engineering",
    "Notifications": "Engineering", "UX friction / forced prompts": "Product",
    "Routing / pickup time": "Product / Ops", "Support unreachable": "Support",
    "Cab late / not assigned / no-show": "Operations", "Safety / driver conduct": "Operations",
}
NOT_THEMES = {"Contentless (short, no specific issue)", "Other (specific, untagged)"}
OWNER_COLORS = alt.Scale(domain=["Engineering", "Product", "Product / Ops", "Support", "Operations"],
                         range=["#1f77b4", "#d62728", "#9467bd", "#2ca02c", "#ff7f0e"])

@st.cache_data
def load(path="reviews.csv"):
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["version"] = df["version"].fillna("unknown").astype(str)
    df["text"] = df["text"].fillna("")
    df["themes"] = df["themes"].apply(ast.literal_eval)
    df["month"] = df["date"].dt.to_period("M").astype(str)
    if "replyContent" not in df:
        df["replyContent"] = None
    return df

try:
    data = load()
except FileNotFoundError:
    st.error("reviews.csv not found. Run `python ratings_pipeline.py` first.")
    st.stop()

# ---------------- sidebar filters ----------------
st.sidebar.header("Filters")
d0, d1 = data["date"].min().date(), data["date"].max().date()
rng = st.sidebar.date_input("Date range", (d0, d1), min_value=d0, max_value=d1)
if isinstance(rng, tuple) and len(rng) == 2:
    d0, d1 = rng
stars = st.sidebar.multiselect("Star rating", [1, 2, 3, 4, 5], default=[1, 2, 3, 4, 5])
min_n = st.sidebar.slider("Min reviews per version (version table)", 10, 100, 50, step=10)
st.sidebar.caption("Source: Play Store reviews scraped with ratings_pipeline.py. "
                   "Reviewer identities are not stored.")

df = data[(data["date"].dt.date >= d0) & (data["date"].dt.date <= d1) & (data["rating"].isin(stars))]
if df.empty:
    st.warning("No reviews match these filters.")
    st.stop()
neg = df[df["rating"] <= 2]

# ---------------- header + KPIs ----------------
st.title("MoveInSync: Play Store ratings health")
st.caption(f"{d0:%d %b %Y} to {d1:%d %b %Y}. The average below is of scraped reviews, "
           "not the store's cumulative rating.")

last30 = df[df["date"] >= df["date"].max() - pd.Timedelta(days=30)]
prev30 = df[(df["date"] < df["date"].max() - pd.Timedelta(days=30)) &
            (df["date"] >= df["date"].max() - pd.Timedelta(days=60))]
delta = (last30["rating"].mean() - prev30["rating"].mean()) if len(last30) and len(prev30) else None
replied = neg["replyContent"].notna().sum()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Reviews", f"{len(df):,}")
k2.metric("Average rating", f"{df['rating'].mean():.2f}")
k3.metric("1-2 star share", f"{100 * len(neg) / len(df):.1f}%")
k4.metric("Last 30 days", f"{last30['rating'].mean():.2f}" if len(last30) else "n/a",
          None if delta is None else f"{delta:+.2f} vs prior 30d")
k5.metric("Dev reply rate (1-2 star)", f"{100 * replied / max(len(neg), 1):.1f}%",
          help=f"{replied} of {len(neg)} negative reviews received a developer reply")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Why ratings are low", "Releases", "Fix first", "Review explorer"])

# ---------------- tab 1: overview ----------------
with tab1:
    c1, c2 = st.columns([2, 1])
    monthly = df.groupby("month")["rating"].agg(avg="mean", reviews="count").reset_index()
    line = (alt.Chart(monthly).mark_line(point=True)
            .encode(x=alt.X("month:O", title="Month"),
                    y=alt.Y("avg:Q", scale=alt.Scale(domain=[1, 5]), title="Average rating"),
                    tooltip=["month", alt.Tooltip("avg:Q", format=".2f"), "reviews"])
            .properties(title="Average rating by month", height=320))
    c1.altair_chart(line, use_container_width=True)
    c1.caption("Last month shown may be partial. Dips are compared with release versions in the Releases tab.")
    dist = df["rating"].value_counts().sort_index().rename_axis("stars").reset_index(name="reviews")
    bars = (alt.Chart(dist).mark_bar().encode(x=alt.X("stars:O", title="Stars"), y="reviews:Q",
            tooltip=["stars", "reviews"]).properties(title="Star distribution", height=320))
    c2.altair_chart(bars, use_container_width=True)
    st.info("Ratings are polarized: most reviewers give 5 stars, and a hard core gives 1 star.")

# ---------------- tab 2: themes ----------------
with tab2:
    rows = []
    for t in OWNER:
        n = neg[neg["themes"].apply(lambda x, t=t: t in x)]
        rows.append({"Theme": t, "Owner": OWNER[t], "1-2 star reviews": len(n),
                     "Share %": round(100 * len(n) / max(len(neg), 1), 1)})
    th = pd.DataFrame(rows).sort_values("1-2 star reviews", ascending=False)
    chart = (alt.Chart(th).mark_bar()
             .encode(y=alt.Y("Theme:N", sort="-x", title=None),
                     x=alt.X("Share %:Q", title=f"% of {len(neg)} one- and two-star reviews (themes overlap)"),
                     color=alt.Color("Owner:N", scale=OWNER_COLORS),
                     tooltip=["Theme", "Owner", "1-2 star reviews", "Share %"])
             .properties(height=380))
    st.altair_chart(chart, use_container_width=True)
    not_shown = {k: int(neg["themes"].apply(lambda x, k=k: k in x).sum()) for k in NOT_THEMES}
    st.caption("Not shown: " + "; ".join(f"{v} {k.lower()}" for k, v in not_shown.items()) +
               ". Tagging is keyword-based and approximate.")
    by_owner = th.groupby("Owner")["1-2 star reviews"].sum().reset_index()
    c1, c2 = st.columns(2)
    c1.subheader("Mentions by owner")
    c1.dataframe(by_owner.sort_values("1-2 star reviews", ascending=False), hide_index=True)
    c2.subheader("Theme table")
    c2.dataframe(th, hide_index=True)

# ---------------- tab 3: releases ----------------
with tab3:
    ver = (df[df["version"] != "unknown"].groupby("version")["rating"]
           .agg(avg="mean", reviews="count").query("reviews >= @min_n").round(2)
           .sort_values("avg").reset_index())
    st.subheader(f"Versions with at least {min_n} reviews (lowest first)")
    st.dataframe(ver, hide_index=True)
    st.caption("Version averages are noisy on small samples. Use as a pointer, not proof of cause.")
    mv = (df[df["version"] != "unknown"].groupby("month")["version"]
          .agg(lambda s: ", ".join(s.value_counts().head(3).index)).reset_index(name="Top versions that month"))
    mv = mv.merge(monthly.round(2), on="month")
    st.subheader("Top versions in each month vs the monthly average")
    st.dataframe(mv, hide_index=True)

# ---------------- tab 4: recommendation summary ----------------
with tab4:
    st.subheader("Prioritized actions")
    st.caption("Summary of the full recommendation (docs/Recommendation.pdf).")
    actions = pd.DataFrame([
        [1, "Release quality", "Dips follow releases", "Crash-rate and login-success gate, staged rollout, rollback", "Engineering"],
        [2, "Login / OTP / session", "Logged out while cab is waiting; OTP not received", "Keep session during an active trip; clear OTP errors", "Engineering"],
        [3, "Booking flow", "Booking became a 2-step process; waitlist not shown", "One-step booking; show waitlist status", "Product + Engineering"],
        [4, "ETA and tracking", "Wrong driver location; map zoom resets", "Fix location and ETA sync; stop auto-zoom reset", "Engineering"],
        [5, "Forced prompts", "Forced rating, seat-belt pop-up before OTP, repeated permissions", "Skip on rating; one-tap OTP; ask once", "Product"],
        [6, "Review replies", "Few negative reviews get a reply", "Reply to every 1-2 star review within 48 hours", "Support / Product"],
    ], columns=["Rank", "Problem", "Evidence", "Fix", "Owner"])
    st.dataframe(actions, hide_index=True, use_container_width=True)
    st.warning("Not fixable in the app: late or unassigned cabs, routing, driver conduct. "
               "Share evidence with operations and transport desks.")

# ---------------- tab 5: explorer ----------------
with tab5:
    c1, c2, c3 = st.columns([1, 2, 1])
    theme_pick = c1.selectbox("Theme", ["All"] + list(OWNER))
    query = c2.text_input("Search text")
    min_words = c3.slider("Min words", 1, 40, 8)
    ex = df.copy()
    if theme_pick != "All":
        ex = ex[ex["themes"].apply(lambda x: theme_pick in x)]
    if query:
        ex = ex[ex["text"].str.contains(query, case=False, na=False)]
    ex = ex[ex["text"].str.split().str.len() >= min_words]
    ex = ex.sort_values(["thumbs", "date"], ascending=False)
    st.caption(f"{len(ex)} reviews")
    st.dataframe(ex[["date", "rating", "version", "thumbs", "text"]].head(300),
                 hide_index=True, use_container_width=True)

st.divider()
st.caption("Limitations: keyword tagging is approximate; only reviewers who write are captured; "
           "short reviews carry little detail.")
