# main.py: 主程序入口
import os, sys, asyncio, signal
from app.logger import logger
from utils.boot import task, shutdown_handler
from rich import print
from rich.console import Console

console = Console()

asciiart = r"""

   ____    ______              _              
  / __ \  / ____/__  __ _____ (_)____   ____ _
 / / / / / /_   / / / // ___// // __ \ / __ `/
/ /_/ / / __/  / /_/ // /   / // / / // /_/ / 
\___\_\/_/     \__,_//_/   /_//_/ /_/ \__,_/  

                                                                                                                                                                    
"""

rainbow_colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]


    
if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')  # 清空终端
    #sys.stdout.reconfigure(encoding='utf-8')  # 设置编码为 utf-8
    for i, line in enumerate(asciiart.splitlines()):
        print(f"[{rainbow_colors[i % len(rainbow_colors)]}]{line}[/]")
    print("⭐️开源地址: https://github.com/syuchua/QFurina\n")
    print("📖文档地址：https://qfurina.yuchu.me\n")

    # 注册信号处理程序
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    try:
        asyncio.run(task())
    except Exception as e:
        logger.error(f"Main loop encountered an error: {e}")
    finally:
        logger.info("程序退出")