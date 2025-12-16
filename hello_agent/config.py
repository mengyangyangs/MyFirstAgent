"""配置管理"""
import os 
from typing import Optional,Dict,Any
from pydantic import BaseModel

class Config(BaseModel):
    """HelloAgents配置类"""

    # LLM配置
    default_model:str = "gpt-3.5-turbo"
    default_provider:str = "openai"

    # Gemini配置
    # default_model:str = "gemini-2.5-flash"
    # default_provider:str = "gemini"
    # temperature:float = 0.7
    # max_tokens:Optional[int] = None

    # 系统配置
    debug:bool = False
    log_level:str = "INFO"

    # 其他配置
    max_history_length:int = 100

    @classmethod
    def from_env(cls) -> "Config":
        """
        一个类方法，用于从环境变量中加载配置并创建一个新的Config实例。
        这使得配置可以通过外部环境变量进行动态修改，而无需更改代码。
        """
        # 创建并返回一个新的Config类的实例
        return cls(
            # 从环境变量 "DEBUG" 读取调试模式配置。如果未设置，默认为 "false"。
            # .lower() == "true" 的方式将字符串 "true" 或 "false" 转换为布尔值。
            debug = os.getenv("DEBUG","false").lower() == "true",
            
            # 从环境变量 "LOG_LEVEL" 读取日志级别，如果未设置，则默认值为 "INFO"。
            log_level = os.getenv("LOG_LEVEL","INFO"),
            
            # 从环境变量 "TEMPERATURE" 读取温度值，并将其转换为浮点数，默认值为 0.7。
            temperature = float(os.getenv("TEMPERATURE","0.7")),
            
            # 从环境变量 "MAX_TOKENS" 读取最大token数。
            # 如果环境变量存在，则将其转换为整数；否则，设置为None。
            max_tokens = int(os.getenv("MAX_TOKENS")) if os.getenv("MAX_TOKENS") else None,
        )

    def to_dict(self) -> Dict[str,Any]:
        return self.dict()