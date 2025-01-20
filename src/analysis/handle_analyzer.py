import os
from datetime import datetime, timedelta
import pandas as pd
import argparse
from typing import List, Dict
import logging
from dotenv import load_dotenv
from ..backtesting.backtest import Backtester
from ..config.settings import settings
from ..config.validator import ConfigValidator

logger = logging.getLogger(__name__)

class HandleAnalyzer:
    def __init__(self, handles: List[str], start_date: str, end_date: str):
        logger.info(f"Initializing HandleAnalyzer with dates: {start_date} to {end_date}")
        logger.info(f"Handles to analyze: {handles}")
        
        # Load environment variables
        load_dotenv()
        
        # Validate configuration
        logger.info("Validating configuration and testing connections")
        try:
            ConfigValidator.validate_all()
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise

        self.handles = handles
        self.start_date = start_date
        self.end_date = end_date
        self.results: Dict[str, Dict] = {}
        
    def analyze_handles(self):
        """Run backtests for all handles"""
        logger.info("Starting handle analysis")
        
        for handle in self.handles:
            logger.info(f"\nAnalyzing handle: {handle}")
            try:
                logger.debug(f"Creating backtester for {handle}")
                backtester = Backtester(self.start_date, self.end_date)
                
                logger.info(f"Running backtest for {handle}")
                backtester.run_backtest(handle)
                
                logger.debug(f"Storing results for {handle}")
                self.results[handle] = {
                    'performance_metrics': backtester.performance_metrics,
                    'symbol_metrics': backtester.symbol_metrics,
                    'symbols_traded': list(backtester.symbols_traded)
                }
                
                logger.info(f"Successfully analyzed {handle}")
                logger.debug(f"Results for {handle}: {self.results[handle]}")
                
            except Exception as e:
                logger.error(f"Error analyzing handle {handle}: {str(e)}", exc_info=True)
    
    def generate_rankings(self) -> pd.DataFrame:
        """Generate rankings based on different metrics"""
        logger.info("Generating handle rankings")
        
        if not self.results:
            logger.warning("No results available for ranking")
            return pd.DataFrame()
            
        rankings_data = []
        for handle, data in self.results.items():
            logger.debug(f"Processing rankings for {handle}")
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

def main():
    parser = argparse.ArgumentParser(description='Analyze multiple Twitter handles for trading performance')
    parser.add_argument('--handles', nargs='+', required=True, help='List of Twitter handles to analyze')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=30, help='Number of days to analyze (default: 30)')
    parser.add_argument('--output', type=str, help='Output CSV file for results')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting analysis with arguments:")
    logger.info(f"Handles: {args.handles}")
    logger.info(f"Debug mode: {args.debug}")
    
    # Set dates
    if args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
    
    logger.info(f"Analysis period: {start_date} to {end_date}")
    
    try:
        # Run analysis
        analyzer = HandleAnalyzer(args.handles, start_date, end_date)
        analyzer.analyze_handles()
        
        # Generate and print report
        rankings = analyzer.generate_rankings()
        print("\nAnalysis Results:")
        print(rankings)
        
        # Save results if output file specified
        if args.output:
            logger.info(f"Saving results to {args.output}")
            rankings.to_csv(args.output, index=False)
            
    except Exception as e:
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()