# main.py: 主程序入口
import os, sys, asyncio, signal
from app.logger import logger
from app.config import Config
from utils.boot import task, shutdown_handler
from rich import print
from rich.console import Console

console = Console()

asciiart = r"""

 ____    ____   ____  ____               ___       ______       ___     _________  
|_   \  /   _| |_  _||_  _|            .'   `.    |_   _ \    .'   `.  |  _   _  | 
  |   \/   |     \ \  / /             /  .-.  \     | |_) |  /  .-.  \ |_/ | | \_| 
  | |\  /| |      \ \/ /              | |   | |     |  __'.  | |   | |     | |     
 _| |_\/_| |_     _|  |_     _______  \  `-'  \_   _| |__) | \  `-'  /    _| |_    
|_____||_____|   |______|   |_______|  `.___.\__| |_______/   `.___.'    |_____|  


"""

rainbow_colors = ["red", "orange", "yellow", "green", "blue", "indigo", "violet"]


    
if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')  # 清空终端
    sys.stdout.reconfigure(encoding='utf-8')  # 设置编码为 utf-8
    for i, line in enumerate(asciiart.splitlines()):
        print(f"[{rainbow_colors[i % len(rainbow_colors)]}]{line}[/]")
    print("⭐️开源地址: https://github.com/syuchua/MY_QBOT\n")

    config = Config.get_instance()

    # 注册信号处理程序
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    try:
        asyncio.run(task())
    except Exception as e:
        logger.error(f"Main loop encountered an error: {e}")
    finally:
        logger.info("程序退出")
