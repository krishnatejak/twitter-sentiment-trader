import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import argparse
from .backtest import Backtester
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description='Run backtesting for Twitter Sentiment Trading')
    parser.add_argument('--handle', type=str, required=True, help='Twitter handle to analyze')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30, help='Number of days to backtest (default: 30)')
    parser.add_argument('--output', type=str, help='Output CSV file for results')
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Set dates
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    # Initialize and run backtester
    backtester = Backtester(start_date, end_date)
    backtester.run_backtest(args.handle)
    
    # Print report
    print(backtester.generate_report())
    
    # Save results if output file specified
    if args.output:
        results = {
            'handle': args.handle,
            'start_date': start_date,
            'end_date': end_date,
            **backtester.performance_metrics,
            'symbols_traded': list(backtester.symbols_traded),
            'symbol_metrics': backtester.symbol_metrics
        }
        
        pd.DataFrame([results]).to_csv(args.output, index=False)

if __name__ == "__main__":
    main()