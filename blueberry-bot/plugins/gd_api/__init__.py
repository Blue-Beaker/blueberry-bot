import asyncio
import threading
from pydantic import BaseModel
from nonebot import logger, get_driver, get_plugin_config

class Config(BaseModel):
    gdapi_warn_run_async:bool=False
    
try:
    plugin_config=get_plugin_config(Config)
except:
    plugin_config=Config()

def run_async(coro):
    """在同步函数中运行 async 函数。

    如果当前线程没有运行中的事件循环，用 asyncio.run() 直接执行。
    如果已有运行中的事件循环，在另一个线程中用新事件循环执行并等待结果。
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # 已有运行中的事件循环 — 说明调用方在 async 上下文中调用了同步兼容函数
    if plugin_config.gdapi_warn_run_async:
        import traceback
        logger.warning(
            "检测到运行中的事件循环，不应使用同步兼容函数。"
            "请改用对应的 _async 版本并 await。\n"
            + "".join(traceback.format_stack()[:-1])
        )
    result_container: list = []
    exception_container: list[BaseException] = []
    def _target():
        try:
            result_container.append(asyncio.run(coro))
        except BaseException as e:
            exception_container.append(e)
    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join()
    if exception_container:
        raise exception_container[0]
    return result_container[0]

try:
    driver = get_driver()

    @driver.on_shutdown
    async def _close_http_clients():
        from .gd import close_client as close_gd_client
        await close_gd_client()
except:
    pass


from . import gd
from . import pemonlist
from . import thumbs