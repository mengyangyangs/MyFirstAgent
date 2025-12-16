import os
from typing import Optional
from openai import OpenAI # 穷人家的孩子没有openai的api，所以使用gemini的api
import google.generativeai as genai
from hello_agents import HelloAgentsLLM

class MyLLM(HelloAgentsLLM):
    def __init__(
        self,
        model:Optional[str] = None,
        api_key:Optional[str] = None,
        base_url:Optional[str] = None,
        provider:Optional[str] = "auto",
        **kwargs
    ):
    
        # 检查provider是否为我们想处理的“modelscope”
        if provider == "modelscope":
            print("正在使用自定义的ModelScope Provider")
            self.provider = "modelscope"

        # 解析凭证
            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY")
            self.base_url = base_url or "https://api.modelscope.cn/api/v1"

        # 验证凭证是否存在
            if not self.api_key:
                raise ValueError("ModelScope API Key is not find,please set ModelScope API Key in enviroment variables")
            
        # 设置其他参数
            self.model = model or os.getenv("LLM_MODEL") or "qwen2.5-coder:1.5b"
            self.temperature = kwargs.get("temperature",0.7)
            self.max_tokens = kwargs.get("max_tokens")
            self.timeout = kwargs.get("timeout",60)

        # 使用获取的参数创建OpenAI客户端实例
            self._client = OpenAI(api_key=self.api_key,base_url=self.base_url,timeout=self.timeout)

        else:
            # 如果不是modelscope，则完全使用父类的原始逻辑来处理
            super().__init__(model=model,api_key=api_key,base_url=base_url,provider=provider,**kwargs)