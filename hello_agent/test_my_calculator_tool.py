from dotenv import load_dotenv
from my_calculator_tool import create_calculator_registry

# 从 .env 文件中加载环境变量。这是一种常见的实践，用于管理 API 密钥等敏感信息，而无需将其硬编码到代码中。
load_dotenv()

def test_calculator_tool():
    """
    测试自定义计算器工具。
    
    这个函数旨在独立地验证计算器工具的基本功能是否正常工作。
    它通过一系列预定义的简单数学表达式来测试工具的解析和计算能力。
    """
    # 创建一个工具注册表，该注册表包含了我们定义的“my_calculator”工具。
    registry = create_calculator_registry()
    print(" 测试自定义计算器工具\n ")

    # 定义一组简单的数学表达式作为测试用例。
    test_cases = [
        "2+3",      # 加法
        "10-4",     # 减法
        "5*6",      # 乘法
        "15/3",     # 除法
        "sqrt(16)", # 平方根函数
    ]
    # 遍历所有测试用例，并执行计算。
    for i,expression in enumerate(test_cases,1):
        print(f"测试{i}:{expression}")
        # 通过注册表调用名为 "my_calculator" 的工具，并将表达式字符串作为参数传入。
        result = registry.execute_tool("my_calculator",expression)
        print(f"结果:{result}\n")

def test_with_simple_agent():
    """
    测试计算器工具与一个简单的代理（Agent）的集成。
    
    此函数模拟了一个更完整的智能代理工作流程：
    1. 接收一个包含计算任务的自然语言问题。
    2. 调用计算器工具来解决问题中的数学部分。
    3. 将计算结果与原始问题结合，交给大语言模型（LLM）生成最终的、符合自然语言习惯的回答。
    """
    # 导入我们自定义的大语言模型（LLM）封装类。
    from hello_agents import HelloAgentsLLM

    # 初始化大语言模型。
    llm = HelloAgentsLLM()

    # 创建工具注册表，以便代理可以访问计算器工具。
    registry = create_calculator_registry()
    print("🤖 与 SimpleAgent集成测试:")

    # 定义一个用户的自然语言问题，其中包含一个需要计算的复杂表达式。
    user_question = "请帮我计算sqrt(16) + 2 * 3"
    print(f"用户问题:{user_question}")

    # 使用工具注册表执行计算器工具，工具能够从完整的问句中提取并计算数学表达式。
    calc_result = registry.execute_tool("my_calculator",user_question)
    print(f"计算结果:{calc_result}")

    # 构建一个消息列表，作为提供给大语言模型的最终提示（prompt）。
    # 这种结构通常用于与基于对话的 LLM API 进行交互。
    final_messages = [
        {"role":"user",
            # content 字段是关键：它将工具的计算结果和用户的原始问题结合起来，
            # 指示模型基于这个计算结果来回答最初的问题。
        "content":f"计算结果是:{calc_result},请用自然语言回答用户问题:{user_question}"}
    ]
    print("\nSimpleAgent的回答:")
    # 调用大语言模型的 `invoke` 方法，发送构造好的提示并获取响应。
    response = llm.invoke(final_messages)
    # 以流式（streaming）的方式处理和打印模型的响应。
    # 这意味着我们会逐块接收和显示文本，而不是等待整个回答生成完毕。
    for chunk in response:
        # 打印每个文本块，end="" 防止自动换行，flush=True 确保立即输出到控制台。
        print(chunk,end="",flush=True)
    print("\n")

# 这是一个标准的 Python 入口点。
# 当这个脚本作为主程序直接运行时，下面的代码块才会被执行。
if __name__ =="__main__":
    # 首先，运行独立的计算器工具测试。
    test_calculator_tool()
    # 然后，运行计算器工具与 Agent 的集成测试。
    test_with_simple_agent()
