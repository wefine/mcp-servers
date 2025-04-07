#!/usr/bin/env python
"""
天气服务MCP SSE服务器

这个模块提供了基于SSE (Server-Sent Events)的MCP服务器实现，
允许客户端通过HTTP连接接收服务器的推送事件。
使用FastAPI框架提供更灵活的API功能。
"""

import logging
import os
import signal
import sys
import threading
import time
import termios
import tty
import argparse
import select
import fcntl
import atexit
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from typing import Any, Dict

# 首先加载环境变量
from dotenv import load_dotenv
load_dotenv()

import uvicorn
import anyio
from fastapi import FastAPI
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.requests import Request

from mcp.server.sse import SseServerTransport
from mcp.server.fastmcp import FastMCP

# 导入现有的MCP服务器和API模块
from mcp_server_weather.server import mcp

# 直接从环境变量中读取配置而不依赖导入的变量
HOST = os.environ.get("HOST", "127.0.0.1")
# 确保当PORT为空时使用默认值
port_value = os.environ.get("PORT", "")
PORT = int(port_value) if port_value.strip() else 8000

# 初始化日志
# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../logs")
os.makedirs(log_dir, exist_ok=True)

# 使用固定名称的滚动日志文件
log_file = os.path.join(log_dir, "sse_server.log")

# 创建一个滚动文件处理器，每个日志文件最大5MB，保留3个备份文件
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=5 * 1024 * 1024,  # 5MB
    backupCount=3,  
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# 创建格式化程序对象
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 创建logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)  # 只添加文件处理器


def create_sse_server(mcp: FastMCP):
    """创建一个Starlette应用，用于通过SSE提供MCP服务。

    Args:
        mcp: FastMCP实例

    Returns:
        配置好的Starlette应用
    """
    # 创建SSE传输处理器，指定消息端点
    logger.info("创建SSE传输处理器...")
    transport = SseServerTransport("/messages/")
    logger.info(f"SSE传输处理器创建完成: {transport}")

    # 定义SSE处理函数
    async def handle_sse(request: Request):
        """处理SSE连接请求。

        Args:
            request: Starlette请求对象
            
        Returns:
            None或错误响应
        """
        # 记录请求信息
        logger.info(f"收到SSE连接请求，请求路径: {request.url.path}")
        logger.info(f"SSE请求客户端信息: {request.client}")
        logger.info(f"SSE请求头: {request.headers}")
        
        try:
            logger.info("开始建立SSE连接...")
            async with transport.connect_sse(
                    request.scope,
                    request.receive,
                    request._send,  # noqa: SLF001
            ) as streams:
                logger.info("SSE连接已建立，开始处理MCP服务器...")
                try:
                    await mcp._mcp_server.run(
                        streams[0], 
                        streams[1], 
                        mcp._mcp_server.create_initialization_options()
                    )
                except anyio.BrokenResourceError:
                    logger.warning("客户端连接已断开")
                    # 返回空响应，不报错
                    return None
                except Exception as e:
                    logger.error(f"处理MCP请求时出错: {e}", exc_info=True)
                    # 不返回错误对象，因为在SSE上下文中无法正确处理
                    # 只记录错误并返回None
                    return None
        except Exception as e:
            logger.error(f"建立SSE连接时出错: {e}", exc_info=True)
            # 在SSE请求中不能返回字典作为响应
            # 必须返回一个响应对象或None
            from starlette.responses import JSONResponse
            return JSONResponse(
                status_code=500,
                content={"error": f"建立SSE连接时出错: {str(e)}"})
        return None

    # 这不是正确的方法，因为Mount需要一个完整的ASGI应用
    # 所以我们需要使用不同的方法
    # 创建一个自定义中间件来处理会话ID
    class SessionFormatMiddleware:
        """ASGI中间件，用于格式化会话ID"""
        def __init__(self, app):
            self.app = app
            
        async def __call__(self, scope, receive, send):
            if scope["type"] == "http" and "/messages/" in scope.get("path", ""):
                # 解析查询参数
                query_string = scope.get("query_string", b"").decode()
                query_params = {}
                for param in query_string.split("&"):
                    if "=" in param:
                        key, value = param.split("=", 1)
                        query_params[key] = value
                
                # 获取和处理会话ID
                session_id = query_params.get("session_id", "")
                
                # 如果会话ID中没有连字符，尝试添加连字符
                if session_id and "-" not in session_id and len(session_id) == 32:
                    formatted_id = session_id[:8] + "-" + session_id[8:12] + "-" + \
                                session_id[12:16] + "-" + session_id[16:20] + "-" + session_id[20:]
                    # 替换查询参数
                    query_params["session_id"] = formatted_id
                    # 重新构建查询字符串
                    new_query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
                    # 更新scope
                    scope["query_string"] = new_query_string.encode()
                    
                    logger.info(f"格式化会话ID从 {session_id} 到 {formatted_id}")
            
            # 继续处理请求
            await self.app(scope, receive, send)
        
    # 创建Starlette路由
    routes = [
        Route("/sse/", endpoint=handle_sse),
        Mount("/messages/", app=SessionFormatMiddleware(transport.handle_post_message)),
    ]

    # 返回配置好的Starlette应用
    return Starlette(routes=routes)

def main():
    """SSE服务器主函数，解析命令行参数并启动服务器。"""

    # 全局变量用于保存终端设置，便于在不同的退出路径中恢复
    global global_terminal_fd, global_terminal_settings
    global_terminal_fd = None
    global_terminal_settings = None
    terminal_restored = False  # 标记终端是否已经恢复

    # 创建终端恢复函数，便于在不同退出路径中调用
    def restore_terminal_settings(fd=None, old_settings=None):
        nonlocal terminal_restored
        if terminal_restored:
            return  # 如果已经恢复过则不再重复恢复
            
        if fd is None or old_settings is None:
            # 尝试使用全局变量
            if global_terminal_fd is not None and global_terminal_settings is not None:
                fd = global_terminal_fd
                old_settings = global_terminal_settings
            else:
                return
            
        try:
            logger.warning("恢复终端设置...")
            # 使用TCSANOW参数立即恢复而不是等待输出缓冲区清空
            termios.tcsetattr(fd, termios.TCSANOW, old_settings)
            # 强制输出一个新行到终端，来确保显示正常
            sys.stdout.write("\n")
            sys.stdout.flush()
            logger.info("终端设置恢复完成")
            terminal_restored = True  # 标记为已经恢复
        except Exception as e:
            logger.error(f"恢复终端设置失败: {e}")
            
    # 注册atexit处理器，确保在程序退出时一定会恢复终端设置
    atexit.register(restore_terminal_settings)

    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='运行天气MCP SSE服务器')
    parser.add_argument('--host', default=HOST, help='绑定的主机地址')
    parser.add_argument('--port', type=int, default=PORT, help='监听的端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()

    # 创建 FastAPI 应用
    app = FastAPI(title="天气MCP SSE服务器", debug=args.debug)
    
    # 挂载 SSE 服务器到 FastAPI 应用
    sse_app = create_sse_server(mcp)
    app.mount("/", sse_app)
    
    # 添加基本路由
    @app.get("/")
    async def read_root():
        """提供基本的API信息"""
        return {
            "service": "天气MCP SSE服务器",
            "version": "1.0.0",
            "endpoints": {
                "sse": "/sse/",
                "messages": "/messages/"
            }
        }

    # 强制使用127.0.0.1作为主机地址，无视命令行参数和环境变量
    host = "127.0.0.1"
    

    
    # 完全禁用uvicorn的控制台日志
    # 设置 uvicorn 相关的所有日志器
    uvicorn_loggers = ["uvicorn", "uvicorn.error", "uvicorn.access"]
    for logger_name in uvicorn_loggers:
        uvicorn_logger = logging.getLogger(logger_name)
        # 移除现有的所有处理器
        for handler in uvicorn_logger.handlers[:]:  # 使用副本进行循环以避免修改列表引起问题
            uvicorn_logger.removeHandler(handler)
        # 添加文件处理器
        uvicorn_logger.addHandler(file_handler)
        # 设置级别
        uvicorn_logger.setLevel(logging.INFO)
        # 确保不传播到父级日志器
        uvicorn_logger.propagate = False
    
    # 打印启动信息到日志文件
    logger.info(f"正在启动天气MCP SSE服务器，地址: {host}:{args.port}...")
    
    # 使用uvicorn运行应用，强制使用127.0.0.1
    try:
        logger.info(f"服务器日志设置完成，所有日志输出到文件: {log_file}")
        
        # 创建空日志配置
        log_config = {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "default": {
                    "()":
                    "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "use_colors": False,
                },
            },
            "handlers": {
                "null": {
                    "class": "logging.NullHandler",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["null"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"handlers": ["null"], "level": "INFO", "propagate": False},
                "uvicorn.access": {"handlers": ["null"], "level": "INFO", "propagate": False},
            },
        }
        
        # 创建一个滚动日志文件同时捕获标准输出和标准错误
        stdout_stderr_log = os.path.join(log_dir, "uvicorn_output.log")
        logger.info(f"重定向标准输出和标准错误到文件: {stdout_stderr_log} (当文件大小超过5MB时自动滚动)")
        
        # 保存原始的标准输出和标准错误
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        # 创建一个可滚动的文件对象
        class RotatingFile:
            def __init__(self, filename, max_bytes=5*1024*1024, backup_count=3):
                self.filename = filename
                self.max_bytes = max_bytes
                self.backup_count = backup_count
                self.file = open(filename, 'a', encoding='utf-8')
                self.file_size = os.path.getsize(filename) if os.path.exists(filename) else 0
                
            def write(self, data):
                data_len = len(data.encode('utf-8'))  # 用字节长度而非字符长度
                
                # 检查是否需要滚动
                if self.file_size + data_len > self.max_bytes:
                    self.do_rollover()
                    
                self.file.write(data)
                self.file.flush()  # 立即刷新
                self.file_size += data_len
                
            def do_rollover(self):
                """执行文件滚动"""
                self.file.close()
                
                # 删除旧的备份
                if self.backup_count > 0 and os.path.exists(f"{self.filename}.{self.backup_count}"):
                    os.remove(f"{self.filename}.{self.backup_count}")
                    
                # 重命名所有现有备份
                for i in range(self.backup_count-1, 0, -1):
                    if os.path.exists(f"{self.filename}.{i}"):
                        os.rename(f"{self.filename}.{i}", f"{self.filename}.{i+1}")
                        
                # 重命名当前文件
                if os.path.exists(self.filename):
                    os.rename(self.filename, f"{self.filename}.1")
                    
                # 创建新文件
                self.file = open(self.filename, 'w', encoding='utf-8')
                self.file_size = 0
                
            def flush(self):
                self.file.flush()
                
            def close(self):
                try:
                    self.file.close()
                except:
                    pass
                    
        # 创建可滚动的文件对象
        rotating_file = RotatingFile(stdout_stderr_log, max_bytes=5*1024*1024, backup_count=3)
        
        # 同时重定向标准输出和标准错误到滚动文件
        sys.stdout = rotating_file
        sys.stderr = rotating_file
        
        # 运行状态监控
        running = True
        exit_requested = False
        
        # 创建一个单独的线程来监控键盘输入和强制退出
        def monitor_thread():
            nonlocal running, exit_requested
            logger.info("按q键或Ctrl+C可强制退出服务器")
            
            # 设置标准输入的非阻塞模式
            try:
                # 保存原始终端设置
                fd = sys.stdin.fileno()
                old_settings = termios.tcgetattr(fd)
                
                # 将终端设置保存到全局变量，便于在不同路径中访问
                global global_terminal_fd, global_terminal_settings
                global_terminal_fd = fd
                global_terminal_settings = old_settings
                
                logger.info(f"保存原始终端设置，准备在退出时恢复")
                
                # 设置终端为原始模式
                tty.setraw(fd)
                
                # 设置非阻塞模式
                fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)
                
                while running:
                    # 检查是否有输入
                    r, _, _ = select.select([sys.stdin], [], [], 0.5)
                    if r:
                        c = sys.stdin.read(1)
                        # q键或Ctrl+C(ASCII 3)将强制退出
                        if c in ('q', '\x03'):
                            if exit_requested:
                                logger.warning("第二次退出请求接收到，立即强制终止进程!")
                                # 先恢复终端设置
                                restore_terminal_settings(fd, old_settings)
                                    
                                # 先尝试SIGTERM，如果可能的话
                                os.kill(os.getpid(), signal.SIGTERM)
                                # 短暂停顿
                                time.sleep(0.3)
                                # 强制终止进程
                                os.kill(os.getpid(), signal.SIGKILL)
                            else:
                                exit_requested = True
                                logger.warning("退出请求接收到，正在关闭服务器...")
                                logger.warning("再次按q键或Ctrl+C立即强制退出")
                                
                                # 设置定时器在一段时间后强制退出
                                def force_exit():
                                    if running:  # 只在仍然运行时强制退出
                                        # 先恢复终端设置
                                        restore_terminal_settings(fd, old_settings)
                                        
                                        logger.warning("服务器在规定时间内未能正常关闭，强制终止！")
                                        # 先尝试SIGTERM，给进程一个清理的机会
                                        os.kill(os.getpid(), signal.SIGTERM)
                                        # 等待短暂时间
                                        time.sleep(0.5)
                                        # 如果还在运行，则使用SIGKILL
                                        os.kill(os.getpid(), signal.SIGKILL)
                                
                                # 设置强制退出定时器（2秒后）
                                force_timer = threading.Timer(2.0, force_exit)
                                force_timer.daemon = True
                                force_timer.start()
                                
                                # 触发一个中断信号给自己
                                os.kill(os.getpid(), signal.SIGINT)
            except Exception as e:
                logger.error(f"监控线程出错: {e}")
            finally:
                # 恢复终端设置 - 在finally块中约定一定会执行
                restore_terminal_settings(fd, old_settings)
                # 在线程退出时再输出一个新行，确保终端展示正常
                try:
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                except:
                    pass
        
        # 启动监控线程
        monitor = threading.Thread(target=monitor_thread)
        monitor.daemon = True  # 这样主线程退出时监控线程也会退出
        monitor.start()
        
        # 运行uvicorn
        uvicorn.run(
            app, 
            host=host, 
            port=args.port,
            timeout_keep_alive=5,  # 减少保持连接的超时时间
            log_level="info",
            access_log=False,      # 关闭访问日志以减少关闭时的操作
            log_config=log_config  # 使用自定义的空日志配置
        )
    except KeyboardInterrupt:
        # 这是备用处理，以防uvicorn自己的信号处理不起作用
        logger.info("接收到键盘中断，正在退出...")
        # 在KeyboardInterrupt处理中恢复终端设置
        restore_terminal_settings()
    finally:
        # 标记监控线程也需要退出
        running = False
        
        # 恢复标准输出和标准错误
        if 'original_stdout' in locals() and 'original_stderr' in locals():
            try:
                sys.stdout = original_stdout
                sys.stderr = original_stderr
            except Exception as e:
                logger.error(f"恢复标准输出失败: {e}")
        
        # 再次确保终端设置被恢复
        restore_terminal_settings()
        
        # 强制输出一个新行到终端，确保显示正常
        try:
            print("\n服务器已安全退出")
            sys.stdout.flush()
        except:
            pass

if __name__ == "__main__":
    main()
