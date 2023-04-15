from pydantic import Extra, BaseModel


class Config(BaseModel, extra=Extra.ignore):
    last_operation_time: int = 10
