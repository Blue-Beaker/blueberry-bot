import nonebot
from nonebot.adapters.minecraft import Adapter as MINECRAFTAdapter

from nonebot.adapters.discord import Adapter as DISCORDAdapter



nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(MINECRAFTAdapter)

driver.register_adapter(DISCORDAdapter)


nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()