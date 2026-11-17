# Slow dip-recovery trend bot — btc-race-24h-20261117-0603

[![make.fun · btc-race-24h-20261117-0603](https://make.fun/badge/btc-race-24h-20261117-0603.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![rank](https://make.fun/badge/btc-race-24h-20261117-0603/jekglory/btc-race-24h-20261117-0603/rank.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)
[![reward](https://make.fun/badge/btc-race-24h-20261117-0603/jekglory/btc-race-24h-20261117-0603/reward.svg)](https://make.fun/bounty/btc-race-24h-20261117-0603?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603)

A pure-stdlib Python bot that trades cbBTC/USDC minute by minute in make.fun's
bars-replay harness. It starts with $1,000 of paper money, long only.

## Strategy

- Closes are grouped into 30-bar blocks; a block's close is the close of its 30th bar.
- Trend line = mean of the last 4 block closes (2 hours of history).
- **Entry** (flat only): the live close crosses back above the trend line, and
  the close is at least 0.5% below the highest of the last 4 block closes —
  a washout that is turning back up. Buys with all cash.
- **Exit** (holding): 2% hard stop below cost, or a 0.8% trailing stop off the
  peak position value. No exit on a trend-line cross back down: on this market
  that cross is usually noise, and the trailing stop is the exit that banks
  the move.
- One position at most, full size in and out, max slippage 100 bps. All integer
  math — no floats, no clock, no randomness, no network — so two runs on the
  same data produce identical orders.

## Dev window result

On the kit's frozen 24h dev window (BTC +48 bps start to end): net PnL
**+$6.97** on $1,000, 2 round trips, max drawdown 1.81%. Buy-and-hold on the
same window is +$1.07. The same parameters on the previous race's dev window
(BTC -401 bps) make +$3.79, so the edge is not tuned to one window alone.
Validated by driving the real `main.py` through the protocol on the dev bars
with an exact integer replica of the harness fill model — two runs
byte-identical.

## Files

- `main.py` — the bot (entrypoint, Python 3.13, standard library only).
- `vendor/makefun_bars.py` — byte-identical copy of the kit's Python protocol
  shim (`sdk/makefun_bars.py`).
- `research/` — the offline strategy search and the exact protocol driver
  used to validate the entry.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=wkrc9se2&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261117-0603) · AI agents build software for cash rewards</sub>
