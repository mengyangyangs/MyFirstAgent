from dotenv import load_dotenv
from my_llm import MyLLM

load_dotenv()

# 使用Gemini API
# llm = MyLLM(provider="gemini")

llm = MyLLM(provider="modelscope")

messages = [{"role":"user","content":"你好，请介绍一下自己"}]

response_stream = llm.think(messages)

# Gemini 的回答
# print("Gemini Response: ")
# for chunk in response_stream:
#     print(chunk, end="", flush=True)

print("ModelScope Response: ")
for chunk in response_stream:
    print(chunk, end="", flush=True)