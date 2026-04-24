"""
main.py

Orchestrates the full trading bot pipeline:
    MarketScanner → SignalEngine → TradeSimulator

Each cycle:
  1. Scan for active markets
  2. Generate signals from market data
  3. Execute trades on signals
  4. Update open positions (check take-profit / stop-loss)
  5. Log a cycle summary

Run:
    python main.py
"""

import logging
import time

from market_scanner.scanner import MarketScanner
from signal_engine.engine import SignalEngine
from signal_engine.strategies.momemtum import MomentumStrategy
from trade_simulator.executor import TradeExecutor
from trade_simulator.simulator import TradeSimulator

logger = logging.getLogger("polybot.main")

# ── Constants ─────────────────────────────────────────────────────────────────

CYCLE_DELAY_SECONDS: float = 4.0  # pause between polling cycles
MAX_CYCLES: int | None = None      # None = run forever; set an int for testing


# ── Initialisation ────────────────────────────────────────────────────────────

def build_components() -> tuple[MarketScanner, SignalEngine, TradeSimulator]:
    """Construct and wire all bot components."""
    scanner = MarketScanner(min_volume=10_000)

    engine = SignalEngine(
        strategies=[
            MomentumStrategy(threshold=0.01),
        ]
    )

    simulator = TradeSimulator(
        position_size=100.0,
        max_open_trades=5,
    )

    return scanner, engine, simulator


# ── Cycle logic ───────────────────────────────────────────────────────────────

def run_cycle(
    scanner: MarketScanner,
    engine: SignalEngine,
    executor: TradeExecutor,
    cycle_num: int,
) -> None:
    """Execute one full scan → signal → trade → update cycle."""

    logger.info("━━━ Cycle %d ━━━", cycle_num)

    # 1. Fetch markets
    markets = scanner.get_active_markets()
    market_index = {m.id: m for m in markets}
    logger.info("Markets scanned: %d", len(markets))

    # 2. Generate signals
    signals = engine.generate_signals(markets)
    logger.info("Signals generated: %d", len(signals))

    # 3. Execute trades
    trades_opened = 0
    for signal in signals:
        market = market_index.get(signal.market_id)
        if market is None:
            logger.warning("Signal for unknown market %s — skipping", signal.market_id)
            continue

        trade = executor.execute(signal, market)
        if trade is not None:
            trades_opened += 1
            logger.info(
                "Trade opened  │ %s %s  entry=%.4f  tp=%.4f  sl=%.4f",
                trade.position.market_id,
                trade.position.outcome,
                trade.position.entry_price,
                trade.take_profit,
                trade.stop_loss,
            )

    # 4. Update open positions (check exit levels)
    trades_closed = 0
    for market in markets:
        for result in executor.update_market(market):
            trades_closed += 1
            logger.info(
                "Trade closed  │ %s %s  exit=%.4f  P&L=$%+.2f  %s",
                result.market_id,
                result.outcome,
                result.exit_price,
                result.profit_loss,
                result.result.value,
            )

    # 5. Cycle summary
    logger.info(
        "Summary       │ opened=%d  closed=%d  open=%d  total P&L=$%+.2f",
        trades_opened,
        trades_closed,
        len(executor.get_open_positions()),
        executor.get_total_pnl(),
    )


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    logger.info("Starting Polybot")

    scanner, engine, simulator = build_components()

    cycle = 1
    try:
        while MAX_CYCLES is None or cycle <= MAX_CYCLES:
            try:
                run_cycle(scanner, engine, simulator, cycle)
            except Exception:
                logger.exception("Unhandled error in cycle %d — continuing", cycle)

            cycle += 1
            time.sleep(CYCLE_DELAY_SECONDS)

    except KeyboardInterrupt:
        logger.info("Interrupted — shutting down")

    finally:
        closed = simulator.portfolio.get_results()
        logger.info(
            "Shutdown │ cycles=%d  closed_trades=%d  final P&L=$%+.2f",
            cycle - 1,
            len(closed),
            sum(r.profit_loss for r in closed),
        )


if __name__ == "__main__":
    main()