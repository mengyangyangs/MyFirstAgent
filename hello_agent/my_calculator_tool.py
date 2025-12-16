import ast
import operator
import math
from hello_agents import ToolRegistry

def my_calculator(expression:str) -> str:
    """ 
    主要面向用户的计算器函数。
    它接收一个字符串形式的数学表达式，使用 ast (Abstract Syntax Trees) 模块来安全地解析和执行，
    避免了直接使用 eval() 可能带来的安全风险。
    最后，它将计算结果作为字符串返回。
    """
    # 检查输入表达式去除首尾空格后是否为空，确保有内容需要计算。
    if not expression.strip():
        return "计算表达式不能为空"
    
    # 定义一个字典，将 ast 中的操作符类型映射到 Python 的 operator 模块中的具体函数。
    # 这样做可以让我们根据 AST 节点的类型动态地选择相应的计算函数。
    # 支持的基本运算：加、减、乘、除。
    operators = {
        ast.Add:operator.add, # 加法
        ast.Sub:operator.sub, # 减法
        ast.Mult:operator.mul, # 乘法
        ast.Div:operator.truediv, # 真除法 (结果为浮点数)
    }

    # 定义支持的数学函数和常量。
    # 键是函数/常量的字符串名称，值是 math 模块中对应的函数或常量。
    functions = {
        "sqrt":math.sqrt, # 平方根函数
        "pi":math.pi,     # 圆周率常量
    }

    # 使用 try-except 块来捕获解析和计算过程中可能出现的任何错误，
    # 例如语法错误、不支持的操作等，从而增强程序的健壮性。
    try:
        # 使用 ast.parse 将输入的字符串表达式解析成一个抽象语法树（AST）。
        # mode='eval' 表示我们将表达式作为单个表达式来解析，而不是一个完整的代码块。
        node = ast.parse(expression,mode='eval')
        # 调用辅助函数 _eval_node 来递归地计算 AST 的值。
        result = _eval_node(node.body,operators,functions)
        # 将计算结果转换为字符串并返回。
        return str(result)
    except:
        # 如果在解析或计算过程中发生任何异常，则返回一个通用的错误消息。
        return "计算失败，请检查表达式格式"

def _eval_node(node,operators,functions):
    """
    一个递归的辅助函数，用于遍历和计算抽象语法树（AST）中的每个节点。
    它是整个安全计算过程的核心，通过模式匹配节点的类型（如常数、二元运算、函数调用等）
    来决定如何进行计算。
    """
    # 递归的基准情况：如果节点是一个常量（例如数字 5 或字符串 "hello"），直接返回它的值。
    if isinstance(node,ast.Constant):
        return node.value
    # 如果节点是一个二元操作（如 a + b），则递归地计算左右两边的子节点，
    # 然后根据操作符类型（node.op）从 operators 字典中查找对应的函数并执行计算。
    elif isinstance(node,ast.BinOp):
        left = _eval_node(node.left,operators,functions)
        right = _eval_node(node.right,operators,functions)
        op = operators.get(type(node.op))
        return op(left,right)
    # 如果节点是一个函数调用（如 sqrt(4)），
    # 首先获取函数名称（node.func.id），然后递归地计算所有参数（node.args）的值，
    # 最后从 functions 字典中找到对应的函数并传入参数列表进行调用。
    elif isinstance(node,ast.Call):
        func_name = node.func.id
        if func_name in functions:
            args = [_eval_node(arg,operators,functions) for arg in node.args]
            return functions[func_name](*args)
    # 如果节点是一个名称（例如变量名 'pi'），
    # 从 functions 字典中查找并返回对应的常量值。
    elif isinstance(node,ast.Name):
        if node.id in functions:
            return functions[node.id]
    
def create_calculator_registry():
    """
    这是一个工厂函数，用于创建一个工具注册表（ToolRegistry）实例，
    并将我们定义的计算器函数注册进去。
    这在 Agent 或工具调用框架中很常见，可以将一个普通函数封装成一个可被外部系统（如 AI Agent）调用的“工具”。
    """
    # 创建一个 ToolRegistry 类的实例。
    registry = ToolRegistry()
    
    # 调用注册表实例的 register_function 方法。
    # 这会将 my_calculator 函数注册为一个名为 "my_calculator" 的工具，
    # 并提供一段描述信息，以便 AI 或其他系统了解这个工具的功能和用法。
    registry.register_function(
        name = "my_calculator",
        description = "简单的数学计算工具，支持基本计算(+,-,*,/)和sqrt函数",
        func = my_calculator
    )
    # 返回配置好并包含计算器工具的注册表实例。
    return registry
