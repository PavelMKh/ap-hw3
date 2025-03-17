from pydantic import BaseModel

class LinkRequest(BaseModel):
    link: str