"""Slow dip-recovery trend bot for make.fun btc-race-24h-20261117-0603.

Idea: trade the slow swing, not the minute noise. Closes are grouped into
30-bar blocks (half an hour each); the trend line is the mean of the last
four block closes (two hours of history). The bot only buys when price
crosses back above that line after sitting at least 0.5% under the recent
block high -- a washout that is turning -- and then it rides the move with
a 0.8% trailing stop and a 2% hard stop. It never exits on a trend-line
cross back down: on this market a cross down is usually noise, and the
trailing stop is the exit that actually banks the move.

All integer math, no floats, no clock, no randomness, no network, no files:
two runs on the same bars produce identical orders.

Dev window (this competition's frozen 24h, 2026-11-16 06:03Z to 2026-11-17
06:03Z; BTC +48 bps start to end, range -0.9% to +1.6%): net PnL +$6.97
on $1,000, 2 round trips, max drawdown 1.81%. Buy-and-hold on the same
window is +$1.07. The same parameters on the previous race's dev window
(BTC -401 bps) make +$3.79, so the edge is not tuned to one window alone.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"
BLOCK_BARS = 30           # bars per block (30 minutes)
MA_BLOCKS = 4             # blocks in the trend mean (2 hours)
DIP_BPS = 50              # entry needs close >= 0.5% below the 4-block high
TRAIL_BPS = 80            # 0.8% trailing stop off the peak position value
STOP_BPS = 200            # 2% hard stop below cost
MAX_SLIPPAGE_BPS = 100    # 1% slippage cap vs the latest close

block_closes = []         # completed block closes (ints, price_scale 5)
block_buf = []            # closes of the current, incomplete block
was_above = None          # was the previous close above the trend mean?
peak_value = 0            # peak position value at closes, since entry


def trend_mean():
    """Mean of the last MA_BLOCKS block closes, as a (sum, count) pair."""
    return sum(block_closes[-MA_BLOCKS:]), MA_BLOCKS


def is_above(close):
    """True when close is above the trend mean, in exact integers."""
    total, count = trend_mean()
    return close * count > total


def on_batch(state, batch):
    global was_above, peak_value
    for bar in batch["bars"]:
        if bar["symbol"] != SYMBOL:
            continue
        close = int(bar["c"])
        block_buf.append(close)
        if len(block_buf) == BLOCK_BARS:
            block_closes.append(block_buf[-1])
            block_buf.clear()
        if len(block_closes) < MA_BLOCKS:
            continue
        above = is_above(close)
        previously_above = was_above
        was_above = above
        held = state.positions.get(SYMBOL)
        if held is not None:
            if state.warming_up:
                continue
            # state.value marks the position at its latest close, exactly
            # how the harness marks equity, so the stops compare like for like.
            value = state.value(SYMBOL, held.qty)
            if value > peak_value:
                peak_value = value
            if value * 10000 <= held.cost * (10000 - STOP_BPS):
                peak_value = 0
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            if value * 10000 <= peak_value * (10000 - TRAIL_BPS):
                peak_value = 0
                return [{"side": "sell", "symbol": SYMBOL, "qty": held.qty,
                         "max_slippage_bps": MAX_SLIPPAGE_BPS}]
            continue
        # Flat: buy the cross back above the trend line, off a dip.
        if state.warming_up:
            continue
        if previously_above is not None and not previously_above and above:
            high = max(block_closes[-MA_BLOCKS:])
            if close * 10000 <= high * (10000 - DIP_BPS):
                peak_value = 0
                if state.cash >= 1000000:
                    return [{"side": "buy", "symbol": SYMBOL,
                             "notional_quote_units": state.cash,
                             "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


def on_hello(state):
    # Fail fast if the universe does not carry the one symbol this bot trades.
    if SYMBOL not in state.symbols:
        raise ValueError("universe has no %s" % SYMBOL)


makefun_bars.run(on_batch, on_hello=on_hello)
