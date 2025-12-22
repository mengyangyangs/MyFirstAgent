AGENT_SYSTEM_PROMPT = """
你是一个智能旅行助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具：
- 'get_weather(city:str)':查询指定城市的实时天气。
- 'get_attraction(city:str,weather:str)':根据城市和天气搜索推荐的旅游景点。

# 行动格式：
你的回答必须严格遵循以下格式。首先是你的思考过程，然后是你要执行的具体行动。
Thought:[这里是你的思考过程和下一步计划]
Action:[这你是你要调用的工具，格式为 function_name(arg_name''arg_value')]

# 任务完成：
当你收集到足够的信息，能够回答用户的最终问题时，你必须使用'finish(answer="...")'来输出最终答案。

请开始吧！
"""
import requests
import json

def get_weather(city:str) -> str:
    """
    通过调用wttr.in API 查询真实的天气信息
    """
    # API端点，我们请求json格式的数据
    url = f"https://wttr.in/{city}?format=j1"

    try:
        # 发起网络请求
        response = requests.get(url)
        # 检查响应状态是否为200(成功)
        response.raise_for_status()
        # 解析返回的JSON数据
        data = response.json()
        # 提取当前天气状况
        current_condition = data['current_condition'][0] # 大白话说就是data字典中的current_condition键对应的值，这个值是一个列表，列表中第一个元素是当前天气状况
        weather_desc = current_condition['weatherDesc'][0]['value'] # 大白话说就是current_condition列表中第一个元素的weatherDesc键对应的值，这个值是一个列表，列表中第一个元素是天气描述
        temp_c = current_condition['temp_C'] # 大白话说就是current_condition列表中第一个元素的temp_C键对应的值，这个值是当前气温
        # 格式化成自然语言返回
        return f"{city}当前天气:{weather_desc},气温:{temp_c}摄氏度"
    except requests.exceptions.RequestException as e:
        # 处理网络错误
        return f"错误:查询天气时遇到问题 - {e}"
    except (KeyError, IndexError) as e:
        # 处理数据解析错误
        return f"错误:解析天气数据失败，可能是城市名无效 - {e}"
    
import os
from tavily import TavilyClient

def get_attraction(city:str,weather:str) -> str:
    """
    根据城市和天气，使用Tavily Seach API搜索并返回优化后的景点推荐
    """
    # 1.从环境变量中读取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误:未配置TAVILY_API_KEY环境变量。"
    # 2.创建Tavily客户端
    tavily = TavilyClient(api_key=api_key)
    # 3.构建一个精确的查询
    query = f"{city}在{weather}天气下最值得去的旅游景点以及推荐理由"
    try:
        # 4.调用API，include_answer=True返回一个综合性的回答
        response = tavily.search(query=query,search_depth="basic",include_answer=True) # search_depth表示搜索深度，basic表示快速，轻量搜索
        # 5.Tavily返回的结果已经非常干净，可以直接使用
        # response['answer']是一个基于所有搜索结果的总结性回答
        if response.get("answer"):
            return response["answer"]
        # 如果没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results",[]):
            formatted_results.append(f"- {result["title"]}:{result["content"]}")
        
        if not formatted_results:
            return "抱歉:没有找到相关的景点推荐。"

        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"

# 将所有工具函数放入一个字典，方便后续调用
avaliable_tools = {
    "get_weather": get_weather,
    "get_attraction": get_attraction,
}

# from openai import OpenAI # 没钱调用openai的API，所以用google的gemini
from google import genai # 确保已经安装 pip install google-genai

class GeminiClient:
    """
    一个用于调用Google Gemini服务的客户端。
    """
    def __init__(self, model:str, api_key:str):
        self.model = model
        # 移除 base_url
        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt:str, system_prompt:str) -> str:
        """
        调用LLM API来生成回应。
        """
        print("正在调用大语言模型...")
        try:
            # --- 关键修改：Gemini SDK 的调用方式 ---
            
            # 1. 构造消息列表 (contents)
            messages = [
                # 用户输入，包含历史记录和当前指令
                {"role":"user","parts":[{"text": prompt}]} 
            ]
            
            # 2. 构造配置 (config)
            # 在 Gemini SDK 中，系统提示和工具信息是通过 config 参数传递的
            config = {
                "system_instruction": system_prompt,
                # 传入可用工具列表
                "tools": [{"function_declarations": [
                    {
                        "name": "get_weather",
                        "description": "查询指定城市的实时天气。",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {"city": {"type": "STRING", "description": "要查询的城市名称，例如“北京”"}},
                            "required": ["city"]
                        }
                    },
                    {
                        "name": "get_attraction",
                        "description": "根据城市和天气搜索推荐的旅游景点。",
                        "parameters": {
                            "type": "OBJECT",
                            "properties": {
                                "city": {"type": "STRING", "description": "要查询的城市名称"},
                                "weather": {"type": "STRING", "description": "当前的天气状况，例如“多云，气温:15摄氏度”"}
                            },
                            "required": ["city", "weather"]
                        }
                    }
                ]}]
            }

            # 3. 调用 generate_content
            response = self.client.models.generate_content(
                model = self.model,
                contents = messages,
                config = config
            )
            
            # --- 解析响应 ---
            
            # 检查是否有函数调用请求 (Function Call)
            if response.function_calls:
                # 构造符合您现有 Action: 格式的输出
                call = response.function_calls[0]
                tool_name = call.name
                args_str = ", ".join([f'{k}="{v}"' for k, v in dict(call.args).items()])
                
                # 假设您模型中的 Thought: 是模型生成的，这里我们先省略模型生成的 Thought
                # 而是直接构造 Action
                return f"Thought:模型已决定调用工具来执行下一步操作。\nAction:{tool_name}({args_str})"
            
            # 如果没有函数调用，则返回文本内容
            answer = response.text
            print("大语言模型响应成功")
            return answer
        
        except Exception as e:
            # 为了调试，这里打印完整的错误
            print(f"调用LLM API时发生错误: {e}")
            # 返回一个固定的错误消息
            return "错误:调用语言模型服务时出错。"

import re
# --- 1.配置LLM客户端 ---
# 请根据您使用的服务，将这里替换成对应的凭证和地址
API_KEY = "YOUR_API_KEY"
# BASE_URL = "https://aistudio.google.com/"
MODEL_ID = "gemini-2.5-flash"
TAVILY_API_KEY = "YOUR_API_KEY"
os.environ["TAVILY_API_KEY"] = "YOUR_API_KEY"

llm = GeminiClient(
    model = MODEL_ID,
    api_key = API_KEY
    # base_url = BASE_URL
)

# --- 2.初始化 ---
user_prompt = "你好，请帮我查询一下今天柳州的天气，然后根据天气推荐一个适合旅游的景点"
prompt_history = [f"用户请求:{user_prompt}"]
print(f"用户输入：{user_prompt}\n" + "="*40)

# --- 3.运行主循环 ---
for i in range(5):
    print(f" --- 循环{i+1} ---\n")

    # 3.1 构建prompt
    full_prompt = "\n".join(prompt_history)

    # 3.2 调用LLM进行思考
    llm_output = llm.generate(full_prompt,system_prompt=AGENT_SYSTEM_PROMPT)
    print(f"模型输出:\n{llm_output}\n")
    prompt_history.append(llm_output)

    # 3.3 解析并执行行动
    action_match = re.search(r"Action:(.*)",llm_output,re.DOTALL)
    if not action_match:
        print("解析错误:模型输出中为找到 Aciton")
        break
    action_str = action_match.group(1).strip()

    if action_str.startswith("finish"):
        final_answer = re.search(r'finish\(answer="(.*)"\)', action_str).group(1)
        print(f"任务完成，最终答案:{final_answer}")
        break

    tool_name = re.search(r"(\w+)\(",action_str).group(1)
    args_str = re.search(r"\((.*)\)",action_str).group(1)
    kwargs = dict(re.findall(r'(\w+)="([^"]*)"',args_str))

    if tool_name in avaliable_tools:
        observation = avaliable_tools[tool_name](**kwargs)
    else:
        observation = f"错误:未定义的工具'{tool_name}'"

    # 3.4 记录观察结果
    observation_str = f"Observation:{observation}"
    print(f"{observation_str}\n" + "="*40)
    prompt_history.append(observation_str)
