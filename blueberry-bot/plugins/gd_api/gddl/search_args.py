from enum import Enum
import json
from typing import Any, Optional


class Sort(Enum):
    ID = "ID"
    RATING = "rating"
    NAME = "name"
    ENJOYMENT = "enjoyment"
    ENJOYMENT_COUNT = "enjoymentCount"
    RATING_COUNT = "ratingCount"
    DEVIATION = "deviation"
    POPULARITY = "popularity"
    RANDOM = "random"


class SortDir(Enum):
    ASCEND = "asc"
    DESCEND = "desc"


class Difficulty(Enum):
    OFFICIAL = "Official"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
    INSANE = "Insane"
    EXTREME = "Extreme"

class Length(Enum):
    ANY = 0
    TINY = 1
    SHORT = 2
    MEDIUM = 3
    LONG = 4
    XL = 5
    PLAT = 6

class TwoPlayer(Enum):
    ANY = "any"
    NO = "no"
    ONLY = "only"


class GDDLSearchArgs:
    # Pagination
    limit: int|None = None
    page: int|None = 0

    # Sorting
    sort: Optional[Sort] = None
    sortDirection: Optional[SortDir] = None

    # Search
    name: Optional[str] = None
    creator: Optional[str] = None
    song: Optional[str] = None

    # Rating / Enjoyment / Deviation ranges
    minRating: Optional[float] = None
    maxRating: Optional[float] = None
    minEnjoyment: Optional[float] = None
    maxEnjoyment: Optional[float] = None
    minEnjoymentCount: Optional[int] = None
    maxEnjoymentCount: Optional[int] = None
    minDeviation: Optional[float] = None
    maxDeviation: Optional[float] = None

    # Difficulty & level properties
    difficulty: Optional[Difficulty] = None
    minID: Optional[int] = None
    maxID: Optional[int] = None
    length: Optional[Length] = None
    minSeconds: Optional[float] = None
    maxSeconds: Optional[float] = None
    minObjects: Optional[int] = None
    maxObjects: Optional[int] = None
    minDensity: Optional[float] = None
    maxDensity: Optional[float] = None
    twoPlayer: Optional[TwoPlayer] = None
    isInPack: Optional[bool] = None

    # Tags & skillsets
    topTagID: Optional[int] = None
    hasSkillset: Optional[int] = None

    # User-based exclusions
    notRatedBy: Optional[int] = None

    # Exclude flags
    excludeCompleted: Optional[bool] = None
    excludeRated: Optional[bool] = None
    excludeRatedEnjoyment: Optional[bool] = None
    excludeUnrated: Optional[bool] = None
    excludeUnratedEnjoyment: Optional[bool] = None
    
    def getData(self):
        data:dict[str,Any]={}
        for k,v in self.__dict__.items():
            if isinstance(v,Enum):
                data[k]=v.value
                continue
            data[k]=v
        return data