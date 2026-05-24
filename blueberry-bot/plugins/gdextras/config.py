from pydantic import BaseModel, field_validator

class Config(BaseModel):
    render_server_uri:str="ws://localhost:9080"