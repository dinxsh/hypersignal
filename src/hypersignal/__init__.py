"""hypersignal -- a GoldRush-powered Hyperliquid signal engine.

Public surface:
    from hypersignal import run, Settings
    report = run(Settings.from_env(), offline=True)
    print(report.signal.regime)
"""
from .config import Settings, Thresholds
from .engine import HyperSignalReport, run
from .signal import RegimeSignal

__all__ = ["run", "Settings", "Thresholds", "HyperSignalReport", "RegimeSignal"]
__version__ = "0.1.0"
