# 默认规划词提示词模版
MY_DEFAULT_PROMPT = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的，可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的自然串。

问题:
{question}

请严格按照以下格式输出你的计划：
''' python
["步骤1","步骤2","步骤3",...]
'''
"""

# 默认执行器提示词模版
DEFAULT_EXECUTOR_PROMPT = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将接收到原始问题，完整的计划，以及到目前为止已经完成的步骤和结果。
请你专注于解决“当前步骤“，并输出该步骤的最终答案，不要输出任何额外的解释或对话

# 原始问题：
{question}

# 完整计划：
{plan}

# 历史步骤与结果：
{history}

# 当前步骤：
{current_step}

请仅输出针对“当前步骤“的回答：
"""

# 导入必要的库
import ast  # 用于安全地评估字符串形式的Python字面量（如列表）
from typing import Optional, List, Dict, Any  # 用于类型注解，增强代码可读性和健壮性
from hello_agents import HelloAgentsLLM  # 导入自定义的大语言模型客户端
from agent import Agent  # 导入基础Agent类
from messages import Message  # 导入消息类，用于记录对话历史
from config import Config  # 导入配置类

class Planner:
    """
    规划器 (Planner) - 负责将用户的复杂问题分解为一系列更简单、可执行的步骤。
    这是实现“规划与解决”模式的第一步。
    """
    def __init__(self, llm_client: HelloAgentsLLM, prompt_template: Optional[str] = None):
        """
        初始化规划器。

        Args:
            llm_client (HelloAgentsLLM): 用于与大语言模型交互的客户端实例。
            prompt_template (Optional[str]): 可选的自定义提示词模板。如果未提供，则使用默认模板 MY_DEFAULT_PROMPT。
        """
        self.llm_client = llm_client  # 保存LLM客户端实例
        # 如果用户没有提供自定义模板，则使用默认的规划提示词模板
        self.prompt_template = prompt_template if prompt_template else MY_DEFAULT_PROMPT

    def plan(self, question: str, **kwargs) -> List[str]:
        """
        根据用户的问题生成一个行动计划。

        Args:
            question (str): 用户提出的需要解决的复杂问题。
            **kwargs: 传递给LLM调用的额外参数 (例如 temperature, max_tokens等)。

        Returns:
            List[str]: 一个包含多个步骤描述字符串的列表。如果生成或解析失败，则返回空列表。
        """
        # 将用户问题填充到提示词模板中，生成完整的prompt
        prompt = self.prompt_template.format(question=question)
        # 构造符合LLM API格式的消息列表
        messages = [{"role": "user", "content": prompt}]

        print("--- 正在生成计划 ---")
        # 调用LLM，获取生成的计划文本。如果返回None，则默认为空字符串。
        response_text = self.llm_client.invoke(messages, **kwargs) or ""
        print(f"✅ 计划已生成:\n{response_text}")

        try:
            # 尝试从LLM的响应中提取Python代码块里的内容
            # 假设响应格式为 " ... ```python\n['步骤1', '步骤2']\n``` ... "
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # 使用 ast.literal_eval 安全地将字符串转换为Python列表对象，避免eval()的安全风险
            plan = ast.literal_eval(plan_str)
            # 确保解析结果确实是一个列表，否则返回空列表
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            # 捕获解析过程中可能出现的错误（如格式不正确，找不到代码块等）
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应:{response_text}")
            return []  # 解析失败时返回空列表
        except Exception as e:
            # 捕获其他未知异常
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []

class Executor:
    """
    执行器 (Executor) - 负责按照规划器生成的计划，一步步地执行任务。
    它会在执行每一步时，都考虑原始问题、完整计划以及之前步骤的结果。
    """
    def __init__(self, llm_client: HelloAgentsLLM, prompt_template: Optional[str] = None):
        """
        初始化执行器。

        Args:
            llm_client (HelloAgentsLLM): 用于与大语言模型交互的客户端实例。
            prompt_template (Optional[str]): 可选的自定义执行提示词模板。如果未提供，则使用默认模板 DEFAULT_EXECUTOR_PROMPT。
        """
        self.llm_client = llm_client  # 保存LLM客户端实例
        # 如果用户没有提供自定义模板，则使用默认的执行提示词模板
        self.prompt_template = prompt_template if prompt_template else DEFAULT_EXECUTOR_PROMPT

    def execute(self, question: str, plan: List[str], **kwargs) -> str:
        """
        按顺序执行计划中的每一个步骤，并返回最终结果。

        Args:
            question (str): 用户的原始问题。
            plan (List[str]): 由规划器生成的步骤列表。
            **kwargs: 传递给LLM调用的额外参数。

        Returns:
            str: 执行完所有步骤后得到的最终答案。
        """
        history = ""  # 用于存储已完成步骤及其结果的字符串，作为后续步骤的上下文
        final_answer = ""  # 用于存储最后一个步骤的输出作为最终答案

        print("\n--- 正在执行计划 ---")
        # 遍历计划中的每一个步骤，并带上索引（从1开始）
        for i, step in enumerate(plan, 1):
            print(f"\n -> 正在执行步骤 {i}/{len(plan)}:{step}")
            # 准备当前步骤的提示词，包含所有必要的上下文信息
            prompt = self.prompt_template.format(
                question=question,
                plan=plan,
                history=history if history else "无",  # 如果历史为空，则显示"无"
                current_step=step
            )
            # 构造LLM API的消息
            messages = [{"role": "user", "content": prompt}]

            # 调用LLM执行当前步骤
            response_text = self.llm_client.invoke(messages, **kwargs) or ""
            # 将当前步骤和其结果追加到历史记录中，为下一步提供上下文
            history += f"步骤{i}:{step}\n 结果:{response_text}\n\n"
            # 更新最终答案为当前步骤的结果（循环结束后，这将是最后一个步骤的结果）
            final_answer = response_text
            print(f"✅ 步骤{i}已完成，结果:{final_answer}")

        # 返回最后一个步骤的执行结果作为整个任务的最终答案
        return final_answer

class PlanAndSolveAgent(Agent):
    """
    规划与解决（Plan and Solve）智能体 - 采用两步走的策略来解决复杂问题。

    这个Agent能够：
    1.  将复杂问题分解为多个简单步骤（规划阶段）。
    2.  按照生成的计划逐步执行，每一步都利用之前的上下文信息（解决阶段）。
    3.  维护执行历史和上下文。
    4.  得出最终答案。
    这种模式特别适合需要多步推理、数学计算、复杂分析等任务。
    """
    def __init__(
        self,
        name: str,
        llm_client: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        custom_prompts: Optional[Dict[str, str]] = None
    ):
        """
        初始化 Plan and Solve Agent。

        Args:
            name (str): Agent的名称。
            llm_client (HelloAgentsLLM): LLM客户端实例。
            system_prompt (Optional[str]): 系统的顶级提示词（如果需要）。
            config (Optional[Config]): 配置对象。
            custom_prompts (Optional[Dict[str, str]]): 一个包含自定义提示词模板的字典，键为 "planner" 和 "executor"。
        """
        # 调用父类Agent的构造函数进行基本初始化
        super().__init__(name, llm_client, system_prompt, config)

        # 设置规划器和执行器的提示词模板：优先使用用户自定义的，否则为None（将触发使用默认模板）
        if custom_prompts:
            planner_prompt = custom_prompts.get("planner")
            executor_prompt = custom_prompts.get("executor")
        else:
            planner_prompt = None
            executor_prompt = None

        # 实例化规划器组件
        self.planner = Planner(llm_client, planner_prompt)
        # 实例化执行器组件
        self.executor = Executor(llm_client, executor_prompt)

    def run(self, input_text: str, **kwargs) -> str:
        """
        运行 Plan and Solve Agent 的主流程。

        Args:
            input_text (str): 用户输入的需要解决的问题。
            **kwargs: 传递给LLM调用的额外参数。

        Returns:
            str: 问题的最终答案。
        """
        print(f"\n🤖:{self.name}开始处理问题{input_text}")

        # --- 阶段1: 生成计划 ---
        plan = self.planner.plan(input_text, **kwargs)
        # 检查计划是否成功生成
        if not plan:
            # 如果计划列表为空，说明规划失败，任务无法继续
            final_answer = "无法生成有效的行动计划，任务终止。"
            print(f"\n --- 任务中止 ---\n{final_answer}")

            # 将此次失败的交互记录到历史消息中
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(final_answer, "assistant"))

            return final_answer

        # --- 阶段2: 执行计划 ---
        final_answer = self.executor.execute(input_text, plan, **kwargs)
        print(f"\n --- 任务完成 ---\n最终答案:{final_answer}")

        # 将成功的交互（用户问题和最终答案）记录到历史消息中
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))

        # 返回最终答案
        return final_answer
