import asyncio
import os
import datetime
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

async def generate_date_file(mcp_server: MCPServer):
    # 获取当前日期和时间
    now = datetime.datetime.now()
    
    # 格式化日期和星期
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekdays[now.weekday()]
    date_str = now.strftime("%Y年%m月%d日 %H:%M:%S")
    
    # 创建文件内容
    file_content = f"当前日期和时间: {date_str}\n今天是: {weekday}"
    
    # 从.env文件中获取主目录
    home_dir = os.getenv("HOME_DIR")
    
    # 生成文件名
    file_name = f"{home_dir}/tmp/date_{now.strftime('%Y%m%d_%H%M%S')}.txt"
    
    agent = Agent(
        name="文件助手",
        instructions="你是一个文件助手，可以创建、读取和分析文件。请使用filesystem MCP服务器来访问文件。",
        mcp_servers=[mcp_server],
        model=model_name
    )
    
    # 创建文件操作指令
    message = f"请在 {file_name} 创建一个新文件，内容为:\n{file_content}"
    print("\n" + "-" * 40)
    print(f"执行: {message}")
    
    # 配置运行环境
    run_config = RunConfig(
        model_settings=ModelSettings(
            max_tokens=8192
        ),
        model_provider=OpenAIProvider(
            api_key=api_key,
            base_url=base_url,
            use_responses=False
        ),
        tracing_disabled=True
    )
    
    # 执行创建文件的操作
    result = await Runner.run(
        starting_agent=agent,
        input=message,
        run_config=run_config
    )
    print(result.final_output)
    
    # 读取并显示文件内容
    message = f"请读取并显示 {file_name} 的内容"
    print("\n" + "-" * 40)
    print(f"执行: {message}")
    
    result = await Runner.run(
        starting_agent=agent,
        input=message,
        run_config=run_config
    )
    print(result.final_output)
    
    return file_name


async def main():
    print("开始运行文件日期生成器...")    
    
    async with MCPServerStdio(
        cache_tools_list=True,  # 缓存工具列表，用于演示
        params={
            "command": "node",
            "args": [
                # 需要npm全局安装依赖 @modelcontextprotocol/server-filesystem
                f"{os.getenv('HOME_DIR')}/.config/nvm/versions/node/v22.14.0/lib/node_modules/@modelcontextprotocol/server-filesystem/dist/index.js",
                f"{os.getenv('HOME_DIR')}/tmp"
            ],
            "model": model_name,
            "api_key": api_key,  # 添加API密钥
            "base_url": base_url  # 添加从.env中读取的base_url
        },
    ) as server:
        generated_file = await generate_date_file(server)
        print(f"\n成功创建文件: {generated_file}")


if __name__ == "__main__":
    asyncio.run(main())
