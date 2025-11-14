# agent_runner.py
import os
import asyncio
from logger_setup import setup_logger
from report import TestReport, StepRecord

# LangChain imports
from langchain.chat_models import ChatOpenAI
from langchain.agents.react.agent import create_react_agent

# MCP adapter
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = setup_logger()

async def run_agent_test(openai_api_key: str):
    # 1) 初始化 LLM（OpenAI）
    llm = ChatOpenAI(model_name="gpt-4", openai_api_key=openai_api_key, temperature=0)

    # 2) 配置 MultiServerMCPClient：本示例让 client 通过 npx 启动 Playwright MCP 本地进程
    #    你也可以改成已运行的远程 MCP 服务器，方式见下方注释
    mcp_servers = {
        "playwright": {
            # 使用 npx 启动 Playwright MCP（README 推荐配置）
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest", "--port", "8931"],
            # 可添加 env、allowed-hosts 等其他启动参数
        }
    }

    report = TestReport(test_name="NVIDIA CN basic navigation test", environment="local-playwright-mcp")

    async with MultiServerMCPClient(mcp_servers) as client:
        logger.info("MultiServerMCPClient started and MCP servers launching/connected.")

        # 3) 从 MCP 获取工具（注意：get_tools() 在多数实现中为 awaitable）
        tools = await client.get_tools()
        logger.info(f"Loaded {len(tools)} tool(s) from MCP servers.")
        for t in tools:
            logger.info(f" - tool: {getattr(t, 'name', repr(t))}")

        # 4) 创建 ReAct agent（使用 MCP 工具）
        agent = create_react_agent(llm=llm, tools=tools)
        logger.info("Agent created with MCP tools.")

        # 5) 准备用户指令（中文），你可以改成任何测试需求
        user_input = (
            "请打开 https://www.nvidia.cn/ ，"
            "在页面加载后，尝试通过页面导航进入 GeForce/产品相关页面（如果需要点击“产品”或“GeForce”），"
            "最后验证页面标题或主要 h1 包含 'GeForce' 或 'RTX' 等关键字（请在执行过程中把每步的结果输出）。"
        )

        # 6) 把整个 agent 执行当做一个 Step（你也可以使用回调来捕获每次工具调用以细化步骤）
        main_step = StepRecord("Agent: run full navigation+assertion scenario")
        report.add_step(main_step)
        try:
            # 调用 agent：大多数 create_react_agent 的返回对象支持 async .ainvoke 或 .arun 接口
            # 我们使用 ainvoke 并传入 messages / input 文本（不同版本 Agent 接口可能略有差异）
            logger.info("Invoking agent (ainvoke) ...")
            # 尝试两种常见调用方式以兼容不同版本：
            try:
                # 首选：ainvoke with {"messages": "..."} (seen in many examples)
                response = await agent.ainvoke({"messages": user_input})
            except TypeError:
                # fallback: ainvoke({"input": ...})
                response = await agent.ainvoke({"input": user_input})

            logger.info("Agent finished running.")
            main_step.mark_passed(message=str(response))
        except Exception as e:
            logger.exception("Agent execution failed.")
            main_step.mark_failed(message=str(e))

        # 完成并保存报告
        report.mark_finished()
        os.makedirs("reports", exist_ok=True)
        report.save_json("reports/last_report.json")
        report.save_markdown("reports/last_report.md")
        report.save_html("reports/last_report.html")
        logger.info("Reports saved under ./reports/")

def main():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError("Please set OPENAI_API_KEY environment variable before running.")
    asyncio.run(run_agent_test(openai_api_key))

if __name__ == "__main__":
    main()
