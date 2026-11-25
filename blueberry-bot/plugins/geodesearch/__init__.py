try:
    from . import geodesearch  # noqa: F401
except (ValueError, RuntimeError):
    # 未调用 nonebot.init() 时（如单元测试）跳过命令注册，
    # 避免 bbot_api 依赖 get_driver() 导致整个包无法导入
    from nonebot import logger

    logger.debug("geodesearch: NoneBot 未初始化，跳过命令注册")