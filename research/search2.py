"""Search round 2: block-MA dip-recovery, Donchian breakout, slow EMA.
Reuses simulate() from search.py (same fill model)."""
import sys
sys.path.insert(0, "/home/hatch/workspace/makefun/btc-race-24h-20261117-0603/research")
from search import simulate, CLOSES, BARS

results = []


def block_ma_decide(block_bars, ma_blocks, dip_bps, trail_bps, stop_bps,
                    exit_on_cross=True, tp_bps=0):
    # block closes: close of every block_bars-th bar
    blocks = []
    buf = []
    for c in CLOSES:
        buf.append(c)
        if len(buf) == block_bars:
            blocks.append(buf[-1])
            buf.clear()
    # map bar index -> block index completed at that bar (block closes at bar k)
    blk_at = []
    b = -1
    for k in range(len(CLOSES)):
        if (k + 1) % block_bars == 0:
            b += 1
        blk_at.append(b)

    def decide(st, k, bar):
        bi = blk_at[k]
        if bi + 1 < ma_blocks:
            return None
        recent = blocks[bi - ma_blocks + 1:bi + 1]
        ma = sum(recent) / len(recent)
        c = bar["c"]
        above = c > ma
        # previous bar's above-ness
        prev_above = None
        if k >= 1:
            bi2 = blk_at[k - 1]
            if bi2 + 1 >= ma_blocks:
                rec2 = blocks[bi2 - ma_blocks + 1:bi2 + 1]
                prev_above = CLOSES[k - 1] > sum(rec2) / len(rec2)
        if st["qty"] > 0:
            val = st["qty"] * c
            if val > st["peak"]:
                st["peak"] = val
            if st["cost"] > 0 and val <= st["cost"] * (1 - stop_bps / 10000):
                return ("sell",)
            if st["peak"] > 0 and val <= st["peak"] * (1 - trail_bps / 10000):
                return ("sell",)
            if tp_bps and st["cost"] > 0 and val >= st["cost"] * (1 + tp_bps / 10000):
                return ("sell",)
            if exit_on_cross and prev_above is not None and prev_above and not above:
                return ("sell",)
            return None
        if prev_above is not None and not prev_above and above:
            high = max(recent)
            if dip_bps == 0 or c <= high * (1 - dip_bps / 10000):
                return ("buy",)
        return None
    return decide


def donchian_decide(n_hi, n_lo, trail_bps, stop_bps, tp_bps=0):
    def decide(st, k, bar):
        c = bar["c"]
        if k < max(n_hi, n_lo):
            return None
        hi = max(CLOSES[k - n_hi:k])
        lo = min(CLOSES[k - n_lo:k])
        if st["qty"] > 0:
            val = st["qty"] * c
            if val > st["peak"]:
                st["peak"] = val
            if st["cost"] > 0 and val <= st["cost"] * (1 - stop_bps / 10000):
                return ("sell",)
            if st["peak"] > 0 and val <= st["peak"] * (1 - trail_bps / 10000):
                return ("sell",)
            if tp_bps and st["cost"] > 0 and val >= st["cost"] * (1 + tp_bps / 10000):
                return ("sell",)
            if c < lo:
                return ("sell",)
            return None
        if c > hi:
            return ("buy",)
        return None
    return decide


def slow_ema_decide(fast, slow, trail_bps, stop_bps, tp_bps=0):
    from search import ema_series
    ef = ema_series(CLOSES, fast)
    es = ema_series(CLOSES, slow)

    def decide(st, k, bar):
        c = bar["c"]
        if st["qty"] > 0:
            val = st["qty"] * c
            if val > st["peak"]:
                st["peak"] = val
            if st["cost"] > 0 and val <= st["cost"] * (1 - stop_bps / 10000):
                return ("sell",)
            if st["peak"] > 0 and val <= st["peak"] * (1 - trail_bps / 10000):
                return ("sell",)
            if tp_bps and st["cost"] > 0 and val >= st["cost"] * (1 + tp_bps / 10000):
                return ("sell",)
            if ef[k] < es[k] and ef[k - 1] >= es[k - 1]:
                return ("sell",)
            return None
        if k >= 1 and ef[k - 1] <= es[k - 1] and ef[k] > es[k]:
            return ("buy",)
        return None
    return decide


print("== block-MA dip-recovery ==")
for bb in (10, 15, 30):
    for mb in (4, 6, 8):
        for dip in (0, 50, 100, 150, 200):
            for trail in (50, 80, 120, 200):
                for stop in (150, 200, 300):
                    for xoc in (True, False):
                        r = simulate(block_ma_decide(bb, mb, dip, trail, stop, xoc))
                        results.append((r["pnl"], "blockMA", (bb, mb, dip, trail, stop, xoc),
                                        r["trades"], round(r["max_dd_pct"], 2)))
results.sort(reverse=True)
for row in results[:15]:
    print(row)

print("== Donchian ==")
dres = []
for nhi in (30, 60, 120, 240):
    for nlo in (30, 60, 120):
        for trail in (60, 100, 150, 250):
            for stop in (150, 250, 400):
                r = simulate(donchian_decide(nhi, nlo, trail, stop))
                dres.append((r["pnl"], "donch", (nhi, nlo, trail, stop),
                             r["trades"], round(r["max_dd_pct"], 2)))
dres.sort(reverse=True)
for row in dres[:15]:
    print(row)

print("== slow EMA ==")
sres = []
for fast, slow in ((30, 120), (30, 180), (60, 180), (60, 240), (45, 120), (20, 120)):
    for trail in (60, 100, 150, 250):
        for stop in (150, 250, 400):
            for tp in (0, 200, 400):
                r = simulate(slow_ema_decide(fast, slow, trail, stop, tp))
                sres.append((r["pnl"], "slowEMA", (fast, slow, trail, stop, tp),
                             r["trades"], round(r["max_dd_pct"], 2)))
sres.sort(reverse=True)
for row in sres[:15]:
    print(row)
