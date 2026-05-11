from pydantic import BaseModel


class Config(BaseModel):
    say_request_url:str="http://192.168.31.206:23456/voice/gpt-sovits?id=0&preset=default2&text={$text}"
    
    redis_host:str='localhost'
    redis_port:int=6379