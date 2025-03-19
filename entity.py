from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LinkRequest(BaseModel):
    link: str
    expires_at: Optional[datetime] = None

class CustomLinkRequest(BaseModel):
    link: str
    custom_alias: str
    expires_at: Optional[datetime] = None