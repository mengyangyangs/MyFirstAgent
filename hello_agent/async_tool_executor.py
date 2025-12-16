# 异步工具执行支持
import asyncio # 导入asyncio库，用于编写单线程并发代码
import concurrent.futures # 导入concurrent.futures模块，特别是ThreadPoolExecutor，用于在单独的线程中执行阻塞操作
from typing import Dict,List,Any,Callable # 导入类型提示，增强代码可读性和健壮性
from hello_agents import ToolRegistry # 从hello_agents库导入ToolRegistry，这是一个用于管理和执行工具的类

class AsyncToolExecutor:
    """
    异步工具执行器。
    这个类的主要功能是接收同步的工具函数调用，并通过一个线程池来异步地执行它们，
    从而避免在asyncio事件循环中发生阻塞。
    """
    def __init__(self,registry:ToolRegistry,max_workers:int = 4):
        """
        初始化异步工具执行器。
        :param registry: ToolRegistry的实例，包含了所有可用的工具。
        :param max_workers: 线程池中的最大工作线程数。
        """
        self.registry = registry # 保存工具注册表的引用
        # 创建一个线程池执行器，用于在后台线程中运行同步函数
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def execute_tool_async(self,tool_name:str,input_data:str) -> str:
        """
        异步地执行单个工具。
        这个方法将一个同步的工具执行调用（self.registry.execute_tool）包装成一个可以在asyncio中等待的异步任务。
        它通过在线程池中运行同步函数来实现这一点。
        """
        loop = asyncio.get_event_loop() # 获取当前的asyncio事件循环

        # 定义一个内部函数，该函数将执行实际的同步工具调用
        # 这是因为 loop.run_in_executor 需要一个不带参数的可调用对象
        def _execute():
            return self.registry.execute_tool(tool_name,input_data)
        
        # 在线程池（self.executor）中执行_execute函数，并等待其结果
        # 这使得同步的、可能耗时的操作不会阻塞事件循环
        result = await loop.run_in_executor(self.executor,_execute)
        return result # 返回工具执行的结果

    async def execute_tools_paraller(self,tasks:List[Dict[str,str]]) -> List[str]:
        """
        并行地执行多个工具任务。
        这个方法接收一个任务列表，为每个任务创建一个异步执行协程，并使用 asyncio.gather 来并发运行它们。
        """
        print(f"开始并执行{len(tasks)}个工具任务")

        # 创建一个列表，用于存放所有的异步任务（协程）
        async_tasks = []
        for task in tasks:
            # 从任务字典中解析出工具名称和输入数据
            tool_name = task["tool_name"]
            input_data = task["input_data"]
            # 为每个任务调用 execute_tool_async，创建一个协程对象
            async_task = self.execute_tool_async(tool_name,input_data)
            # 将创建的协程添加到任务列表中
            async_tasks.append(async_task)

        # 使用 asyncio.gather 并发地运行列表中的所有协程，并等待它们全部完成
        # `*async_tasks` 是将列表解包成独立的参数传递给 gather
        results = await asyncio.gather(*async_tasks)

        print("所有工具执行完毕")
        return results # 返回一个包含所有任务结果的列表，其顺序与输入任务的顺序相对应

    def __del__(self):
        """
        对象销毁时的清理操作。
        确保线程池被安全地关闭，释放所有资源。
        """
        # 检查executor属性是否存在，以防初始化失败
        if hasattr(self,'executor'):
            # 关闭线程池，wait=True表示等待所有正在执行的任务完成后再关闭
            self.executor.shutdown(wait=True)

# 使用示例
async def test_parallel_execution():
    """ 
    测试并行工具执行功能的示例异步函数。
    这个函数展示了如何实例化AsyncToolExecutor并用它来并行处理一组不同的工具调用。
    """
    # 动态导入，通常在示例或测试代码中这样做
    from hello_agents import ToolRegistry

    # 创建一个工具注册表实例
    registry = ToolRegistry()

    # 创建一个异步工具执行器实例
    executor = AsyncToolExecutor(registry)

    # 定义一个任务列表，每个任务都是一个字典，包含要调用的工具名和输入数据
    tasks = [
        {"tool_name":"search","input_data":"python编程"},
        {"tool_name":"search","input_data":"机器学习"},
        {"tool_name":"calculator","input_data":"2+2"},
        {"tool_name":"calculator","input_data":"sqrt(16)"},
    ]

    # 调用并行执行方法，并等待所有任务完成
    results = await executor.execute_tools_paraller(tasks)
    print("并行执行结果:",results)

    # 遍历并打印每个任务的结果（为了简洁，只显示结果的前100个字符）
    for i,result in enumerate(results,1):
        print(f"任务 {i+1} 结果:{result[:100]}...")
