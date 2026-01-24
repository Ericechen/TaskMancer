from pydantic import BaseModel

class RootPathRequest(BaseModel):
    path: str

class CommandRequest(BaseModel):
    path: str
    action: str 
