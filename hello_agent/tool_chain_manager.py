# 工具链式调用机制
from typing import Optional,List,Dict,Any
from hello_agents import ToolRegistry

class ToolChain:
    """ 
    工具链 - 支持多个工具的顺序执行。
    这个类允许将一系列工具调用串联起来，前一个工具的输出可以作为后一个工具的输入，
    形成一个处理流程。
    """
    def __init__(self,name:str,description:str):
        # 工具链的名称，用于唯一标识
        self.name = name
        # 工具链的功能描述
        self.description = description
        # 存储工具链中所有步骤的列表
        self.steps:List[Dict[str,Any]] = []

    def add_step(self,tool_name:str,input_template:str,output_key:str = None):
        """ 
        向工具链中添加一个执行步骤。

        Args:
            tool_name (str): 要调用的工具的名称。
            input_template (str): 工具的输入模板。支持使用花括号 `{}` 进行变量替换，
                                  变量来自于执行上下文（context）。
            output_key (str, optional): 当前步骤执行结果在上下文（context）中存储的键名。
                                        如果未提供，会自动生成一个默认的键名。
                                        这个键名可用于后续步骤引用本次执行的结果。
        """
        # 将一个步骤定义（一个字典）追加到步骤列表中
        self.steps.append({
            "tool_name":tool_name, # 工具名
            "input_template":input_template, # 输入模板
            "output_key":output_key or f"step_{len(self.steps)}_result" # 输出结果的键名，如果未指定则自动生成
        })

    def execute(self,registry:ToolRegistry,initial_input:str,context:Dict[str,Any] = None) -> str:
        """ 
        按顺序执行工具链中的所有步骤。

        Args:
            registry (ToolRegistry): 一个包含所有可用工具的工具注册表。
            initial_input (str): 工具链的初始输入数据。
            context (Dict[str,Any], optional): 初始的执行上下文，可以预设一些变量。

        Returns:
            str: 工具链最后一个步骤的执行结果。
        """
        # 如果没有提供初始上下文，则创建一个空字典
        context = context or {}
        # 将初始输入存入上下文中，默认键名为 "input"
        context["input"] = initial_input

        print(f"开始执行工具链:{self.name}")

        # 遍历工具链中的每一个步骤并执行
        for i,step in enumerate(self.steps,1):
            # 获取当前步骤的工具名称、输入模板和输出键名
            tool_name = step["tool_name"]
            input_template = step["input_template"]
            output_key = step["output_key"]

            try:
                # 使用上下文中的变量来格式化（渲染）输入模板，生成最终的工具输入
                tool_input = input_template.format(**context)
            except KeyError as e:
                # 如果模板中的某个变量在上下文中找不到，则执行失败并返回错误信息
                return f"工具链执行失败：模版变量{e}未找到"

            print(f"步骤{i}:使用{tool_name}处理'{tool_input[:50]}...'")

            # 通过工具注册表实际执行工具调用
            result = registry.execute_tool(tool_name,tool_input)
            # 将当前步骤的执行结果以指定的 output_key 存入上下文，供后续步骤使用
            context[output_key] = result

            print(f"  ✅ 步骤 {i} 完成，结果长度: {len(result)} 字符")
        
        # 获取最后一步的输出键名
        last_step_output_key = self.steps[-1]["output_key"]
        # 从上下文中获取并返回最后一步的执行结果
        final_result = context[last_step_output_key]
        print(f"工具链'{self.name}'执行完成")
        return final_result

class ToolChainManager:
    """ 
    工具链管理器。
    负责注册、管理和执行多个工具链。
    """
    def __init__(self,registry:ToolRegistry):
        # 持有一个工具注册表的引用，用于执行工具
        self.registry = registry
        # 使用字典来存储所有已注册的工具链，键为工具链名称，值为ToolChain对象
        self.chains:Dict[str,ToolChain] = {}

    def register_chain(self,chain:ToolChain):
        """ 注册一个新的工具链到管理器中。"""
        # 将工具链实例添加到 chains 字典中
        self.chains[chain.name] = chain
        print(f"工具链{chain.name}注册成功")

    def execute_chain(self,chain_name:str,input_data:str,context:Dict[str,Any] = None) -> str:
        """ 根据名称执行一个已注册的工具链。"""
        # 检查要执行的工具链是否存在
        if chain_name not in self.chains:
            return f"工具链{chain_name}不存在"

        # 从字典中获取工具链实例
        chain = self.chains[chain_name]
        # 调用该工具链实例的 execute 方法来执行它
        return chain.execute(self.registry,input_data,context)

    def list_chains(self) -> List[str]:
        """ 列出所有已注册的工具链的名称。"""
        # 返回 chains 字典中所有键的列表
        return list(self.chains.keys())

# --- 使用示例 ---
def create_research_chain() -> ToolChain:
    """ 
    创建一个示例研究工具链。
    该工具链模拟一个“研究并计算”的流程：先搜索信息，然后基于搜索结果进行计算。
    """
    # 实例化一个 ToolChain 对象
    chain = ToolChain(
        name = "research_and_calculate",
        description = "搜索信息并进行相关计算"
    )

    # 步骤1: 使用 "search" 工具进行信息搜索
    chain.add_step(
        tool_name = "search",
        # 输入模板为 "{input}"，表示直接使用工具链的初始输入作为搜索工具的输入
        input_template = "{input}",
        # 将搜索结果存储在上下文的 "search_result" 键中
        output_key = "search_result"
    )

    # 步骤2: 使用 "my_calculator" 工具进行计算
    chain.add_step(
        tool_name = "my_calculator",
        # 输入模板引用了上一步的结果 "{search_result}"
        input_template = "根据以下信息计算相关数据:{search_result}",
        # 将计算结果存储在上下文的 "calculation_result" 键中
        output_key = "calculation_result"
    )

    # 返回创建好的工具链实例
    return chain
