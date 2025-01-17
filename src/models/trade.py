from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class Trade(BaseModel):
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    entry_time: datetime
    exit_time: Optional[datetime]
    tweet_id: str
    handle: str
    sentiment: str
    pnl: Optional[float]
    status: str  # 'OPEN' or 'CLOSED'