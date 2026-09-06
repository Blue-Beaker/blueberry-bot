from typing import Any, Union
import inspect

IMG_TYPE = Union[str,bytes]

class RenderArgs:
    def __init__(self) -> None:
        pass
    def get_params(self):
        keys:set[str]=set()
        keys.update(self.__class__.__dict__.keys())
        keys.update(self.__dict__.keys())
        
        data:dict[str,Any]={}
        for k in keys:
            if k.startswith("__"):
                continue
            val=getattr(self,k)
            if val is not None:
                data[k]=val
        return data
    def update_args(self,**kwargs):
        self.__dict__.update(kwargs)
    
    @property
    def scene_type(self):
        return ""
    
class PlayerInfoRenderArgs(RenderArgs):
    scene_type: str="player_info"
    playername: str=""
    stars: int = 0
    moons: int = 0
    coins: int = 0
    usercoins: int = 0
    demons: int = 0
    creatorpoints: int = 0
    nondemons: int|str = 0
    nonpemons: int|str = 0
    c_demons: int = 0
    pemons: int = 0
    player_icon: IMG_TYPE
    icon_cube: IMG_TYPE
    icon_ship: IMG_TYPE
    icon_ball: IMG_TYPE
    icon_ufo: IMG_TYPE
    icon_wave: IMG_TYPE
    icon_robot: IMG_TYPE
    icon_spider: IMG_TYPE
    icon_swing: IMG_TYPE
    icon_jetpack: IMG_TYPE
    
class DemonsRenderArgs(RenderArgs):
    scene_type: str="demons"
    c_ezd: int = 0
    c_med: int = 0
    c_hdd: int = 0
    c_insd: int = 0
    c_exd: int = 0
    c_all: int = 0
    p_ezd: int = 0
    p_med: int = 0
    p_hdd: int = 0
    p_insd: int = 0
    p_exd: int = 0
    p_all: int = 0
    weekly: int = 0
    gauntlet: int = 0

class NonDemonsRenderArgs(RenderArgs):
    scene_type: str="nondemons"
    c_auto: int = 0
    c_easy: int = 0
    c_normal: int = 0
    c_hard: int = 0
    c_harder: int = 0
    c_insane: int = 0
    c_all: int|str = 0
    p_auto: int = 0
    p_easy: int = 0
    p_normal: int = 0
    p_hard: int = 0
    p_harder: int = 0
    p_insane: int = 0
    p_all: int|str = 0
    daily: int = 0
    gauntlet: int = 0
    
class LevelRenderArgs(RenderArgs):
    scene_type: str = "level"
    
    level_id: int = 0
    level_name: str = ""
    creator: str = ""
    
    song_id: int = 0
    song_name: str = ""
    song_author: str = ""
    stars: int = 0
    is_plat: bool = False
    length: str = ""
    
    likes: int = 0
    downloads: int = 0
    orbs: int = 0
    # Texture resources — accepts raw bytes or URL string
    thumbnail: IMG_TYPE
    
    difficulty: int = 0
    # 0 = Star rate, 1 = Featured, 2 = Epic, 3 = Legendary, 4 = Mythic
    feature_level: int = 0
    # Coins
    coins: int = 0
    bronze_coins: bool = False
    # Plarformer Data
    weight: str
    pemonlist: str
    diffchart_tier: str
    
class LevelLargeRenderArgs(LevelRenderArgs):
    scene_type: str = "level_large"
    
    # For level description
    description: str = ''
    # For external descriptions from other sources
    description2: str = ''
    
    # Detailed length, like 3m50s
    length2: str
    # Detailed song info
    song_info: str
    
    # Plarformer Data
    checkpoints: str
    diffchart_tags: str
    # Challenge
    challenge_name: str
    challenge_tier: str
    challenge_tags: str
    
    # AREDL
    aredl_pos: str
    aredl_tags: str
    # Underrated
    underrated_tier: str
    underrated_tags: str
    # NLW-like
    nlw_type: str
    nlw_tier: str
    nlw_tags: str