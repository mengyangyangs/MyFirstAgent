from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM,ToolRegistry
from hello_agents.tools import CalculatorTool
from my_simple_agent import MySimpleAgent
from my_react_agent import MyReActAgent
from my_reflection_agent import MyReflectionAgent
from my_PlanAndSolve_agent import PlanAndSolveAgent
from hello_agents.core.llm import HelloAgentsLLM

load_dotenv()

llm = HelloAgentsLLM()

# Plan And Solve Agent 测试
agent = PlanAndSolveAgent(
    name = "我的规划与执行助手",
    llm_client = llm
)

# 测试复杂问题
question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
result = agent.run(question)
print(f"最终结果:{result}")

# # Reflection Agent 测试：使用默认通用提示词
# general_agent = MyReflectionAgent(
#     name = "我的反思助手",
#     llm = llm
# )
# # 使用自定义代码生成提示词
# code_prompts = {
#     "initial":"你是python专家，请编写函数:{task}",
#     "reflect":"请审查代码的算法效率:\n任务:{task}\n代码:{code}",
#     "refine":"请根据反馈优化代码:\n任务:{task}\n反馈:{feedback}"
# }
# code_agent = MyReflectionAgent(
#     name = "我的代码优化助手",
#     llm = llm,
#     custom_prompts = code_prompts
# )

# result = code_agent.run("请帮我写一个计算斐波那契数列的函数")
# print(f"最终结果:{result}")

# 测试使用
# result = general_agent.run("写一篇关于人工智能发展历程的简短文章")
# print(f"最终结果:{result}")

# # ReAct Agent 测试1:基础对话测试(无工具)
# print("====基础对话测试====")
# basic_agent = MySimpleAgent(
#     name = "基础智能体",
#     llm = llm,
#     system_prompt = "你是一个友好的AI助手，请用简介明了的方式回答问题"

# )

# response = basic_agent.run("你好，请介绍一下自己")
# print(f"基础对话响应:{response}")

# 测试2:带工具的Agent
# print("====带工具的Agent对话====")
# tool_registry = ToolRegistry()
# calculator = CalculatorTool()
# tool_registry.register_tool(calculator)

# enhanced_agent = MySimpleAgent(
#     name = "增强智能体",
#     llm = llm,
#     system_prompt = "你是一个非常智能的AI助手，可以使用工具来帮助用户",
#     enable_tool_calling = True,
#     tool_registry = tool_registry
# )

# response = enhanced_agent.run("请帮我计算15*8+22")
# print(f"增强对话响应:{response}")

# 测试2:带工具的Agent
# print("====带工具的Agent对话====")
# tool_registry = ToolRegistry()
# calculator = CalculatorTool()
# tool_registry.register_tool(calculator)

# enhanced_agent = MyReActAgent(
#     name = "增强智能体",
#     llm = llm,
#     system_prompt = "你是一个超级无敌的AI助手，我询问你什么问题你都答得非常详细，深入且完整。",
#     # enable_tool_calling = True,
#     tool_registry = tool_registry
# )

# response = enhanced_agent.run("如何把大象放进冰箱，请你分三步走。放进去之后，我又该如何取出大象")
# print(f"增强对话响应:{response}")

# # 测试3:流式响应
# print("====流式响应====")
# print("流式响应",end='')
# for chunk in basic_agent.stream_run("请解释什么是人工智能"):
#     pass
    
# # 测试4:动态添加工具
# print("\n====动态添加工具====")
# print(f"添加工具前:{basic_agent.has_tools()}")
# basic_agent.add_tool(calculator)
# print(f"添加工具后:{basic_agent.has_tools()}")
# print(f"可用工具:{basic_agent.list_tools()}")

# print(f"\n对话历史:{len(basic_agent.get_history())}条消息")