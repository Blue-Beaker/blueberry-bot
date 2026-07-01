from __future__ import annotations

import base64
from enum import Enum
from typing import override
from urllib.parse import unquote

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    from pathlib import Path
    import sys
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.gd.utils import safeBool, safeInt
else:
    from .utils import safeBool, safeInt

class Length(Enum):
    TINY = 0
    SHORT = 1
    MEDIUM = 2
    LONG = 3
    XL = 4
    PLAT = 5
    
    def get_name(self):
        if self.value<Length.XL.value:
            return self.name.capitalize()
        elif self==Length.PLAT:
            return "Plat."
        else:
            return self.name
        
    def is_plat(self):
        return self==Length.PLAT

class Difficulty(Enum):
    NA = 0
    EASY = 1
    NORMAL = 2
    HARD = 3
    HARDER = 4
    INSANE = 5
    EASY_DEMON = 6
    MEDIUM_DEMON = 7
    HARD_DEMON = 8
    INSANE_DEMON = 9
    EXTREME_DEMON = 10
    AUTO = 11
    ANY_DEMON = 12
    
    def is_demon(self):
        return Difficulty.EASY_DEMON.value<=self.value<=Difficulty.EXTREME_DEMON.value or self==Difficulty.ANY_DEMON


class BaseLevel:
    id: int
    name: str
    creator: str

    def __init__(self) -> None:
        pass

    def load(self, data: dict[str, str]) -> BaseLevel:
        self.id = int(data.get('1', '-1'))
        self.name = data.get('2', '')
        self.creator = data.get('50', '')
        return self

    def __repr__(self) -> str:
        return f"{self.name} by {self.creator}, id={self.id}"


class LevelList(BaseLevel):
    levels: list[int]

    def __init__(self) -> None:
        self.levels = []

    @override
    def load(self, data: dict[str, str]) -> LevelList:
        super().load(data)
        list_levels = data.get('51', '')
        self.levels = [int(l) for l in list_levels.split(',') if l]
        return self

    def __repr__(self) -> str:
        return f"{self.name} by {self.creator}, id={self.id}, levels={self.levels}"

class SearchStatus(Enum):
    SUCCESS=""
    PARSE_FAILED="解析失败"
    EMPTY_RESULTS="无结果"
    USER_NOT_FOUND="未找到用户"
    NO_USER_ARG="未提供用户名/ID"

class PageInfo:
    status: SearchStatus
    total: int=0
    offset: int=0
    amount: int=0

    def __init__(self) -> None:
        self.status=SearchStatus.SUCCESS
        self.total = 0
        self.offset = 0
        self.amount = 10
        
    def success(self):
        return self.status==SearchStatus.SUCCESS or self.status==SearchStatus.EMPTY_RESULTS
    
    def setStatus(self,status:SearchStatus):
        self.status=status
        return self

    def parse(self, line: str) -> PageInfo:
        spl = line.split(":")
        try:
            if spl.__len__() >= 3:
                self.total = int(spl[0])
                self.offset = int(spl[1])
                self.amount = int(spl[2])
        except Exception:
            pass
        return self


class Level(BaseLevel):
    creator_id: int

    def __init__(self) -> None:
        # === 常用字段 ===
        self.stars: int = 0              #: 18 — 星数
        self.difficulty: int = 0         #: 9 — 难度分子。0=未评级，10=easy，20=normal，30=hard，40=harder，50=insane
        self.featured: int = 0           #: 19 — 推荐分数。0=未推荐，正数越高在推荐列表越靠前
        self.epic: int = 0               #: 42 — 史诗评级。0=无，1=epic，2=legendary，3=mythic
        self.length: int = 0             #: 15 — 关卡长度。0=tiny，1=short，2=medium，3=long，4=XL，5=platformer
        self.demon: bool = False         #: 17 — 是否为恶魔难度
        self.auto: bool = False          #: 25 — 是否为自动关卡
        self.creator_id: int = 0         #: 6 — 作者 Player ID
        self.downloads: int = 0          #: 10 — 下载次数
        self.likes: int = 0              #: 14 — 点赞数 - 点踩数
        self.songID: int = 0             #: 12/35 — 歌曲 ID。优先取 12(official)，否则取 35(custom)
        self.coins: int = 0              #: 37 — 用户硬币数量
        self.verifiedCoins: bool = False  #: 38 — 用户硬币是否已验证(银色)

        # === 元数据/存档字段 ===
        self.description: str = ""                    #: 3 — 关卡描述，Base64 编码
        self.level_string: str | None = None           #: 4* — 关卡数据字符串，仅从 downloadGJLevel22 返回
        self.version: int = 0                          #: 5 — 关卡发布版本号
        self.difficulty_denominator: int = 0           #: 8 — 难度分母。返回 0 表示 N/A，返回 10 表示已分配难度
        self.set_completes: int = 0                    #: 11 — 完成人数，2.1 更新中移除
        self.game_version: int = 0                     #: 13 — 上传时的 GD 版本号
        self.dislikes: int = 0                         #: 16 — 点踩数
        self.password: str | None = None               #: 27* — 复制关密码，XOR 加密（密钥 26364）
        self.upload_date: str | None = None            #: 28* — 上传日期（近似）
        self.update_date: str | None = None            #: 29* — 更新日期（近似）
        self.copied_id: int = 0                        #: 30 — 原关卡 ID（若为复制关）
        self.two_player: bool = False                  #: 31 — 是否启用双人模式
        self.extra_string: str = ""                    #: 36 — 上传时传入的额外字符串，用途未知
        self.stars_requested: int = 0                  #: 39 — 作者请求的星数
        self.low_detail_mode: bool | None = None       #: 40* — 是否启用低细节模式
        self.daily_number: int | None = None           #: 41* — 每日/每周编号
        self.demon_difficulty: int = 0                 #: 43 — 恶魔难度细分
        self.is_gauntlet: bool = False                 #: 44 — 是否属于关卡包
        self.objects: int = 0                          #: 45 — 物体数量，上限 65535
        self.editor_time: int = 0                      #: 46 — 当前副本的编辑用时（秒），上限 24-bit
        self.editor_time_copies: int = 0               #: 47 — 累计编辑用时（秒），上限 24-bit
        self.song_ids: str | None = None               #: 52* — 所有歌曲 ID，逗号分隔
        self.sfx_ids: str | None = None                #: 53* — 所有 SFX ID，逗号分隔
        self.unknown: int = 0                          #: 54 — 未知值
        self.verification_time: int | None = None      #: 57* — 验证用时（帧，假设 240 FPS），上限 24-bit

        # === 未使用字段 (文档标注) ===
        self.record_string: str = ""     #: 26 — 记录字符串(未使用)
        self.settings_string: str = ""   #: 48 — 设置字符串(未使用)

    def get_description(self) -> str:
        """解码并返回关卡描述（Base64 url safe → 明文）。"""
        if not self.description:
            return ""
        try:
            padded = self.description.replace("-", "+").replace("_", "/")
            padded += "=" * (-len(padded) % 4)
            return base64.b64decode(padded).decode("utf-8", errors="replace")
        except Exception:
            return ""

    def is_plat(self) -> bool:
        return self.length == Length.PLAT.value
    def get_length(self):
        return Length(self.length)
    def get_difficulty(self) -> Difficulty:
        if self.auto:
            return Difficulty.AUTO
        if not self.demon:
            return Difficulty(self.difficulty)
        else:
            return Difficulty(self.difficulty + 5)

    def repr_difficulty(self) -> str:
        diffs = ['NA', 'Easy', 'Normal', 'Hard', 'Harder', 'Insane',
                 'EZD', 'MED', 'HDD', 'INSD', 'EXD', 'Auto']
        diffstr = diffs[self.get_difficulty().value]
        if self.demon and self.is_plat():
            diffstr = diffstr.removesuffix('D') + 'P'
        return f"{diffstr} {self.stars} {'⭐' if not self.is_plat() else '🌙'}"

    @override
    def load(self, data: dict[str, str]) -> Level:
        super().load(data)
        self.stars = safeInt(data.get('18'), 0)
        self.difficulty = safeInt(data.get('9'), 0) // 10
        self.length = safeInt(data.get('15'), 0)
        self.demon = safeBool(data.get('17'))
        self.auto = safeBool(data.get('25'))
        self.creator_id = safeInt(data.get('6'))
        self.downloads = safeInt(data.get('10'), 0)
        self.likes = safeInt(data.get('14'), 0)
        self.songID = safeInt(data.get('12'), None) or safeInt(data.get('35'), 0)
        self.coins = safeInt(data.get('37'), 0)
        self.verifiedCoins = safeBool(data.get('38'))
        self.featured = safeInt(data.get('19'), 0)
        self.epic = safeInt(data.get('42'), 0)

        # === 元数据字段加载 ===
        self.description = data.get('3', '')
        raw_level_string = data.get('4')
        if raw_level_string:
            self.level_string = raw_level_string
        self.version = safeInt(data.get('5'), 0)
        self.difficulty_denominator = safeInt(data.get('8'), 0)
        self.set_completes = safeInt(data.get('11'), 0)
        self.game_version = safeInt(data.get('13'), 0)
        self.dislikes = safeInt(data.get('16'), 0)
        raw_password = data.get('27')
        if raw_password:
            self.password = raw_password
        raw_upload = data.get('28')
        if raw_upload:
            self.upload_date = raw_upload
        raw_update = data.get('29')
        if raw_update:
            self.update_date = raw_update
        self.copied_id = safeInt(data.get('30'), 0)
        self.two_player = safeBool(data.get('31'))
        self.extra_string = data.get('36', '')
        self.stars_requested = safeInt(data.get('39'), 0)
        raw_ldm = data.get('40')
        if raw_ldm is not None:
            self.low_detail_mode = safeBool(raw_ldm)
        raw_daily = data.get('41')
        if raw_daily is not None:
            self.daily_number = safeInt(raw_daily)
        self.demon_difficulty = safeInt(data.get('43'), 0)
        self.is_gauntlet = safeBool(data.get('44'))
        self.objects = safeInt(data.get('45'), 0)
        self.editor_time = safeInt(data.get('46'), 0)
        self.editor_time_copies = safeInt(data.get('47'), 0)
        raw_song_ids = data.get('52')
        if raw_song_ids:
            self.song_ids = raw_song_ids
        raw_sfx_ids = data.get('53')
        if raw_sfx_ids:
            self.sfx_ids = raw_sfx_ids
        self.unknown = safeInt(data.get('54'), 0)
        raw_verify = data.get('57')
        if raw_verify is not None:
            self.verification_time = safeInt(raw_verify)

        # === 未使用字段 (文档标注) ===
        self.record_string = data.get('26', '')
        self.settings_string = data.get('48', '')

        return self

    def __repr__(self) -> str:
        return f"{self.name} by {self.creator}, id={self.id}, {self.repr_difficulty()}"


class PlayerIcons:
    color: int
    color2: int
    icon_type: int
    acc_icon: int
    acc_ship: int
    acc_ball: int
    acc_ufo: int
    acc_wave: int
    acc_robot: int
    glow_on: int
    glow_color: int
    acc_spider: int
    acc_swing: int
    acc_jetpack: int

    def __init__(self) -> None:
        self.color = 0
        self.color2 = 0
        self.icon_type = 0
        self.acc_icon = 0
        self.acc_ship = 0
        self.acc_ball = 0
        self.acc_ufo = 0
        self.acc_wave = 0
        self.acc_robot = 0
        self.glow_on = 0
        self.glow_color = -1
        self.acc_spider = 0
        self.acc_swing = 0
        self.acc_jetpack = 0

    def __repr__(self) -> str:
        return f"Icon: {self.__dict__}"

    def get_icon_for_type(self, icon_type: str) -> int | None:
        field_name = "acc_icon" if icon_type == "cube" else "acc_" + icon_type
        icon_id = getattr(self, field_name, None)
        return icon_id if isinstance(icon_id, int) else None

    def get_icon_type(self) -> str:
        icon_types = ["cube", "ship", "ball", "ufo", "wave", "robot", "spider", "swing", "jetpack"]
        return icon_types[max(min(self.icon_type, len(icon_types) - 1), 0)]


class PlayerDemonLevels:
    ezd: int = -1
    med: int = -1
    hdd: int = -1
    insd: int = -1
    exd: int = -1
    weekly: int = -1
    gauntlet: int = -1

    def load(self, data: str) -> PlayerDemonLevels:
        spl = data.split(",")
        if spl.__len__() >= 5:
            self.ezd = safeInt(spl[0])
            self.med = safeInt(spl[1])
            self.hdd = safeInt(spl[2])
            self.insd = safeInt(spl[3])
            self.exd = safeInt(spl[4])
        if spl.__len__() >= 12:
            self.weekly = safeInt(spl[10])
            self.gauntlet = safeInt(spl[11])
        return self

    def sum(self) -> int:
        return self.ezd + self.med + self.hdd + self.insd + self.exd

    def __repr__(self) -> str:
        return f"Demons: {self.__dict__}"


class PlayerLevels:
    auto: int = -1
    easy: int = -1
    normal: int = -1
    hard: int = -1
    harder: int = -1
    insane: int = -1
    daily: int = -1
    gauntlet: int = -1

    def load(self, data: str) -> PlayerLevels:
        spl = data.split(",")
        if spl.__len__() >= 7:
            self.auto = safeInt(spl[0])
            self.easy = safeInt(spl[1])
            self.normal = safeInt(spl[2])
            self.hard = safeInt(spl[3])
            self.harder = safeInt(spl[4])
            self.insane = safeInt(spl[5])
            self.daily = safeInt(spl[6])
            self.gauntlet = safeInt(spl[7]) if spl.__len__() > 7 else -1
        return self

    def sum(self) -> int:
        return self.auto + self.easy + self.normal + self.hard + self.harder + self.insane

    def __repr__(self) -> str:
        return f"Levels: {self.__dict__}"


class PlayerInfo:
    user_name: str
    user_id: int
    stars: int
    moons: int
    demons: int
    diamonds: int
    mod_level: int
    global_rank: int
    creator_points: int
    secret_coins: int
    account_id: int
    user_coins: int
    icon: PlayerIcons
    classic_levels: PlayerLevels
    plat_levels: PlayerLevels
    classic_demons: PlayerDemonLevels
    plat_demons: PlayerDemonLevels

    def __init__(self) -> None:
        self.user_name = ""
        self.user_id = 0
        self.stars = 0
        self.moons = 0
        self.demons = 0
        self.diamonds = 0
        self.mod_level = 0
        self.global_rank = -1
        self.creator_points = 0
        self.secret_coins = 0
        self.account_id = 0
        self.user_coins = 0
        self.icon = PlayerIcons()
        self.classic_levels = PlayerLevels()
        self.plat_levels = PlayerLevels()
        self.classic_demons = PlayerDemonLevels()
        self.plat_demons = PlayerDemonLevels()

    def load(self, data: dict[str, str]) -> PlayerInfo:
        self.user_name = data.get("1", self.user_name)
        self.user_id = safeInt(data.get("2"), self.user_id)
        self.stars = safeInt(data.get("3"), self.stars)
        self.demons = safeInt(data.get("4"), self.demons)
        self.creator_points = safeInt(data.get("8"), self.creator_points)
        self.secret_coins = safeInt(data.get("13"), self.secret_coins)
        self.account_id = safeInt(data.get("16"), self.account_id)
        self.user_coins = safeInt(data.get("17"), self.user_coins)
        self.global_rank = safeInt(data.get("30"), self.global_rank)
        self.diamonds = safeInt(data.get("46"), self.diamonds)
        self.mod_level = safeInt(data.get("49"), self.mod_level)
        self.moons = safeInt(data.get("52"), self.moons)

        icon = self.icon
        icon.color = safeInt(data.get("10"), icon.color)
        icon.color2 = safeInt(data.get("11"), icon.color2)
        icon.icon_type = safeInt(data.get("14"), icon.icon_type)
        icon.acc_icon = safeInt(data.get("21"), icon.acc_icon)
        icon.acc_ship = safeInt(data.get("22"), icon.acc_ship)
        icon.acc_ball = safeInt(data.get("23"), icon.acc_ball)
        icon.acc_ufo = safeInt(data.get("24"), icon.acc_ufo)
        icon.acc_wave = safeInt(data.get("25"), icon.acc_wave)
        icon.acc_robot = safeInt(data.get("26"), icon.acc_robot)
        icon.glow_on = safeInt(data.get("28"), icon.glow_on)
        icon.acc_spider = safeInt(data.get("43"), icon.acc_spider)
        icon.glow_color = safeInt(data.get("51"), icon.glow_color)
        icon.acc_swing = safeInt(data.get("53"), icon.acc_swing)
        icon.acc_jetpack = safeInt(data.get("54"), icon.acc_jetpack)

        if not icon.glow_on:
            icon.glow_color = -1

        classic_raw = data.get("56")
        if classic_raw:
            self.classic_levels = PlayerLevels().load(classic_raw)

        plat_raw = data.get("57")
        if plat_raw:
            self.plat_levels = PlayerLevels().load(plat_raw)

        demons_raw = data.get("55")
        if demons_raw:
            self.classic_demons = PlayerDemonLevels().load(demons_raw)
            spl = demons_raw.split(",")
            if spl.__len__() >= 10:
                plat_demons_data = ",".join(spl[5:10])
                self.plat_demons = PlayerDemonLevels().load(plat_demons_data)

        return self

    def __repr__(self) -> str:
        return f"{self.user_name}: {self.__dict__}"


class Song:
    id: int
    name: str
    artistID: int
    artistName: str
    size: float
    link: str

    def __init__(self) -> None:
        pass

    def load(self, data: dict[str, str]) -> Song:
        self.id = int(data.get('1', '-1'))
        self.name = data.get('2', '')
        self.artistID = int(data.get('3', '-1'))
        self.artistName = data.get('4', '')
        self.size = float(data.get('5', '-1'))
        self.link = unquote(data.get('10', ''))
        return self

    def __repr__(self) -> str:
        return f"{self.name} by {self.artistName}, id={self.id}, link={self.link}"


if __name__ == "__main__":
    print(list(Length))
    print(list(Difficulty))

    # 快速验证各模型类
    l = Level().load({"1": "12345", "2": "TestLevel", "50": "Creator",
                       "18": "10", "9": "50", "15": "4"})
    print(l)
    print(f"  description: {l.get_description()}")
    print(f"  is_plat: {l.is_plat()}")
    print(f"  difficulty: {l.get_difficulty()}")

    s = Song().load({"1": "803223", "2": "Test Song", "3": "42",
                      "4": "Artist", "5": "3.5",
                      "10": "http%3A%2F%2Fexample.com%2Fsong.mp3"})
    print(s)

    info = PlayerInfo().load({"1": "TestPlayer", "2": "100", "3": "500",
                               "4": "50", "55": "10,8,5,3,1,,,,,,"})
    print(info)
