# ⭐️ [修复] 修复了拼写: DEFULT_PROMPT -> DEFAULT_PROMPT
DEFAULT_PROMPT = {
    "initial":"""
    请根据以下要求完成任务:
    任务:{task}
    请提供一个完整，准确的回答。
    """,

    "reflect":"""
    请仔细审查以下回答，并找出可能的问题或改进空间
    # 原始任务:{task}
    # 当前回答:{content}

    请分析这个回答的质量，指出不足之处，并提出具体的改进建议。
    如果回答已经很好，请回答“无需改进”
    """,

    "refine":"""
    请根据反馈意见改进你的回答。
    # 原始任务:{task}
    # 上一轮回答:{content}
    # 反馈意见:{feedback}

    请提供一个改进后的回答。
    """
}

from typing import Optional,List,Dict,Any
from hello_agents import HelloAgentsLLM,ReflectionAgent
from messages import Message
from config import Config

class Memory:
    """
    (您的 Memory 类 - 保持不变, 它设计得很好!)
    简单的短期记忆模块，用于存储智能体的行动与反思轨迹。
    """
    def __init__(self):
        self.records:List[Dict[str,Any]] = []

    def add_record(self,record_type:str,content:str):
        """ 向记忆中添加一条消息 """
        self.records.append({"type":record_type,"content":content})
        print(f"📝 记忆已更新，新增一条 '{record_type}' 记录。")
    
    def get_trajectory(self) -> str:
        """ 将所有记忆记录格式化为一个连贯的字符串文本 """
        trajectory = ""
        for record in self.records:
            if record['type'] == 'execution':
                trajectory += f"---上一轮执行结果---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"---评审员反馈---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self) -> str:
        """ 获取最近一次执行结果 """
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return ""

class MyReflectionAgent(ReflectionAgent):
    """
    重写的Reflection Agent - 反思与改进的智能体
    """
    def __init__(
        self,
        name:str,
        llm:HelloAgentsLLM,
        system_prompt:Optional[str] = None,
        config:Optional[Config] = None,
        max_iterations:int = 5,
        custom_prompts:Optional[Dict[str,str]] = None
        
        # ⭐️ [关键修复] ⭐️
        # 我们移除了 tool_registry:ToolRegistry
        # 因为父类 ReflectionAgent 根本不接受它！
        # 这是一个反思 Agent, 不是工具 Agent.
    ):
        
        # ⭐️ [关键修复] ⭐️
        # 调用父类的 super().__init__()
        # 我们只传递父类 *真正* 接受的参数
        super().__init__(
            name=name,
            llm=llm,
            system_prompt=system_prompt,
            config=config,
            max_iterations=max_iterations,
            custom_prompts=custom_prompts
            # 移除了 tool_registry=tool_registry
        )
        
        # (您的 Memory 和 prompts 逻辑保持不变)
        self.memory = Memory()
        self.prompts = custom_prompts if custom_prompts else DEFAULT_PROMPT
        print(f"✅ {name} (反思智能体) 初始化完成。")


    def run(self,input_text:str,**kwargs) -> str:
        """ 重写父类方法，并运行Reflection Agent """
        print(f"🤖{self.name}:开始处理任务:{input_text}")

        # 重置记忆
        self.memory = Memory()
        task = input_text # 为了清晰，我们重命名 input_text

        # 1.初始执行
        print("---\n正在执行初始尝试----")
        
        # ⭐️ [修复] 确保 .format() 使用 'task'
        # (假设 'initial' 模板使用 {task})
        initial_prompt = self.prompts['initial'].format(task=task) 
        initial_result = self._get_llm_response(initial_prompt,**kwargs)
        self.memory.add_record("execution",initial_result)

        # 2.迭代循环，反思与优化
        for i in range(self.max_iterations):
            print(f"\n---第{i+1}/{self.max_iterations}轮迭代---")

            # a.反思
            print("\n -> 正在进行反思...")
            last_result = self.memory.get_last_execution()
            
            # ⭐️ [修复 1: KeyError: 'code'] ⭐️
            # 您的 code_prompts 期望 {code}, 而不是 {content}
            reflect_prompt = self.prompts['reflect'].format(
                task = task,
                code = last_result  # <-- 修复了 'content' -> 'code'
            )
            feedback = self._get_llm_response(reflect_prompt,**kwargs)
            self.memory.add_record("reflection",feedback)

            # b.检查是否需要停止
            if "无需改进" in feedback or "no need for improvement" in feedback.lower():
                print("\n✅ 反思认为结果已无需改进，任务完成。")
                break

            # c.优化
            print("\n -> 正在进行优化...")
            
            # ⭐️ [修复 2: 潜在的 KeyError] ⭐️
            # 您的 code_prompts (refine) 只期望 {task} 和 {feedback}
            # 它不需要 {content} 或 {last_attempt}
            refine_prompt = self.prompts['refine'].format(
                task = task,
                feedback = feedback
            )
            refined_result = self._get_llm_response(refine_prompt,**kwargs)
            self.memory.add_record("execution",refined_result)
        
        final_result = self.memory.get_last_execution()
        print(f"\n---任务完成---\n最终结果:\n{final_result}")

        # 保存到历史记录
        self.add_message(Message(input_text,"user"))
        self.add_message(Message(final_result,"assistant"))

        return final_result

    def _get_llm_response(self, prompt: str, **kwargs) -> str:
        """调用LLM并获取完整响应"""
        messages = [{"role": "user", "content": prompt}]
        # 确保 invoke 总是返回字符串 (or "" 是个好习惯)
        return self.llm.invoke(messages, **kwargs) or ""