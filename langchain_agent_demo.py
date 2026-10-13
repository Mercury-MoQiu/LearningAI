"""
基于 LangChain 的 Agent 示例
参考: https://blog.csdn.net/AustinCyy/article/details/145114656
改用智谱 GLM API 替代 OpenAI API
"""

import os
import warnings
from datetime import date

warnings.filterwarnings("ignore")

from langchain_community.chat_models import ChatZhipuAI
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.agents import initialize_agent, AgentType, tool
from langchain_experimental.agents.agent_toolkits import create_python_agent
from langchain_experimental.tools.python.tool import PythonREPLTool

# ====== 智谱 API 配置（从 .env 读取，.env 不入库） ======
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
if not os.getenv("ZHIPUAI_API_KEY"):
    raise RuntimeError("请先在项目根目录的 .env 文件中设置 ZHIPUAI_API_KEY（参考 .env.example）")


class ChatZhipuAIReAct(ChatZhipuAI):
    """修复版 ChatZhipuAI：GLM API 的返回内容会包含 stop 字符串本身
    （OpenAI 会在 stop 之前截断），导致 ReAct agent 的 Observation 泄漏、
    动作循环。这里在客户端手动截断 stop 序列。"""

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        result = super()._generate(
            messages, stop=stop, run_manager=run_manager, **kwargs
        )
        if stop:
            for gen in result.generations:
                content = gen.message.content
                if isinstance(content, str):
                    cut = len(content)
                    for s in stop:
                        idx = content.find(s)
                        if idx != -1:
                            cut = min(cut, idx)
                    gen.message.content = content[:cut]
        return result


# 初始化 LLM，temperature=0 降低随机性
# 注：ReAct agent 对模型的指令遵循能力要求较高，glm-4-flash 会出现
# 复读/格式错乱导致死循环，这里使用更强的 glm-4-air
llm = ChatZhipuAIReAct(model="glm-4-air", temperature=0)


def demo_math_and_wikipedia():
    """示例一：Calculator（数学计算）+ wikipedia（维基百科搜索）工具"""
    print("\n" + "=" * 60)
    print("示例一：Calculator + wikipedia 工具")
    print("=" * 60)

    # 自定义计算工具，与 llm-math 底层一样用 numexpr 求值
    # 注：原文用 load_tools(["llm-math"], llm=llm)，但 llm-math 内部要求模型
    # 严格输出 ```text 代码块格式，GLM 会输出 ```python 导致解析失败，
    # 因此这里用 numexpr 自定义等效工具
    @tool
    def Calculator(expression: str) -> str:
        """Useful for when you need to answer questions about math.
        The input should be a single-line mathematical expression,
        e.g. 300*0.25"""
        import numexpr
        result = numexpr.evaluate(expression)
        try:
            return str(result.item())
        except (AttributeError, ValueError):
            return str(result)

    # 加载 wikipedia 工具（需能访问 en.wikipedia.org，网络不通时会捕获异常）
    tools = [Calculator]
    try:
        tools += load_tools(["wikipedia"], llm=llm)
    except Exception as e:
        print(f"[wikipedia 工具加载失败: {type(e).__name__}]")

    # 初始化 agent：CHAT_ZERO_SHOT_REACT_DESCRIPTION 即 ReAct 模式
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        max_iterations=6,  # 兜底，防止意外死循环
        verbose=True,
    )

    # 1. 数学计算问题
    print("\n--- 数学计算 ---")
    try:
        agent.invoke("What is the 25% of 300?")
    except Exception as e:
        print(f"[数学计算失败: {type(e).__name__}: {e}]")

    # 2. 维基百科搜索（国内网络可能访问失败，捕获异常）
    print("\n--- 维基百科搜索 ---")
    question = (
        "Tom M. Mitchell is an American computer scientist "
        "and the Founders University Professor at Carnegie Mellon University (CMU) "
        "what book did he write?"
    )
    try:
        agent.invoke(question)
    except Exception as e:
        print(f"[维基百科访问失败（通常是网络原因）: {type(e).__name__}]")


def demo_python_agent():
    """示例二：Python Agent —— 让 LLM 编写并执行 Python 代码"""
    print("\n" + "=" * 60)
    print("示例二：Python Agent（辅助编程）")
    print("=" * 60)

    agent = create_python_agent(
        llm,
        tool=PythonREPLTool(),
        max_iterations=6,  # 兜底，防止意外死循环
        verbose=True,
        handle_parsing_errors=True,
    )

    customer_list = [
        ["Harrison", "Chase"],
        ["Lang", "Chain"],
        ["Dolly", "Too"],
        ["Elle", "Elem"],
        ["Geoff", "Fusion"],
        ["Trance", "Former"],
        ["Jen", "Ayai"],
    ]

    agent.invoke(
        f"Sort these customers by last name and then first name "
        f"and print the output: {customer_list}"
    )

def demo_custom_tool():
    """示例三：自定义工具 —— 返回当前日期的 time 工具"""
    print("\n" + "=" * 60)
    print("示例三：自定义工具（time）")
    print("=" * 60)

    @tool
    def time(text: str) -> str:
        """Returns todays date, use this for any questions related to knowing
        todays date. The input should always be an empty string, and this
        function will always return todays date - any date mathmatics should
        occur outside this function."""
        return str(date.today())

    tools = load_tools(["llm-math"], llm=llm)

    agent = initialize_agent(
        tools + [time],  # 把自定义工具加进工具列表
        llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        max_iterations=6,  # 兜底，防止意外死循环
        verbose=True,
    )

    agent.invoke("whats the date today?")


if __name__ == "__main__":
    demo_math_and_wikipedia()
    demo_python_agent()
    demo_custom_tool()
