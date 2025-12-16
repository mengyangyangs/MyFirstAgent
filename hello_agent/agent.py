""" Agent基类 """
# 导入ABC (Abstract Base Class) 和 abstractmethod, 用于创建抽象基类和抽象方法。
from abc import ABC,abstractmethod
# 导入类型提示相关的模块，增强代码可读性和健壮性。
from typing import Optional,Any
# 从 messages 模块导入 Message 类，用于表示对话消息。
from messages import Message
# 从 hello_agents.core.llm 模块导入 HelloAgentsLLM 类，这是对大型语言模型的封装。
from hello_agents.core.llm import HelloAgentsLLM
# 从 config 模块导入 Config 类，用于配置 Agent。
from config import Config

# 定义一个名为 Agent 的抽象基类，所有具体的 Agent 类都应继承自该类。
# ABC 意味着这个类不能被直接实例化。
class Agent(ABC):
    """
    Agent基类 (Abstract Base Class for all Agents)。
    
    这个类为所有特定类型的 Agent（如 ReActAgent, ChatAgent 等）提供了一个通用的接口和基础功能。
    它定义了 Agent 的核心属性（如名称、LLM实例、系统提示等）和必须实现的方法（如 run）。
    """
    def __init__(
        self,
        name:str, # Agent 的名称，用于识别不同的 Agent。
        llm:HelloAgentsLLM, # Agent 使用的大型语言模型（LLM）实例。
        system_prompt:Optional[str] = None, # 可选的系统提示，用于指导 LLM 的行为。
        config:Optional[Config] = None # 可选的配置对象。
    ):
        """
        Agent 类的构造函数。
        
        Args:
            name (str): Agent 的名称。
            llm (HelloAgentsLLM): 用于驱动 Agent 的大型语言模型实例。
            system_prompt (Optional[str], optional): 初始化时设置的系统级提示。默认为 None。
            config (Optional[Config], optional): Agent 的配置对象。默认为 None。
        """
        self.name = name # 初始化 Agent 名称。
        self.llm = llm # 初始化 LLM 实例。
        self.system_prompt = system_prompt # 初始化系统提示。
        # 如果提供了 config，则使用它；否则创建一个新的 Config 实例。
        # 注意：这里的 `Config or Config()` 应该是 `config or Config()`，以使用传入的参数。
        self.config = Config or Config()
        # 初始化一个私有列表 `_history`，用于存储对话历史记录。每个元素都是一个 Message 对象。
        self._history:list[Message] = []

    # @abstractmethod 装饰器表明这个方法是一个抽象方法。
    # 任何继承自 Agent 的子类都必须实现自己的 run 方法。
    @abstractmethod
    def run(self,input_text:str,**kwargs) -> str:
        """ 
        运行 Agent 的核心逻辑。
        
        这是一个抽象方法，子类必须重写此方法以定义其具体的行为。
        
        Args:
            input_text (str): 用户输入或任务描述。
            **kwargs: 其他可选的关键字参数。
            
        Returns:
            str: Agent 生成的最终响应。
        """
        # pass 关键字表示这里没有实现，具体实现留给子类。
        pass

    def add_message(self,message:Message):
        """ 
        将一条消息添加到 Agent 的对话历史记录中。
        
        Args:
            message (Message): 要添加的 Message 对象。
        """
        # 使用 append 方法将消息对象添加到 _history 列表的末尾。
        return self._history.append(message)

    def clear_history(self):
        """ 清空 Agent 的对话历史记录。 """
        # 调用列表的 clear 方法，移除所有历史记录。
        return self._history.clear()

    def get_history(self) -> list[Message]:
        """ 
        获取 Agent 的对话历史记录。
        
        Returns:
            list[Message]: 包含所有历史消息的列表的副本。
                           返回副本是为了防止外部代码意外修改内部历史记录。
        """
        # 返回 _history 列表的一个浅拷贝。
        return self._history.copy()

    def __str__(self) -> str:
        """
        返回 Agent 对象的字符串表示形式，方便调试和打印。
        
        Returns:
            str: 描述 Agent 名称和其使用的 LLM 提供商的字符串。
        """
        return f"Agent(name={self.name},provider={self.llm.provider})"

    
