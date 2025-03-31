import asyncio
import os
from dotenv import load_dotenv

from agents import Agent, Runner
from agents.mcp import MCPServer, MCPServerStdio
from agents.model_settings import ModelSettings
from agents.run import RunConfig
from agents.models.openai_provider import OpenAIProvider

# 在文件开头加载环境变量
load_dotenv()

# 从.env文件中获取OpenAI配置
model_name = os.getenv("OPENAI_MODEL_NAME")  # 使用默认值作为备选
base_url = os.getenv("OPENAI_API_BASE")  # 获取API基础URL
api_key = os.getenv("OPENAI_API_KEY")  # 获取API密钥


# 显示当前配置
print(f"\n当前 OpenAI 配置:")
print(f"- API 基础网址: {base_url}")
print(f"- 模型名称: {model_name}")

async def run(mcp_server: MCPServer, repo_path: str):    
    agent = Agent(
        name="Git助手",
        instructions=f"你是一个Git仓库分析助手，可以分析{repo_path}仓库的信息。请使用git MCP服务器来执行各种git命令。",
        mcp_servers=[mcp_server],
        model=model_name,
    )
    

    message = f"step1) 当前是什么分支？"
    print("\n" + "-" * 40)
    print(f"执行: {message}")
    # 使用RunConfig配置API参数，并使用model_provider参数
    run_config = RunConfig(
        model_settings=ModelSettings(
            max_tokens=8192
        ),        
        model_provider=OpenAIProvider(
            api_key=api_key,
            base_url=base_url,
            use_responses=False
        ),
        tracing_disabled = True
    )
    
    result = await Runner.run(
        starting_agent=agent,
        input=message,
        run_config=run_config
    )
    print(result.final_output)


    message = f"step2) 请分析{repo_path}仓库的最近5次提交，并总结修改内容。"
    print("\n" + "-" * 40)
    print(f"执行: {message}")
    
    result = await Runner.run(
        starting_agent=agent,
        input=message,
        run_config=run_config
    )
    print(result.final_output)

    message = f"step3) 请分析{repo_path}仓库的分支结构，哪些分支最活跃？"
    print("\n" + "-" * 40)
    print(f"执行: {message}")
    
    result = await Runner.run(
        starting_agent=agent,
        input=message,
        run_config=run_config
    )
    print(result.final_output)


async def main():
    # 默认仓库路径
    repo_path = os.getcwd()  # 使用当前目录作为默认值
    
    # 从.env文件中获取主目录
    home_dir = os.getenv("HOME_DIR")
    
    # 可选：让用户输入仓库路径，要求是本地的git仓库跟根目录
    user_input = f"{home_dir}/Gits/mcp-off-servers"
    if user_input.strip():
        repo_path = user_input.strip()

    async with MCPServerStdio(
        cache_tools_list=True,  # 缓存工具列表，用于演示
        params={
            "command": "uv", 
            "args": [
                "--directory",
                f"{home_dir}/Gits/mcp-off-servers/src/git", # 本地的mcp server运行路径
                "run",
                "mcp-server-git"
            ],
            "model": model_name,
            "api_key": api_key,  # 添加API密钥
            "base_url": base_url  # 添加从.env中读取的base_url
        },
    ) as server:        
        await run(server, repo_path)


if __name__ == "__main__":
    asyncio.run(main())
