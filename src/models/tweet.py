from datetime import datetime
from pydantic import BaseModel

class Tweet(BaseModel):
    id: str
    text: str
    author: str
    created_at: datetime
    sentiment: str = None