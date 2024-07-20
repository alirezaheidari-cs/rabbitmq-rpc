import json
from typing import Optional, Any, Type, TypeVar
from pydantic import BaseModel, Field, ValidationError, validator
from decouple import config, UndefinedValueError

T = TypeVar('T')

def env_var(field_name: str, default: T, cast_type: Type[T] = str) -> T:
    try:
        return config(field_name, default=default, cast=cast_type)
    except UndefinedValueError:
        return default

class RabbitMQConfig(BaseModel):
    host: str = Field(default_factory=lambda: env_var("RABBITMQ_HOST", "localhost", str))
    port: int = Field(default_factory=lambda: env_var("RABBITMQ_PORT", 5672, int))
    user: str = Field(default_factory=lambda: env_var("RABBITMQ_USER", "rabbitmq_user", str))
    password: str = Field(default_factory=lambda: env_var("RABBITMQ_PASSWORD", "rabbitmq_password", str))
    vhost: Optional[str] = Field(default_factory=lambda: env_var("RABBITMQ_VHOST", "/", str))
    ssl_connection: bool = Field(default_factory=lambda: env_var("RABBITMQ_SSL_CONNECTION", False, bool))
    url: Optional[str] = None

    @validator('port')
    def validate_port(cls, value: int) -> int:
        if not (1 <= value <= 65535):
            raise ValueError('Port must be between 1 and 65535')
        return value

    @validator('vhost', pre=True, always=True)
    def validate_vhost(cls, value: Optional[str]) -> str:
        return value or "/"

    def get_url(self) -> str:
        if self.url:
            return self.url
        vhost = self.vhost if self.vhost != "/" else ""
        return f"amqp{'s' if self.ssl_connection else ''}://{self.user}:{self.password}@{self.host}:{self.port}/{vhost}"

    def __repr__(self) -> str:
        attributes = self.dict(exclude={"url"})
        attributes['url'] = self.get_url()
        attributes_str = json.dumps(attributes, indent=4)[1:-1]
        return f"{self.__class__.__name__}({attributes_str})"

    def __str__(self) -> str:
        return self.__repr__()

    class Config:
        validate_assignment = True
