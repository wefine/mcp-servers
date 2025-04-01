#!/usr/bin/env python
"""
天气服务MCP CLI
"""

import typer
import logging
import os
from dotenv import load_dotenv
from mcp_server_weather.server import mcp, HOST, PORT, AMAP_KEY

app = typer.Typer(help="天气MCP服务器CLI")
logger = logging.getLogger(__name__)

@app.command()
def start(
    host: str = typer.Option(None, "--host", "-h", help="服务器主机地址"),
    port: int = typer.Option(None, "--port", "-p", help="服务器端口"),
    debug: bool = typer.Option(False, "--debug", help="启用调试模式")
):
    """
    启动天气MCP服务器
    """
    # 加载环境变量配置
    load_dotenv()
    
    # 设置日志级别
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # 优先使用命令行参数，其次使用环境变量
    final_host = host or HOST
    final_port = port or PORT
    
    # 检查API密钥
    if AMAP_KEY == "your_amap_key_here":
        logger.warning("您正在使用默认的高德地图API密钥，请设置AMAP_KEY环境变量")
    
    logger.info(f"正在启动天气MCP服务器，地址: {final_host}:{final_port}...")
    
    # 启动MCP服务器
    mcp.run()

def main():
    """
    CLI主入口点
    """
    app()

if __name__ == "__main__":
    main()
