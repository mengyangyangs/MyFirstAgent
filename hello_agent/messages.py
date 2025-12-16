"""消息系统"""
from typing import Optional,Dict,Any,Literal
from datetime import datetime
from pydantic import BaseModel

MessageRole = Literal["user","assistant","system","tool","question"]

class Message(BaseModel):
    """消息类"""

    content:str
    role:MessageRole
    timestamp:datetime = None
    metadata:Optional[Dict[str,Any]] = None
    
    def __init__(self,content:str,role:MessageRole,**kwargs):
        super().__init__(
            content=content,
            role=role,
            timestamp=kwargs.get("timestamp",datetime.now()),
            metadata=kwargs.get("metadata",{})
        )

    def to_dict(self,api_type:Literal["openai","gemini"] = "openai") -> Dict[str,Any]:
        """
        转换为字典格式。
        默认为OpenAI API格式，可指定 api_type = "gemini"来获取Gemini API格式
        Args:
            api_type:目标API格式("openai"或"gemini")
        Returns:
            一个兼容目标API格式的字典
        """
        # Gemini API格式
        if api_type == "gemini":
            # 关键区别 Gemini使用"model"角色，而不是"assistant"
            gemini_role = "model" if self.role == "assistant" else self.role

            # # 等价于
            # if self.role == "assistant":
            #     gemini_role = "model"
            # else:
            #     gemini_role = self.role
            
            return {
                "role":gemini_role,
                "parts":[self.content]
            }

        elif api_type == "openai":

            return {
                "role":self.role,
                "content":[self.content]
            }

        else:
            raise ValueError(f"不支持api_type:{api_type}.支持的是'openai'或'gemini'")

    # def to_dict(self) -> Dict[str,Any]:
    #     """
    #         转换为字典格式(OpenAI API格式)
    #     """
    #     return {
    #         "role":self.role,
    #         "content":self.content
    #     }

    def __str__(self) -> str:
        return f"[{self.role}] {self.content}"