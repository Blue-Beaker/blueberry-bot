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
    sort_direction: Optional[SortDir] = None

    # Search
    name: Optional[str] = None
    creator: Optional[str] = None
    song: Optional[str] = None

    # Rating / Enjoyment / Deviation ranges
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None
    min_enjoyment: Optional[float] = None
    max_enjoyment: Optional[float] = None
    min_enjoyment_count: Optional[int] = None
    max_enjoyment_count: Optional[int] = None
    min_deviation: Optional[float] = None
    max_deviation: Optional[float] = None
    min_submission_count: Optional[int] = None
    max_submission_count: Optional[int] = None

    # Difficulty & level properties
    difficulty: Optional[Difficulty] = None
    min_id: Optional[int] = None
    max_id: Optional[int] = None
    length: Optional[int] = None
    two_player: Optional[TwoPlayer] = None
    is_in_pack: Optional[bool] = None

    # Tags & skillsets
    top_tag_id: Optional[int] = None
    has_skillset: Optional[int] = None

    # User-based exclusions
    not_rated_by: Optional[int] = None

    # Exclude flags
    exclude_completed: Optional[bool] = None
    exclude_rated: Optional[bool] = None
    exclude_rated_enjoyment: Optional[bool] = None
    exclude_unrated: Optional[bool] = None
    exclude_unrated_enjoyment: Optional[bool] = None
    
    def getData(self):
        data:dict[str,Any]={}
        for k,v in self.__dict__.items():
            if isinstance(v,Enum):
                data[k]=v.value
                continue
            data[k]=v
        return data