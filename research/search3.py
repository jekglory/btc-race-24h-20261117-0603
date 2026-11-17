"""Round 3: fine neighborhood around block-MA (10, 8, dip 50, trail 80) +
robustness: same params run on the OLD 15 Nov dev window (different 24h)."""
import gzip
import json
import sys
sys.path.insert(0, "/home/hatch/workspace/makefun/btc-race-24h-20261117-0603/research")
import search
from search import simulate, CLOSES
from search2 import block_ma_decide

print("== fine neighborhood (this window) ==")
rows = []
for bb in (8, 10, 12, 15):
    for mb in (6, 7, 8, 9, 10):
        for dip in (25, 50, 75):
            for trail in (60, 80, 100):
                r = simulate(block_ma_decide(bb, mb, dip, trail, 200, False))
                rows.append((r["pnl"], (bb, mb, dip, trail), r["trades"],
                             round(r["max_dd_pct"], 2)))
rows.sort(reverse=True)
for row in rows[:20]:
    print(row)
print("median pnl of neighborhood:", sorted(r[0] for r in rows)[len(rows)//2],
      "share > 0:", sum(1 for r in rows if r[0] > 0), "/", len(rows))

print("== same params on OLD 15 Nov dev window ==")
old_bars = [json.loads(l) for l in gzip.open(
    "/home/hatch/workspace/makefun/btc-race-kit/btc-race-24h-20261115-0828-kit/dataset/bars/CBBTC.ndjson.gz", "rt")]
old_closes = [int(b["c"]) / 1e5 for b in old_bars]
old_BARS = [{"o": int(b["o"]) / 1e5, "c": int(b["c"]) / 1e5,
             "o_depth": int(b["o_depth"][0]) / 1e6,
             "c_depth": int(b["c_depth"][0]) / 1e6} for b in old_bars]
print("old window: start", old_closes[0], "end", old_closes[-1],
      "chg bps", (old_closes[-1]-old_closes[0])*10000//old_closes[0])

# monkeypatch the globals search.simulate reads
search.BARS = old_BARS
search.CLOSES = old_closes
import search2
search2.CLOSES = old_closes
for params in [(10, 8, 50, 80), (10, 8, 50, 60), (10, 8, 50, 100),
               (15, 8, 50, 80), (30, 4, 50, 80), (10, 7, 50, 80),
               (10, 9, 50, 80), (12, 8, 50, 80), (10, 8, 25, 80),
               (10, 8, 75, 80)]:
    bb, mb, dip, trail = params
    r = simulate(search2.block_ma_decide(bb, mb, dip, trail, 200, False))
    print(params, "pnl", round(r["pnl"], 2), "trades", r["trades"],
          "maxDD%", round(r["max_dd_pct"], 2))
