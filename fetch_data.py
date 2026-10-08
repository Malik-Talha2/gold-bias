"""Fetch hourly gold candles + gold-related headlines and write data.json."""
import json, re, datetime
import feedparser
import yfinance as yf

# 1) Candles: COMEX gold futures (free Yahoo data, closely tracks XAU/USD)
df = yf.download("GC=F", period="30d", interval="1h", progress=False, auto_adjust=True)
if hasattr(df.columns, "get_level_values"):
    df.columns = df.columns.get_level_values(0)
df = df.dropna().tail(100)
candles = [
    {"o": round(float(r.Open), 2), "h": round(float(r.High), 2),
     "l": round(float(r.Low), 2), "c": round(float(r.Close), 2)}
    for r in df.itertuples()
]

# 2) Headlines from free RSS feeds
FEEDS = [
    "https://news.google.com/rss/search?q=gold+price+OR+Fed+OR+dollar+OR+Treasury+yields+when:1d&hl=en-US&gl=US&ceid=US:en",
    "https://www.fxstreet.com/rss/news",
]
KEEP = re.compile(r"gold|bullion|fed\b|dollar|yield|treasur|inflation|rate (cut|hike)|safe.haven", re.I)
seen, headlines = set(), []
for url in FEEDS:
    try:
        for e in feedparser.parse(url).entries:
            t = re.sub(r"\s+-\s+[^-]+$", "", e.title).strip()  # drop " - Source"
            if KEEP.search(t) and t.lower() not in seen:
                seen.add(t.lower()); headlines.append(t)
    except Exception as ex:
        print("feed failed:", url, ex)
headlines = headlines[:15]

if len(candles) < 30:
    raise SystemExit("Not enough candles fetched; keeping old data.json")

out = {
    "updated": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    "candles": candles,
    "headlines": headlines or ["No gold headlines found in the last day"],
}
json.dump(out, open("data.json", "w"))
print(f"Wrote {len(candles)} candles and {len(headlines)} headlines")
