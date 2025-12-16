import os
# 导入os模块，用于访问环境变量，例如获取API密钥
from typing import Optional,List,Dict,Any
# 导入类型提示，增强代码的可读性和健壮性
from hello_agents import ToolRegistry
# 从hello_agents库导入ToolRegistry，用于注册和管理工具

class MyAdvancedSearchTool:
    """
    自定义高级搜索工具类。
    这个类的设计目标是整合多个不同的搜索API（如Tavily、Serper），
    并根据可用性自动选择最佳的搜索源。
    这种模式提高了工具的鲁棒性和适应性。
    """
    def __init__(self):
        """
        类的构造函数（初始化方法）。
        在创建类的实例时被调用，用于设置初始属性。
        """
        self.name = "my_advanced_search"  # 定义工具的名称
        self.description = "智能搜索工具，支持多个搜索源，自动选择最佳结果"  # 定义工具的功能描述
        self.search_sources = []  # 初始化一个空列表，用于存储可用的搜索源名称
        self._setup_search_sources()  # 调用内部方法来检测和配置可用的搜索源

    def _setup_search_sources(self):
        """
        一个内部方法，用于检测环境变量中配置的API密钥，并据此设置可用的搜索源。
        """
        # --- 检查Tavily搜索源的可用性 ---
        # 检查名为"TAVILY_API_KEY"的环境变量是否存在
        if os.getenv("TAVILY_API_KEY"):
            try:
                # 尝试导入Tavily客户端库
                from tavily import TavilyClient
                # 如果导入成功，则创建Tavily客户端实例
                self.tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                # 将'tavily'添加到可用搜索源列表中
                self.search_sources.append("tavily")
                print("Tavily搜索源已启用")
            except ImportError:
                # 如果tavily库没有安装，则捕获ImportError并打印提示信息
                print("Tavily库未安装")

        # --- 检查Serper搜索源的可用性 ---
        # 检查名为"SERPER_API_KEY"的环境变量是否存在
        if os.getenv("SERPER_API_KEY"):
            try:
                # 尝试导入serpapi库以确认其可用性
                import serpapi
                # 将'serper'添加到可用搜索源列表中
                self.search_sources.append("serper")
                print("Serper搜索源已启用")
            except ImportError:
                # 如果serpapi库没有安装，则捕获ImportError并打印提示信息
                print("Serper库未安装")
        
        # 在设置完成后，打印最终的可用搜索源列表
        if self.search_sources:
            print(f"🔧 可用搜索源: {', '.join(self.search_sources)}")
        else:
            # 如果没有任何可用的搜索源，打印警告信息
            print("⚠️ 没有可用的搜索源，请配置API密钥")

    def search(self,query:str) -> str:
        """
        执行智能搜索的核心公共方法。
        它会按顺序尝试所有已启用的搜索源，直到获得一个有效结果为止。
        """
        # 检查输入的查询字符串是否为空或只包含空格
        if not query.strip():
            return "错误，搜索查询不能为空"

        # 检查是否有任何配置好的搜索源
        if not self.search_sources:
            # 如果没有，则返回一段帮助信息，指导用户如何配置API密钥
            return """ 没有可用的搜索源，请配置以下API密钥之一：
    1.Tavily API：设置环境变量 TAVILY_API_KEY
    获取地址：https://tavily.com/
    2.Serper API：设置环境变量 SERPER_API_KEY
    获取地址：https://serper.dev/
    """ 
        print(f"开始智能搜索:{query}")

        # --- 依次尝试所有可用的搜索源 ---
        # 遍历在_setup_search_sources中初始化的搜索源列表
        for source in self.search_sources:
            try:
                # 如果当前搜索源是 'tavily'
                if source == "tavily":
                    result = self._search_with_tavily(query)
                    # 检查结果是否有效（非空且不包含错误信息）
                    if result and "未找到" not in result:
                        return f"Tavily搜索结果是:{result}"  # 如果有效，立即返回结果

                # 如果当前搜索源是 'serper'
                elif source == "serper":
                    result = self._search_with_serper(query)
                    # 检查结果是否有效
                    if result and "未找到" not in result:
                        return f"Serper搜索结果是:{result}"  # 如果有效，立即返回结果
            
            except Exception as e:
                # 如果在调用某个搜索源API时发生任何异常，打印错误信息并继续尝试下一个源
                print(f"{source}搜索失败:{e}")
                continue

        # 如果遍历完所有搜索源都没有成功返回结果，则返回最终的失败信息
        return "所有搜索源都失败了，请检查网络和API"

    def _search_with_tavily(self,query:str) -> str:
        """
        使用Tavily API执行搜索的内部方法。
        """
        # 调用Tavily客户端的search方法，设置查询和最大结果数
        response = self.tavily.search(query=query,max_results=3)

        # 检查Tavily是否返回了AI生成的直接答案
        if response.get("answer"):
            result = f"AI直接答案:{response['answer']}\n\n"
        else:
            result = " "
        
        # 拼接相关搜索结果的标题
        result += "相关结果:\n"

        # 遍历返回的搜索结果列表（最多取前3个）
        for i, item in enumerate(response.get('results', [])[:3], 1):
            # 格式化每条结果，包括序号、标题和内容摘要
            result += f"[{i}] {item.get('title', '')}\n"
            # 内容摘要只取前150个字符，以保持简洁
            result += f"    {item.get('content', '')[:150]}...\n\n"

        return result

    def _search_with_serper(self,query:str) -> str:
        """
        使用Serper (Google Search) API执行搜索的内部方法。
        """
        # 在函数内部导入serpapi，这是一种延迟加载的模式
        import serpapi

        # 创建GoogleSearch对象并配置参数
        search = serpapi.GoogleSearch({
            "q":query,  # 设置搜索查询
            "api_key":os.getenv("SERPER_API_KEY"),  # 从环境变量获取API密钥
            "num":3  # 请求返回的结果数量
        })   

        # 执行搜索并获取字典格式的返回结果
        results = search.get_dict()

        # 初始化结果字符串
        result = "Google搜索结果:\n"
        # 检查响应中是否包含'organic_results'（自然搜索结果）
        if "organic_results" in results:
            # 遍历自然搜索结果列表（最多取前3个）
            for i, res in enumerate(results["organic_results"][:3], 1):
                # 格式化每条结果，包括序号、标题和摘要（snippet）
                result += f"[{i}] {res.get('title', '')}\n"
                result += f"    {res.get('snippet', '')}\n\n"
            
        return result

def create_advanced_search_registry():
    """
    一个工厂函数，用于创建并配置一个包含高级搜索工具的ToolRegistry实例。
    这个函数封装了工具的实例化和注册过程。
    """
    # 创建一个ToolRegistry的实例
    registry = ToolRegistry()

    # 创建MyAdvancedSearchTool工具的实例
    search_tool = MyAdvancedSearchTool()

    # 将search_tool实例的search方法注册到registry中
    registry.register_function(
        name = "advanced_search",  # 为工具函数指定一个在系统中唯一的调用名称
        description = "高级搜索工具，整合Tavily和SerpAPI多个搜索源，提供更全面的搜索结果",  # 提供该工具功能的详细描述
        func = search_tool.search  # 指定实际要调用的函数是search_tool实例的search方法
    )
    # 返回配置好的注册表实例，以便在其他地方使用
    return registry
