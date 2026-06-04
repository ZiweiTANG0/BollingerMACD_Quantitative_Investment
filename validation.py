"""
validation.py
=============
Statistical validation for the Bollinger-MACD backtest.

The point of this module is NOT to make the strategy look good. It is to ask,
honestly, three questions a backtest cannot answer on its own:

    1. Are the inputs even suitable for the modelling assumptions?
       -> Stationarity tests (Augmented Dickey-Fuller) on price vs. returns.

    2. How uncertain are the headline performance numbers?
       -> Moving-block bootstrap confidence intervals for the Sharpe ratio and
          for the mean daily active return (strategy minus benchmark). Block
          resampling is used because daily returns are autocorrelated, so an
          i.i.d. bootstrap would understate the uncertainty.

    3. Is the result distinguishable from luck?
       -> A Monte-Carlo permutation test: re-run the SAME backtesting engine on
          many random-timing strategies that trade as often, and hold as long,
          as the real one. If the real Sharpe sits comfortably inside that null
          distribution, the signal timing adds no measurable edge.

All three are designed to report whatever they find, including a negative
result. A strategy whose edge is not statistically robust is a finding, not a
failure.

Usage
-----
    from backtest import VectorizedBacktest
    from validation import run_all

    results = bt.run(data, signals, verbose=False)   # your existing call
    report = run_all(results, data, signals, VectorizedBacktest,
                     backtest_kwargs=dict(initial_capital=1_000_000,
                                          commission=0.00025, slippage=0.003,
                                          position_size=0.8))
"""

from __future__ import annotations
import numpy as np
import pandas as pd

TRADING_DAYS = 252


# --------------------------------------------------------------------------- #
# 1. Stationarity
# --------------------------------------------------------------------------- #
def adf_report(price: pd.Series, returns: pd.Series) -> dict:
    """Augmented Dickey-Fuller test on the price level and on returns.

    H0: a unit root is present (the series is non-stationary).
    We expect to FAIL to reject H0 for prices (non-stationary) and to REJECT
    it for returns (stationary) -- the standard justification for modelling
    returns rather than prices.
    """
    try:
        from statsmodels.tsa.stattools import adfuller
    except ImportError:
        print("  [skipped] install statsmodels to run the ADF test: pip install statsmodels")
        return {}

    out = {}
    for name, series in (("price", price), ("returns", returns)):
        s = pd.Series(series).dropna()
        stat, pval, *_ = adfuller(s, autolag="AIC")
        stationary = pval < 0.05
        out[name] = {"adf_stat": float(stat), "p_value": float(pval), "stationary": bool(stationary)}

    print("\n[1] STATIONARITY (Augmented Dickey-Fuller)")
    print(f"    price   : ADF={out['price']['adf_stat']:+.3f}  p={out['price']['p_value']:.3f}"
          f"  -> {'stationary' if out['price']['stationary'] else 'NON-stationary (unit root)'}")
    print(f"    returns : ADF={out['returns']['adf_stat']:+.3f}  p={out['returns']['p_value']:.3f}"
          f"  -> {'stationary' if out['returns']['stationary'] else 'NON-stationary'}")
    return out


# --------------------------------------------------------------------------- #
# 2. Moving-block bootstrap confidence intervals
# --------------------------------------------------------------------------- #
def _moving_block_bootstrap(x: np.ndarray, statistic, n_boot=2000, block=None, seed=0):
    """Generic moving-block bootstrap. Preserves short-range autocorrelation by
    resampling contiguous blocks rather than individual observations."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    n = len(x)
    if block is None:                       # rule of thumb ~ n**(1/3)
        block = max(1, int(round(n ** (1 / 3))))
    n_blocks = int(np.ceil(n / block))
    max_start = n - block
    samples = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:n]
        samples[b] = statistic(x[idx])
    return samples, block


def _ann_sharpe(daily_returns: np.ndarray) -> float:
    sd = np.std(daily_returns, ddof=1)
    return (np.mean(daily_returns) / sd) * np.sqrt(TRADING_DAYS) if sd > 0 else 0.0


def bootstrap_cis(strategy_returns: pd.Series, benchmark_returns: pd.Series,
                  n_boot=2000, seed=0) -> dict:
    """95% bootstrap CIs for (a) the annualised Sharpe ratio and (b) the mean
    daily active return (strategy - benchmark)."""
    strat = pd.Series(strategy_returns).dropna()
    point_sharpe = _ann_sharpe(strat.values)
    sharpe_samples, block = _moving_block_bootstrap(strat.values, _ann_sharpe, n_boot, seed=seed)
    s_lo, s_hi = np.percentile(sharpe_samples, [2.5, 97.5])

    aligned = pd.concat([strategy_returns, benchmark_returns], axis=1).dropna()
    active = (aligned.iloc[:, 0] - aligned.iloc[:, 1]).values
    point_active = float(np.mean(active))
    active_samples, _ = _moving_block_bootstrap(active, np.mean, n_boot, seed=seed)
    a_lo, a_hi = np.percentile(active_samples, [2.5, 97.5])
    # two-sided bootstrap p-value for "mean active return = 0"
    p_active = 2 * min((active_samples <= 0).mean(), (active_samples >= 0).mean())

    out = {
        "block_length": block,
        "sharpe": {"point": point_sharpe, "ci95": (float(s_lo), float(s_hi)),
                   "excludes_zero": bool(s_lo > 0 or s_hi < 0)},
        "mean_active_return": {"point": point_active, "ci95": (float(a_lo), float(a_hi)),
                               "p_value": float(p_active), "excludes_zero": bool(a_lo > 0 or a_hi < 0)},
    }
    print(f"\n[2] BOOTSTRAP CONFIDENCE INTERVALS  (moving block, L={block}, B={n_boot})")
    print(f"    Annualised Sharpe : {point_sharpe:+.3f}   95% CI [{s_lo:+.3f}, {s_hi:+.3f}]"
          f"   -> {'excludes 0' if out['sharpe']['excludes_zero'] else 'INCLUDES 0 (not robust)'}")
    print(f"    Mean active ret/d : {point_active:+.2e}  95% CI [{a_lo:+.2e}, {a_hi:+.2e}]"
          f"   p={p_active:.3f}  -> {'edge significant' if out['mean_active_return']['excludes_zero'] else 'NOT significant'}")
    return out


# --------------------------------------------------------------------------- #
# 3. Monte-Carlo permutation test against random-timing strategies
# --------------------------------------------------------------------------- #
def _holding_periods_and_count(trades: list, index: pd.DatetimeIndex):
    """Recover (number of round-trip trades, list of holding lengths in bars)
    from the trade log, by pairing each BUY with the next SELL."""
    pos = {d: i for i, d in enumerate(index)}
    holds, entries = [], []
    open_i = None
    for t in trades:
        di = pos.get(t["date"])
        if di is None:
            continue
        if t["action"] == "BUY":
            open_i = di
        elif t["action"] == "SELL" and open_i is not None:
            holds.append(max(1, di - open_i))
            entries.append(open_i)
            open_i = None
    return len(holds), holds


def _random_signals(index, n_trades, holds, rng):
    """Build a 1/-1/0 signal series with `n_trades` non-overlapping long
    positions placed at random, each held for a duration sampled from `holds`."""
    n = len(index)
    sig = pd.Series(0, index=index)
    if n_trades == 0 or not holds:
        return sig
    placed, attempts, occupied = 0, 0, np.zeros(n, dtype=bool)
    while placed < n_trades and attempts < n_trades * 50:
        attempts += 1
        dur = int(rng.choice(holds))
        start = int(rng.integers(0, n - dur - 1)) if n - dur - 1 > 0 else 0
        if occupied[start:start + dur + 1].any():
            continue
        occupied[start:start + dur + 1] = True
        sig.iloc[start] = 1
        sig.iloc[min(start + dur, n - 1)] = -1
        placed += 1
    return sig


def monte_carlo_random_null(results: dict, data: pd.DataFrame, trades: list,
                            BacktestClass, backtest_kwargs=None, n_sim=500, seed=0) -> dict:
    """Compare the real strategy against many random-timing strategies that
    trade as often and hold as long. Empirical one-sided p-value = fraction of
    random strategies whose Sharpe is at least as high as the real one."""
    backtest_kwargs = backtest_kwargs or {}
    index = data.index
    n_trades, holds = _holding_periods_and_count(trades, index)
    real_sharpe = float(results["metrics"].get("Sharpe Ratio", _ann_sharpe(results["data"]["returns"].dropna().values)))

    rng = np.random.default_rng(seed)
    null_sharpe = np.empty(n_sim)
    for k in range(n_sim):
        sig = _random_signals(index, n_trades, holds, rng)
        r = BacktestClass(**backtest_kwargs).run(data, sig, verbose=False)
        null_sharpe[k] = _ann_sharpe(r["data"]["returns"].dropna().values)

    p_value = float((null_sharpe >= real_sharpe).mean())
    pct = float((null_sharpe < real_sharpe).mean() * 100)
    out = {"real_sharpe": real_sharpe, "n_trades_matched": n_trades, "n_sim": n_sim,
           "null_mean_sharpe": float(np.mean(null_sharpe)),
           "null_ci90": (float(np.percentile(null_sharpe, 5)), float(np.percentile(null_sharpe, 95))),
           "p_value": p_value, "percentile_of_real": pct}
    print(f"\n[3] MONTE-CARLO RANDOM-TIMING NULL  (n_sim={n_sim}, matched trades={n_trades})")
    print(f"    Real Sharpe        : {real_sharpe:+.3f}")
    print(f"    Random Sharpe mean : {out['null_mean_sharpe']:+.3f}"
          f"   90% range [{out['null_ci90'][0]:+.3f}, {out['null_ci90'][1]:+.3f}]")
    print(f"    Real beats {pct:.1f}% of random strategies   (p={p_value:.3f})")
    print(f"    -> {'timing adds a real edge' if p_value < 0.05 else 'NOT distinguishable from random timing'}")
    return out


# --------------------------------------------------------------------------- #
# 4. Sub-period stability
# --------------------------------------------------------------------------- #
def subperiod_stability(strategy_returns: pd.Series, n_periods=4) -> dict:
    """Split the realised return series into equal time blocks and report the
    annualised Sharpe of each, to see whether a (weak) edge is consistent or
    driven by a single window."""
    r = pd.Series(strategy_returns).dropna()
    chunks = np.array_split(r.values, n_periods)
    sharpes = [round(_ann_sharpe(c), 3) for c in chunks]
    print(f"\n[4] SUB-PERIOD STABILITY  ({n_periods} equal windows)")
    print(f"    Sharpe per window  : {sharpes}")
    print(f"    -> {'broadly consistent' if min(sharpes) > 0 else 'inconsistent / driven by some periods'}")
    return {"sharpe_by_window": sharpes}


# --------------------------------------------------------------------------- #
# Orchestrator
# --------------------------------------------------------------------------- #
def run_all(results, data, signals, BacktestClass, backtest_kwargs=None,
            n_boot=2000, n_sim=500, seed=0) -> dict:
    print("=" * 64)
    print("STATISTICAL VALIDATION")
    print("=" * 64)
    df = results["data"]
    report = {}
    report["stationarity"] = adf_report(df["benchmark"], df["benchmark_returns"])
    report["bootstrap"] = bootstrap_cis(df["returns"], df["benchmark_returns"], n_boot=n_boot, seed=seed)
    report["monte_carlo"] = monte_carlo_random_null(results, data, results["trades"],
                                                    BacktestClass, backtest_kwargs, n_sim=n_sim, seed=seed)
    report["stability"] = subperiod_stability(df["returns"])
    print("\n" + "=" * 64)
    return report
