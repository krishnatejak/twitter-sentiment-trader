import os
from datetime import datetime, timedelta
import pandas as pd
import argparse
from typing import List, Dict
from ..backtesting.backtest import Backtester
from ..config.settings import settings

class HandleAnalyzer:
    def __init__(self, handles: List[str], start_date: str, end_date: str):
        self.handles = handles
        self.start_date = start_date
        self.end_date = end_date
        self.results: Dict[str, Dict] = {}
        
    def analyze_handles(self):
        """Run backtests for all handles"""
        for handle in self.handles:
            print(f"\nAnalyzing handle: {handle}")
            try:
                backtester = Backtester(self.start_date, self.end_date)
                backtester.run_backtest(handle)
                
                self.results[handle] = {
                    'performance_metrics': backtester.performance_metrics,
                    'symbol_metrics': backtester.symbol_metrics,
                    'symbols_traded': list(backtester.symbols_traded)
                }
            except Exception as e:
                print(f"Error analyzing handle {handle}: {str(e)}")
    
    def generate_rankings(self) -> pd.DataFrame:
        """Generate rankings based on different metrics"""
        if not self.results:
            return pd.DataFrame()
            
        rankings_data = []
        for handle, data in self.results.items():
            metrics = data['performance_metrics']
            rankings_data.append({
                'handle': handle,
                'total_pnl': metrics.get('total_pnl', 0),
                'win_rate': metrics.get('win_rate', 0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                'profit_factor': metrics.get('profit_factor', 0),
                'max_drawdown': metrics.get('max_drawdown', 0),
                'total_trades': metrics.get('total_trades', 0),
                'symbols_traded': len(data['symbols_traded']),
                'avg_profit_per_trade': metrics.get('total_pnl', 0) / metrics.get('total_trades', 1)
            })
            
        df = pd.DataFrame(rankings_data)
        
        # Calculate composite score
        df['score'] = (
            df['sharpe_ratio'].rank() +
            df['profit_factor'].rank() +
            df['win_rate'].rank() -
            abs(df['max_drawdown']).rank()
        ) / 4
        
        return df.sort_values('score', ascending=False)
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report"""
        if not self.results:
            return "No analysis results available."
            
        rankings = self.generate_rankings()
        
        report = []
        report.append("=== Twitter Handle Analysis Report ===\n")
        
        report.append("Top Performing Handles:")
        for _, row in rankings.head().iterrows():
            report.append(f"\n{row['handle']}:")
            report.append(f"  Total P&L: ₹{row['total_pnl']:,.2f}")
            report.append(f"  Win Rate: {row['win_rate']:.2%}")
            report.append(f"  Sharpe Ratio: {row['sharpe_ratio']:.2f}")
            report.append(f"  Profit Factor: {row['profit_factor']:.2f}")
            report.append(f"  Symbols Traded: {row['symbols_traded']}")
            
        report.append("\nSymbol Analysis:")
        for handle, data in self.results.items():
            report.append(f"\n{handle} - Top Symbols:")
            symbol_metrics = pd.DataFrame.from_dict(data['symbol_metrics'], orient='index')
            if not symbol_metrics.empty:
                top_symbols = symbol_metrics.nlargest(3, 'total_pnl')
                for idx, sym_data in top_symbols.iterrows():
                    report.append(f"  {idx}:")
                    report.append(f"    P&L: ₹{sym_data['total_pnl']:,.2f}")
                    report.append(f"    Win Rate: {sym_data['win_rate']:.2%}")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Analyze multiple Twitter handles for trading performance')
    parser.add_argument('--handles', nargs='+', required=True, help='List of Twitter handles to analyze')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze (default: 30)')
    parser.add_argument('--output', type=str, help='Output CSV file for results')
    
    args = parser.parse_args()
    
    # Set dates
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    # Run analysis
    analyzer = HandleAnalyzer(args.handles, start_date, end_date)
    analyzer.analyze_handles()
    
    # Print report
    print(analyzer.generate_report())
    
    # Save results if output file specified
    if args.output:
        rankings = analyzer.generate_rankings()
        rankings.to_csv(args.output, index=False)

if __name__ == "__main__":
    main()