"""Round 4: pick params positive on BOTH dev windows (this + old 15 Nov).
Score candidates by min(pnl_new, pnl_old) and by sum."""
import gzip
import json
import sys
sys.path.insert(0, "/home/hatch/workspace/makefun/btc-race-24h-20261117-0603/research")
import search
import search2
from search import simulate


def load(path):
    bars = [json.loads(l) for l in gzip.open(path, "rt")]
    return ([{"o": int(b["o"]) / 1e5, "c": int(b["c"]) / 1e5,
              "o_depth": int(b["o_depth"][0]) / 1e6,
              "c_depth": int(b["c_depth"][0]) / 1e6} for b in bars],
            [int(b["c"]) / 1e5 for b in bars])


NEW_BARS, NEW_CLOSES = load(
    "/home/hatch/workspace/makefun/btc-race-24h-20261117-0603-kit/dataset/bars/CBBTC.ndjson.gz")
OLD_BARS, OLD_CLOSES = load(
    "/home/hatch/workspace/makefun/btc-race-kit/btc-race-24h-20261115-0828-kit/dataset/bars/CBBTC.ndjson.gz")


def run_on(bars, closes, params):
    bb, mb, dip, trail = params
    search.BARS = bars
    search.CLOSES = closes
    search2.CLOSES = closes
    fn = search2.block_ma_decide(bb, mb, dip, trail, 200, False)
    return simulate(fn)


rows = []
for bb in (10, 15, 20, 30):
    for mb in (4, 6, 8):
        for dip in (50, 75, 100, 150):
            for trail in (60, 80, 120, 200):
                rn = run_on(NEW_BARS, NEW_CLOSES, (bb, mb, dip, trail))
                ro = run_on(OLD_BARS, OLD_CLOSES, (bb, mb, dip, trail))
                rows.append((min(rn["pnl"], ro["pnl"]), rn["pnl"] + ro["pnl"],
                             (bb, mb, dip, trail), round(rn["pnl"], 2),
                             round(ro["pnl"], 2), rn["trades"], ro["trades"]))
rows.sort(reverse=True)
print("top by min(new, old):")
for r in rows[:20]:
    print(r)
print()
print("top by sum where both > 0:")
both = [r for r in rows if r[3] > 0 and r[4] > 0]
both.sort(key=lambda r: -r[1])
for r in both[:15]:
    print(r)
print("count both>0:", len(both), "/", len(rows))
