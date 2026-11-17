"""Strategy search for btc-race-24h-20261117-0603 (research tooling, NOT shipped).

Fill model re-derived from this competition's RULES.txt:
- Orders decided on bar k fill at bar k+1's open.
- Fee 4 bps on fill; modelled slippage 2 bps (buy above open, sell below).
- Price impact: constant-product vs bar k+1's o_depth (micro-USDC):
  buy pays open * (1 + a/D), sell receives open / (1 + a/D), a = trade worth in USD.
- Final position flattened at last close vs its c_depth, same fee/slip/impact.
- All money in USD floats here (search only); the shipped bot uses integer math.
"""
import gzip
import json
import sys

KIT = "/home/hatch/workspace/makefun/btc-race-24h-20261117-0603-kit"


def load_bars():
    bars = [json.loads(l) for l in gzip.open(
        KIT + "/dataset/bars/CBBTC.ndjson.gz", "rt")]
    out = []
    for b in bars:
        out.append({
            "o": int(b["o"]) / 1e5,
            "c": int(b["c"]) / 1e5,
            "o_depth": int(b["o_depth"][0]) / 1e6,
            "c_depth": int(b["c_depth"][0]) / 1e6,
        })
    return out


BARS = load_bars()
START_CASH = 1000.0


def simulate(decide):
    """decide(state, k, bar) -> ('buy', notional) | ('sell',) | None.
    state: dict with cash, qty, cost, peak, equity history."""
    cash = START_CASH
    qty = 0.0          # BTC
    cost = 0.0         # USD cost basis of position (incl fees)
    peak = 0.0
    trades = 0
    pending = None     # (side, amount) to fill at next bar open
    equity_curve = []
    max_dd = 0.0
    peak_eq = START_CASH
    for k, bar in enumerate(BARS):
        # fill pending order at this bar's open
        if pending is not None:
            side, amt = pending
            pending = None
            o, D = bar["o"], bar["o_depth"]
            if side == "buy":
                fee = amt * 0.0004
                a = amt - fee
                fill = o * 1.0002 * (1 + a / D)
                q = a / fill
                qty += q
                cost = amt
                cash -= amt
                trades += 1
                peak = qty * bar["c"]
            else:
                val = qty * o
                fill = o / 1.0002 / (1 + val / D)
                gross = qty * fill
                fee = gross * 0.0004
                cash += gross - fee
                qty = 0.0
                cost = 0.0
                peak = 0.0
                trades += 1
        eq = cash + qty * bar["c"]
        if qty > 0:
            peak = max(peak, qty * bar["c"])
        equity_curve.append(eq)
        peak_eq = max(peak_eq, eq)
        max_dd = max(max_dd, (peak_eq - eq) / START_CASH)
        if k == len(BARS) - 1:
            break
        st = {"cash": cash, "qty": qty, "cost": cost, "peak": peak,
              "k": k, "equity": eq}
        order = decide(st, k, bar)
        if order is not None:
            side = order[0]
            if side == "buy" and qty == 0 and cash >= 1.0:
                pending = ("buy", cash)
                peak = 0.0
            elif side == "sell" and qty > 0:
                pending = ("sell", None)
    # final flatten at last close vs c_depth
    bar = BARS[-1]
    if qty > 0:
        val = qty * bar["c"]
        fill = bar["c"] / 1.0002 / (1 + val / bar["c_depth"])
        gross = qty * fill
        cash += gross * (1 - 0.0004)
        qty = 0.0
    return {"pnl": cash - START_CASH, "trades": trades,
            "max_dd_pct": max_dd * 100, "final_cash": cash}


def ema_series(closes, n):
    alpha = 2.0 / (n + 1)
    out = []
    e = None
    for c in closes:
        e = c if e is None else alpha * c + (1 - alpha) * e
        out.append(e)
    return out


CLOSES = [b["c"] for b in BARS]


def make_decide(fast, slow, dip_bps, trail_bps, stop_bps, tp_bps):
    ef = ema_series(CLOSES, fast)
    es = ema_series(CLOSES, slow)
    hi = []  # rolling max of last `slow` closes
    for k in range(len(CLOSES)):
        hi.append(max(CLOSES[max(0, k - slow + 1):k + 1]))

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
        # flat: enter on fast crossing above slow, with dip filter
        if k >= 1 and ef[k - 1] <= es[k - 1] and ef[k] > es[k]:
            if dip_bps == 0 or c <= hi[k] * (1 - dip_bps / 10000):
                return ("buy",)
        return None
    return decide


if __name__ == "__main__":
    best = []
    for fast in (6, 8, 12, 20):
        for slow in (21, 30, 60, 90):
            if fast >= slow:
                continue
            for dip in (0, 50, 100, 150):
                for trail in (40, 60, 100, 150):
                    for stop in (150, 200, 300):
                        for tp in (0, 150, 300):
                            r = simulate(make_decide(fast, slow, dip, trail, stop, tp))
                            best.append((r["pnl"], fast, slow, dip, trail, stop, tp,
                                         r["trades"], round(r["max_dd_pct"], 2)))
    best.sort(reverse=True)
    print("top 25 EMA-cross variants (pnl, fast, slow, dip, trail, stop, tp, trades, maxDD%):")
    for row in best[:25]:
        print(row)
    # buy-and-hold reference
    def bh(st, k, bar):
        if k == 0 and st["qty"] == 0:
            return ("buy",)
        return None
    print("buy-and-hold:", simulate(bh))
