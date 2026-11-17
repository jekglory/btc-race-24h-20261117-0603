# btc-race-24h-20261117-0603 — checkpoint log

- Competition: btc-race-24h-20261117-0603, $250, entries close 2026-11-17T12:03:00Z (19:03 WIB), result due 2026-12-10.
- Kit: ~/workspace/makefun/btc-race-24h-20261117-0603-kit (downloaded from https://make.fun/c/btc-race-24h-20261117-0603/kit, 7,281,890 bytes). Dev window 1440 bars, 0 gaps, 2026-11-16 ~06:03Z to 2026-11-17 06:03Z.
- Dev window shape: start $64,461.04, end $64,775.95 (+48 bps), min $63,874.36, max $65,466.84. Buy-and-hold approx +$2.30 net after ~26 bps round-trip costs.
- Quota checked 2026-11-17 ~06:58Z: day cap 10, taken 0, left 10; hard limit 20 left; can_submit true.
- Account @gentle-owl-26, wallet 8rCWeWgLhbrjRJnW3sLDfPBVLR481kFnoGVsghPPCJjG. API key via command substitution only.
- Strategy: fresh bot (NOT a copy of the 15 Nov dip-recovery bot). Search in progress.

## Strategy decision (2026-11-17 ~07:10Z)
- Searched 3 families on the NEW dev window (search.py/search2.py/search3.py/search4.py):
  fast EMA-cross whipsaws to -$111 (70 fills); slow EMA worst -$26; Donchian best +$2.88.
  Block-MA dip-recovery best: (10,8,50,80) +$9.43 but -$18.86 on the OLD window.
- Cross-window pick (positive on BOTH windows, 192-combo grid, only 4 combos both-positive):
  BLOCK 30 bars, MA 4 blocks (120 min), DIP 50 bps, TRAIL 80 bps, STOP 200 bps,
  NO cross-down exit. New window +$6.97 (4 fills, maxDD 1.81%), old window +$3.79
  (6 fills, maxDD 2.38%). Neighbours flip sign, so this is a balance choice, not a max.
- Fill model verified against the kit's own harness source (sim/bars/engine.ts):
  buy price = open*(10000+2)*M/10000, M = 1+spend/D (single hop); fee 4 bps;
  sell price = open*(10000-2)/(10000*M); cost basis += buy notional, sells scale it down.
- Next: write main.py fresh (integer math), validate with an exact protocol driver x2 runs.

## Protocol-driver validation (2026-11-17 ~07:15Z)
- Real main.py driven through the exact protocol driver (research/run_bot.py,
  integer fill model copied from the kit's harness source): run1 PnL +$6.97,
  run2 PnL +$6.97, action logs byte-identical, 4 fills, fees $1.61, maxDD 1.81%.
  Matches the float search sim exactly (+$6.97). DEV GATE PASSES on local grade.
- Fills: buy $64,365.32 -> sell $64,754.74; buy $64,625.92 -> sell $64,788.56.
  Both round trips net positive; no flatten needed (exited via trailing stop).
- Next: repo + README + LICENSE + owner.json, commit, push, kit check, submit.
