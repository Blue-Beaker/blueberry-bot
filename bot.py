import nonebot
from nonebot.adapters.minecraft import Adapter as MINECRAFTAdapter

from nonebot.adapters.discord import Adapter as DISCORDAdapter

from nonebot.adapters.onebot.v11 import Adapter as ONEBOT_V11Adapter



nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(MINECRAFTAdapter)

driver.register_adapter(DISCORDAdapter)

driver.register_adapter(ONEBOT_V11Adapter)


nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()