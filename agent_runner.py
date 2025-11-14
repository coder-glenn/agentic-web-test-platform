# agent_runner.py

from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
import os
from tools import navigate, click_selector, type_text, wait_for, assert_text
from logger_setup import setup_logger
logger = setup_logger("logs/test_agent.log", level=logging.INFO)

def main():
    # 获取 OpenAI API Key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable")

    # 初始化 LLM
    llm = ChatOpenAI(model="gpt-4", temperature=0)  # 你可以调整为 gpt-3.5-turbo 等

    # 准备工具列表
    tools = [navigate, click_selector, type_text, wait_for, assert_text]

    # 初始化 agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )

    logger.info("Agent runner started")
    # 用户输入测试指令／场景
    user_input = """请打开 https://www.nvidia.cn/ ，然后点击上方导航 “产品”，选择 “GeForce” 系列，进入 “GeForce RTX 4090” 页面，并验证页面标题包含 “GeForce RTX 4090”。"""

    # 执行 agent
    try:
        result = agent.run(user_input)
        logger.info(f"Agent run completed – result: {result}")
    except Exception as e:
        logger.exception("Agent run encountered exception")
    finally:
        logger.info("Agent runner finished")

    # 输出结果
    print("=== Agent 执行结果 ===")
    print(result)

if __name__ == "__main__":
    main()
