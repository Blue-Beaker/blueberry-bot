from pydantic import BaseModel, field_validator

class Config(BaseModel):
    max_msg_retries: int = 10
    msg_retry_interval: float = 3
    msg_retry_interval_increment: float = 5