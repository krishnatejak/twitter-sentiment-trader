import pandas as pd
from typing import Dict, List
from ..models.trade import Trade

class HandlePerformance:
    def __init__(self):
        self.handle_metrics: Dict[str, Dict] = {}

    def calculate_handle_metrics(self, handle: str, trades: List[Trade]):
        """Calculate performance metrics for a specific handle"""
        if not trades:
            return

        # Calculate metrics
        total_trades = len(trades)
        profitable_trades = len([t for t in trades if t.pnl > 0])
        win_rate = profitable_trades / total_trades if total_trades > 0 else 0
        total_pnl = sum(t.pnl for t in trades)
        avg_return = total_pnl / total_trades if total_trades > 0 else 0

        self.handle_metrics[handle] = {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_return': avg_return
        }

    def get_handle_ranking(self) -> pd.DataFrame:
        """Get handles ranked by performance"""
        if not self.handle_metrics:
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(self.handle_metrics, orient='index')
        return df.sort_values('total_pnl', ascending=False)