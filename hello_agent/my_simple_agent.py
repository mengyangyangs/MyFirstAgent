from typing import Optional,Iterator
from hello_agents import HelloAgentsLLM,SimpleAgent,Config,Message
import re

class MySimpleAgent(SimpleAgent):
    """
    重写的简单对话Agent
    这个类是一个自定义Agent的示例，它继承自框架提供的`SimpleAgent`基类。
    主要功能是实现一个可以与大语言模型（LLM）进行对话的代理，并增加了调用外部“工具”的能力，
    从而扩展了其功能范围（例如，进行网络搜索、计算等）。
    """

    def __init__(
        self,
        name:str,
        llm:HelloAgentsLLM,
        system_prompt:Optional[str] = None,
        config:Optional[Config] = None,
        tool_registry:Optional["ToolRegistry"] = None,
        enable_tool_calling:bool = True
    ):
        """
        Agent的初始化方法。
        
        参数:
        - name: Agent的名称。
        - llm: 用于生成回复的大语言模型实例。
        - system_prompt: 系统提示词，用于指导LLM的行为。
        - config: Agent的配置选项。
        - tool_registry: 工具注册表，管理所有可用的工具。
        - enable_tool_calling: 是否启用工具调用功能的开关。
        """
        # 调用父类的初始化方法，完成基本设置
        super().__init__(name,llm,system_prompt,config)
        # 保存工具注册表实例
        self.tool_registry = tool_registry
        # 确定是否启用工具调用：必须全局启用并且传入了工具注册表
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        # 打印初始化状态信息，方便调试
        print(f"{self.name}:初始化完成，工具调用：{'start' if self.enable_tool_calling else 'disabled'}")

    def run(self,input_text:str,max_tool_iterations:int = 3,**kwargs) -> str:
        """
        Agent的核心运行方法。
        它接收用户输入，处理对话历史，并与LLM交互以生成回复。
        如果启用了工具调用，它将进入一个循环，允许LLM多次调用工具来解决复杂问题。

        参数:
        - input_text: 用户的当前输入文本。
        - max_tool_iterations: 在一次`run`调用中，允许LLM调用工具的最大循环次数，防止无限循环。
        - **kwargs: 传递给LLM调用的额外参数。

        返回:
        - LLM生成的最终回复字符串。
        """
        print(f"{self.name}:正在处理{input_text}")

        # 初始化本次对话的消息列表
        messages = []

        # 获取增强后的系统提示词（可能包含工具信息）
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        # 将系统提示词作为第一条消息添加到列表中
        messages.append({'role':"system",'content':enhanced_system_prompt})

        # 将历史对话记录添加到消息列表中
        for msg in self._history:
            messages.append({'role':msg.role,'content':msg.content})
        
        # 将用户的当前输入作为最后一条消息添加到列表中
        messages.append({'role':"user",'content':input_text})

        # 如果未启用工具调用，则执行简单的问答流程
        if not self.enable_tool_calling:
            # 直接调用LLM获取回复
            response = self.llm.invoke(messages,**kwargs)
            # 将用户的输入和LLM的回复添加到历史记录中
            self.add_message(Message(input_text,"user"))
            self.add_message(Message(response,"assistant"))
            print(f"{self.name}响应完成")
            # 返回最终回复
            return response

        # 如果启用了工具调用，则调用专门处理工具逻辑的方法
        return self._run_with_tools(messages,input_text,max_tool_iterations,**kwargs)

    
    def _get_enhanced_system_prompt(self) -> str:
        """ 
        构建一个增强的系统提示词。
        如果启用了工具调用，此方法会在原始系统提示词的基础上，
        追加关于可用工具的描述以及如何调用这些工具的格式说明。
        这能引导LLM在需要时正确地生成工具调用指令。

        返回:
        - 包含或不包含工具信息的完整系统提示词字符串。
        """
        # 使用用户提供的system_prompt，如果没有则使用一个默认值
        base_prompt = self.system_prompt or "你是一个有用的AI助手,你的回答必须总是详细，深入且完整。"

        # 如果工具调用未启用，直接返回基础提示词
        if not self.enable_tool_calling:
            return base_prompt

        # 从工具注册表获取所有工具的描述
        tools_description = self.tool_registry.get_tools_description()
        # 如果没有工具或描述为空，也只返回基础提示词
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt

        # 构建工具描述部分
        tools_section = "\n\n## 可用工具\n"
        tools_section += "你可以使用以下工具来帮助回答问题:\n"
        tools_section += tools_description + "\n"

        # 构建工具调用格式说明部分
        tools_section += "\n## 工具调用格式\n"
        tools_section += "当需要使用工具时，请使用以下格式:\n"
        tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n"
        tools_section += "例如:`[TOOL_CALL:search:Python编程]` 或 `[TOOL_CALL:memory:recall=用户信息]`\n\n"
        tools_section += "工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。\n"

        # 将基础提示词和工具部分拼接后返回
        return base_prompt + tools_section

    def _run_with_tools(self,messages:list,input_text:str,max_tool_iterations:int,**kwargs) -> str:
        """
        实现支持工具调用的核心逻辑（类似于ReAct模式）。
        在一个循环中，Agent会：
        1. 调用LLM获取回复。
        2. 解析回复中是否包含工具调用指令。
        3. 如果有，则执行工具，并将工具结果反馈给LLM，进入下一次循环。
        4. 如果没有，则认为这是最终答案并退出循环。
        
        参数:
        - messages: 当前的完整对话消息列表。
        - input_text: 用户的原始输入，用于保存历史记录。
        - max_tool_iterations: 最大工具调用循环次数。
        - **kwargs: 传递给LLM调用的额外参数。

        返回:
        - LLM生成的最终回复字符串。
        """
        current_iteration = 0  # 初始化循环计数器
        final_response = ""    # 初始化最终回复

        # 循环直到达到最大迭代次数
        while current_iteration < max_tool_iterations:
            # 第一步：调用LLM获取回复（或下一步行动）
            response = self.llm.invoke(messages,**kwargs)
            # 第二步：解析回复，查找工具调用指令
            tool_calls = self._parse_tool_calls(response)

            # 如果检测到工具调用
            if tool_calls:
                print(f"检测到{len(tool_calls)}个工具调用")
                # 执行所有工具调用并收集结果
                tool_results = []
                clean_response = response  # 用于存放清除了工具调用语法后的回复

                for call in tool_calls:
                    # 执行单个工具调用
                    result = self._execute_tool_call(call["tool_name"],call["parameters"])
                    tool_results.append(result)
                    # 从LLM的原始回复中移除工具调用指令文本
                    clean_response = clean_response.replace(call["original"],"")

                # 将LLM的思考过程（清除工具调用语法后）作为助手的回复存入消息列表
                messages.append({"role": "assistant", "content": clean_response})

                # 将所有工具的执行结果合并，并作为一条新的用户消息添加到对话中
                # 这会让LLM在下一步知道工具执行的结果
                tool_results_text = "\n\n".join(tool_results)
                messages.append({"role": "user", "content": f"工具执行结果:\n{tool_results_text}\n\n请基于这些结果给出完整的回答。"})

                # 增加迭代计数器并继续下一次循环
                current_iteration += 1
                continue

            # 如果没有检测到工具调用，说明LLM认为已经可以给出最终答案
            final_response = response
            break # 退出循环
        
        # 如果循环因为达到最大次数而终止，但还没有最终回复，则再调用一次LLM生成最终回复
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages,**kwargs)

        # 将用户的原始输入和Agent的最终回复保存到历史记录
        self.add_message(Message(input_text,"user"))
        self.add_message(Message(final_response,"assistant"))
        print(f"{self.name}响应完成")
        return final_response


    def _parse_tool_calls(self,text:str) -> list:
        """
        使用正则表达式解析文本中的工具调用指令。
        指令格式为 `[TOOL_CALL:tool_name:parameters]`。

        参数:
        - text: LLM生成的文本。

        返回:
        - 一个列表，包含所有解析出的工具调用信息字典。每个字典包含'tool_name', 'parameters', 'original'。
        """
        # 定义匹配工具调用格式的正则表达式
        # r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        # \[TOOL_CALL:  - 匹配字面量 "[TOOL_CALL:"
        # ([^:]+)       - 捕获组1: 匹配一个或多个非冒号字符（即工具名）
        # :             - 匹配字面量 ":"
        # ([^\]]+)      - 捕获组2: 匹配一个或多个非右方括号字符（即参数）
        # \]            - 匹配字面量 "]"
        pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        matches = re.findall(pattern,text)

        tool_calls = []
        # 遍历所有匹配项
        for tool_name,parameters in matches:
            # 将解析出的信息构造成一个字典并添加到列表中
            tool_calls.append({
                "tool_name":tool_name,
                "parameters":parameters.strip(), # 去除参数字符串两端的空白
                "original":f'[TOOL_CALL:{tool_name}:{parameters}]' # 保存原始匹配字符串，方便后续替换
            })
        return tool_calls

    def _execute_tool_call(self,tool_name:str,parameters:str) -> str:
        """
        执行一个具体的工具调用。

        参数:
        - tool_name: 要调用的工具名称。
        - parameters: 传递给工具的参数字符串。

        返回:
        - 工具执行结果的格式化字符串。如果出错则返回错误信息。
        """
        # 检查工具注册表是否存在
        if not self.tool_registry:
            return f"错误：未配置工具注册表"

        try:
            # 对calculator工具进行特殊处理（假设它接收一个直接的表达式字符串）
            if tool_name == "calculator":
                result = self.tool_registry.get_tool(tool_name,parameters)
            else:
                # 对其他工具，先解析参数字符串为字典
                param_dict = self._parse_tool_parameters(tool_name,parameters)
                # 从注册表中获取工具实例
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    return f"错误：未找到工具{tool_name}"
                # 运行工具，并传入解析后的参数字典
                result = tool.run(param_dict)
            # 返回格式化的成功结果
            return f"工具{tool_name} 执行结果:\n{result}"

        except Exception as e:
            # 捕获并返回执行过程中的任何异常
            return f"工具调用失败{e}"

    def _parse_tool_parameters(self,tool_name:str,parameters:str) -> dict:
        """
        智能地将参数字符串解析为字典。
        支持多种格式，如 "key=value", "key1=value1,key2=value2" 或直接的参数值。

        参数:
        - tool_name: 工具名称，用于在无法解析时进行智能猜测。
        - parameters: 原始参数字符串。

        返回:
        - 一个包含参数键值的字典。
        """
        param_dict = {}

        # 检查是否为 key=value 格式
        if '=' in parameters:
            # 格式：key=value 或者 action=search,query=Python
            # 注意：代码中的 `if '.' in parameters:` 可能是个笔误，通常参数分隔符是逗号`,`
            if ',' in parameters: # 假设分隔符是逗号
                # 多个参数的情况：action=search,query=Python,limit=3
                pairs = parameters.split(',')
                for pair in pairs:
                    if '=' in pair:
                        key,value = pair.split("=",1)
                        param_dict[key.strip()] = value.strip()
            else:
                # 单个参数的情况：key=value
                key,value = parameters.split("=",1)
                param_dict[key.strip()] = value.strip()
        
        else:
            # 如果没有'='，则认为是直接传入参数值，根据工具名智能判断参数键
            if tool_name == "search":
                param_dict = {"query":parameters} # 搜索工具的默认参数是 'query'
            elif tool_name == "memory":
                param_dict = {"action":"search","query":parameters} # 内存工具的默认动作是搜索
            else:
                # 其他工具的通用默认参数是 'input'
                param_dict = {"input":parameters}

        return param_dict

    def stream_run(self,input_text:str,**kwargs) -> Iterator[str]:
        """
        自定义的流式运行方法。
        此方法会以流的形式逐步返回LLM的响应，而不是等待完整响应生成后再返回。
        注意：当前实现不支持工具调用。

        参数:
        - input_text: 用户的输入。
        - **kwargs: 传递给LLM流式调用的额外参数。

        返回:
        - 一个迭代器，每次迭代产生一小块响应文本。
        """
        print(f"{self.name}:开始流式处理:{input_text}")

        # 准备发送给LLM的消息列表
        messages = []

        if self.system_prompt:
            messages.append({"role":"system","content":self.system_prompt})
        
        # 添加历史消息
        for msg in self._history:
            messages.append({"role":msg.role,"content":msg.content})
        
        # 添加当前用户输入
        messages.append({"role":"user","content":input_text})

        # 调用LLM的流式接口
        full_response = ""
        print("实时响应",end="")
        for chunk in self.llm.stream_invoke(messages,**kwargs):
            full_response += chunk  # 累积完整的回复内容
            print(chunk,end="",flush=True) # 实时打印到控制台
            yield chunk # 将文本块返回给调用者
        
        print() # 换行

        # 流式响应结束后，将完整的对话保存到历史记录
        self.add_message(Message(input_text,"user"))
        self.add_message(Message(full_response,"assistant"))
        print(f"{self.name}:流式响应完毕")

    def add_tool(self,tool) -> None:
        """
        向Agent动态添加一个工具。

        参数:
        - tool: 要添加的工具对象。
        """
        # 如果当前没有工具注册表，则创建一个新的
        if not self.tool_registry:
            from hello_agents import ToolRegistry
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True # 同时启用工具调用功能

        # 将工具添加到注册表
        self.tool_registry.register_tool(tool)
        print(f"工具{tool.name}:添加成功")

    def has_tools(self) -> bool:
        """检查Agent是否有可用的工具。"""
        return self.enable_tool_calling and self.tool_registry is not None

    def remove_tool(self,tool_name:str) -> bool:
        """
        从Agent中移除一个工具。

        参数:
        - tool_name: 要移除的工具的名称。

        返回:
        - 如果成功移除返回True，否则返回False。
        """
        if self.tool_registry:
            # 调用工具注册表的注销方法
            self.tool_registry.unregister(tool_name)
            return True
        return False

    def list_tools(self) -> list:
        """
        列出Agent当前所有可用的工具。

        返回:
        - 一个包含工具名称的列表。
        """
        if self.tool_registry:
            return self.tool_registry.list_tools()
        return []
