from __future__ import annotations

from enum import Enum

# 直接运行时将 blueberry-bot/ 加入 sys.path，使 plugins 包可导入
if __name__ == "__main__" and __package__ is None:
    from pathlib import Path
    import sys
    _root = Path(__file__).resolve().parents[3]  # blueberry-bot/
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from plugins.gd_api.gd.models import Difficulty, Length
else:
    from .models import Difficulty, Length

class ListSearchType(Enum):
    SEARCH = 0
    DOWNLOADS = 1
    LIKES = 2
    TRENDING = 3
    RECENT = 4
    FROM_USER = 5
    LISTS_BUTTON = 6
    MAGIC = 7  # (returns the same levels as most liked)
    AWARDED = 11
    FOLLOWED = 12
    FRIENDS = 13
    SENT = 27


class LevelSearchType(Enum):
    SEARCH = 0
    DOWNLOADS = 1
    LIKES = 2
    TRENDING = 3
    RECENT = 4
    FROM_USER = 5
    FEATURED = 6
    MAGIC = 7
    MOD_SENT = 8
    LIST_OF_LEVELS = 10
    AWARDED = 11
    FOLLOWED = 12
    FRIENDS = 13
    WORLD_LIKED = 15
    HALL_OF_FAME = 16
    WORLD_FEATURED = 17
    DAILY = 21
    WEEKLY = 22
    LEVEL_FROM_LIST = 25
    SENT = 27


def _diff_to_raw(d: Difficulty) -> int:
    """Difficulty → diff raw value。"""
    if d == Difficulty.NA:
        return -1
    if d == Difficulty.AUTO:
        return -3
    if d == Difficulty.ANY_DEMON:
        return -2
    if Difficulty.EASY.value <= d.value <= Difficulty.INSANE.value:
        return d.value
    if d.value >= Difficulty.EASY_DEMON.value:
        return -2
    return -1


def _raw_to_difficulty(v: int) -> Difficulty:
    """diff raw value → Difficulty。"""
    if v == -3:
        return Difficulty.AUTO
    if v == -2:
        return Difficulty.ANY_DEMON
    if v == -1:
        return Difficulty.NA
    if 1 <= v <= 5:
        return Difficulty(v)
    return Difficulty.NA


def _demon_to_raw(d: Difficulty) -> int | None:
    """Difficulty → demonFilter raw value。"""
    mapping = {
        Difficulty.EASY_DEMON: 1,
        Difficulty.MEDIUM_DEMON: 2,
        Difficulty.HARD_DEMON: 3,
        Difficulty.INSANE_DEMON: 4,
        Difficulty.EXTREME_DEMON: 5,
    }
    return mapping.get(d)


def _raw_to_demon(v: int) -> Difficulty | None:
    """demonFilter raw value → Difficulty。"""
    mapping = {1: Difficulty.EASY_DEMON, 2: Difficulty.MEDIUM_DEMON,
               3: Difficulty.HARD_DEMON, 4: Difficulty.INSANE_DEMON,
               5: Difficulty.EXTREME_DEMON}
    return mapping.get(v)


class LevelSearchArgs:
    """链式调用的关卡搜索参数构造器。

    self 上存储的是可以直接发往端点的原始值：
    - int（0/1 的用 bool）直接对应端点参数
    - str/None 直接对应端点参数

    通过 setter/getter 方法提供抽象层转换。
    """

    def __init__(self) -> None:
        # === 原始值字段（直接对应端点参数） ===
        self.type: int = LevelSearchType.SEARCH.value  # 搜索类型 raw int
        self.str: str | None = None                    # 搜索关键词
        self.page: int = 0                             # 页码
        self.gauntlet: int | None = None               # 关卡包 ID
        self.diff: str | None = None                   # 难度过滤 raw (逗号分隔)
        self.demonFilter: int | None = None            # 恶魔难度细分
        self.len: str | None = None                    # 长度过滤 raw (逗号分隔)
        self.song: int | None = None                   # 歌曲 ID
        self.customSong: bool = False                  # 是否自定义歌曲

        # 布尔开关 (端点用 "1"/"0", self 存 bool)
        self.featured: bool = False
        self.original: bool = False
        self.twoPlayer: bool = False
        self.coins: bool = False
        self.epic: bool = False
        self.legendary: bool = False
        self.mythic: bool = False
        self.noStar: bool = False
        self.star: bool = False
        self.uncompleted: bool = False
        self.onlyCompleted: bool = False

        # === 以下字段不在 self 上存储，仅通过 setter 设置原始值 ===
        self._completedLevels: str | None = None

    # --- 抽象 setter / getter（成对排列） ---

    def setSearchType(self, v: LevelSearchType) -> LevelSearchArgs:
        self.type = v.value
        return self

    def getSearchType(self) -> LevelSearchType | None:
        if self.type is None:
            return None
        try:
            return LevelSearchType(self.type)
        except ValueError:
            return None

    def setSearch(self, v: str) -> LevelSearchArgs:
        self.str = v
        return self
    
    def getSearch(self) -> str|None:
        return self.str

    def setDifficulty(self, v: list[Difficulty]) -> LevelSearchArgs:
        """设置难度过滤。空列表清除过滤。

        当传入的难度中包含 Demon 时，自动将 diff 设为 ANY_DEMON(-2)，
        并从中提取首个恶魔难度设置 demonFilter。
        """
        if not v:
            self.diff = None
            self.demonFilter = None
            return self

        # 分离恶魔和非恶魔难度
        demons = [d for d in v if d.is_demon()]
        nondemons = [d for d in v if not d.is_demon()]
        
        if demons and nondemons:
            raise ValueError(f"Cannot mix demon and non-demon difficulties: {v}")
        
        if demons.__len__()>1:
            raise ValueError(f"Cannot select multiple demon difficulties: {v}")

        if demons:
            # 有具体恶魔难度 → diff 设为 ANY_DEMON，取首个设 demonFilter
            self.diff = str(_diff_to_raw(Difficulty.ANY_DEMON))
            
            selected_demon=demons[0]
            if selected_demon!=Difficulty.ANY_DEMON:
                self.demonFilter = _demon_to_raw(selected_demon)
        else:
            # 无恶魔难度 → 按正常逻辑
            self.diff = ",".join(str(_diff_to_raw(d)) for d in nondemons)
            self.demonFilter = None
        return self

    def getDifficulty(self) -> list[Difficulty]:
        if not self.diff:
            return []
        return [_raw_to_difficulty(int(x)) for x in self.diff.split(",") if x]

    def setDemonDifficulty(self, v: Difficulty) -> LevelSearchArgs:
        """设置恶魔难度细分。传入非恶魔 Difficulty 则清除。"""
        raw = _demon_to_raw(v)
        self.demonFilter = raw
        return self

    def getDemonDifficulty(self) -> Difficulty | None:
        if self.demonFilter is None:
            return None
        return _raw_to_demon(self.demonFilter)

    def setLength(self, v: list[Length]) -> LevelSearchArgs:
        """设置长度过滤。空列表清除过滤。"""
        if not v:
            self.len = None
        else:
            self.len = ",".join(str(l.value) for l in v)
        return self

    def getLength(self) -> list[Length]:
        if not self.len:
            return []
        return [Length(int(x)) for x in self.len.split(",") if x]

    def setCompletedLevels(self, v: list[int]) -> LevelSearchArgs:
        """设置已完成关卡列表（配合 uncompleted/onlyCompleted 使用）。"""
        if not v:
            self._completedLevels = None
        else:
            self._completedLevels = "(" + ",".join(str(i) for i in v) + ")"
        return self

    def getCompletedLevels(self) -> list[int]:
        if not self._completedLevels:
            return []
        return [int(x) for x in self._completedLevels.strip("()").split(",") if x]

    def setPage(self, v: int) -> LevelSearchArgs:
        self.page = v
        return self

    def getPage(self) -> int:
        return self.page

    def setGauntlet(self, v: int) -> LevelSearchArgs:
        self.gauntlet = v
        return self

    def getGauntlet(self) -> int | None:
        return self.gauntlet

    def setSong(self, v: int, custom: bool = False) -> LevelSearchArgs:
        """设置歌曲。custom=True 时同时启用 customSong。"""
        self.song = v
        self.customSong = custom
        return self

    def getSong(self) -> int | None:
        return self.song

    def isCustomSong(self) -> bool:
        return self.customSong

    # --- 布尔开关 setter（全部返回 self 支持链式调用） ---

    def setFeatured(self, v: bool = True) -> LevelSearchArgs:
        self.featured = v
        return self

    def isFeatured(self) -> bool:
        return self.featured

    def setOriginal(self, v: bool = True) -> LevelSearchArgs:
        self.original = v
        return self

    def isOriginal(self) -> bool:
        return self.original

    def setTwoPlayer(self, v: bool = True) -> LevelSearchArgs:
        self.twoPlayer = v
        return self

    def isTwoPlayer(self) -> bool:
        return self.twoPlayer

    def setCoins(self, v: bool = True) -> LevelSearchArgs:
        self.coins = v
        return self

    def hasCoins(self) -> bool:
        return self.coins

    def setEpic(self, v: bool = True) -> LevelSearchArgs:
        self.epic = v
        return self

    def isEpic(self) -> bool:
        return self.epic

    def setLegendary(self, v: bool = True) -> LevelSearchArgs:
        self.legendary = v
        return self

    def isLegendary(self) -> bool:
        return self.legendary

    def setMythic(self, v: bool = True) -> LevelSearchArgs:
        self.mythic = v
        return self

    def isMythic(self) -> bool:
        return self.mythic

    def setNoStar(self, v: bool = True) -> LevelSearchArgs:
        self.noStar = v
        return self

    def isNoStar(self) -> bool:
        return self.noStar

    def setStar(self, v: bool = True) -> LevelSearchArgs:
        self.star = v
        return self

    def isStar(self) -> bool:
        return self.star

    def setUncompleted(self, v: bool = True) -> LevelSearchArgs:
        self.uncompleted = v
        return self

    def isUncompleted(self) -> bool:
        return self.uncompleted

    def setOnlyCompleted(self, v: bool = True) -> LevelSearchArgs:
        self.onlyCompleted = v
        return self

    def isOnlyCompleted(self) -> bool:
        return self.onlyCompleted

    # --- 构建请求数据 ---

    def getData(self) -> dict[str, str]:
        """将所有参数转换为端点可直接发送的 dict。"""
        data: dict[str, str] = {}
        if self.type is not None:
            data["type"] = str(self.type)
        if self.str is not None:
            data["str"] = self.str
        if self.page:
            data["page"] = str(self.page)
        if self.gauntlet is not None:
            data["gauntlet"] = str(self.gauntlet)
        if self.diff is not None:
            data["diff"] = self.diff
        if self.demonFilter is not None:
            data["demonFilter"] = str(self.demonFilter)
        if self.len is not None:
            data["len"] = self.len
        if self.song is not None:
            data["song"] = str(self.song)
        if self.customSong:
            data["customSong"] = "1"

        # 布尔开关 — 只有 True 才发 "1"
        for key in ("featured", "original", "twoPlayer", "coins",
                     "epic", "legendary", "mythic", "noStar", "star",
                     "uncompleted", "onlyCompleted"):
            if getattr(self, key):
                data[key] = "1"

        if self._completedLevels is not None:
            data["completedLevels"] = self._completedLevels

        data["secret"] = "Wmfd2893gb7"
        return data


if __name__ == "__main__":
    args = (LevelSearchArgs()
        .setSearchType(LevelSearchType.RECENT)
        .setSearch("")
        .setDifficulty([Difficulty.ANY_DEMON])
        .setLength([Length.PLAT])
    )
    args.star = True
    print(args.getData())
    
    from plugins.gd_api.gd import getLevelSearch
    print(getLevelSearch(args))
