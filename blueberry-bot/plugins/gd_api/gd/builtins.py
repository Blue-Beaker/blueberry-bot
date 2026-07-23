from enum import Enum
from .models import Song

class OfficialSong(Song):
    level_id:int=-1
    def __init__(self) -> None:
        super().__init__()
    @classmethod
    def build(cls,level_id:int,server_id:int,name:str,author:str):
        song=cls()
        song.level_id=level_id
        song.id=server_id
        song.name=name
        song.artistName=author
        return song

OFFICIAL_SONGS:dict[int,OfficialSong]={}

def getOfficialSong(musicID:int) -> OfficialSong|None:
    return OFFICIAL_SONGS.get(musicID)

def load_official_songs():
    songs=[OfficialSong.build(-1,-1,"Practice: Stay Inside Me","OcularNebula"),
    OfficialSong.build(1,0,"Stereo Madness","Foreverbound"),
    OfficialSong.build(2,1,"Back on Track","DJVI"),
    OfficialSong.build(3,2,"Polargeist","Step"),
    OfficialSong.build(4,3,"Dry Out","DJVI"),
    OfficialSong.build(5,4,"Base after Base","DJVI"),
    OfficialSong.build(6,5,"Cant Let Go","DJVI"),
    OfficialSong.build(7,6,"Jumper","Waterflame"),
    OfficialSong.build(8,7,"Time Machine","Waterflame"),
    OfficialSong.build(9,8,"Cycles","DJVI"),
    OfficialSong.build(10,9,"xStep","DJVI"),
    OfficialSong.build(11,10,"Clutterfunk","Waterflame"),
    OfficialSong.build(12,11,"Theory of Everything","DJ-Nate"),
    OfficialSong.build(13,12,"Electroman Adventures","Waterflame"),
    OfficialSong.build(14,13,"Clubstep","DJ-Nate"),
    OfficialSong.build(15,14,"Electrodynamix","DJ-Nate"),
    OfficialSong.build(16,15,"Hexagon Force","Waterflame"),
    OfficialSong.build(17,16,"Blast Processing","Waterflame"),
    OfficialSong.build(18,17,"Theory of Everything 2","DJ-Nate"),
    OfficialSong.build(19,18,"Geometrical Dominator","Waterflame"),
    OfficialSong.build(20,19,"Deadlocked","F-777"),
    OfficialSong.build(21,20,"Fingerdash","MDK"),
    OfficialSong.build(22,21,"Dash","MDK"),
    OfficialSong.build(23,22,"Explorers","Hinkik"),
    OfficialSong.build(1001,23,"The Seven Seas","F-777"),
    OfficialSong.build(1002,24,"Viking Arena","F-777"),
    OfficialSong.build(1003,25,"Airborne Robots","F-777"),
    OfficialSong.build(3001,26,"Secret","RobTop"),
    OfficialSong.build(2001,27,"Payload","Dex Arson"),
    OfficialSong.build(2002,28,"Beast Mode","Dex Arson"),
    OfficialSong.build(2003,29,"Machina","Dex Arson"),
    OfficialSong.build(2004,30,"Years","Dex Arson"),
    OfficialSong.build(2005,31,"Frontlines","Dex Arson"),
    OfficialSong.build(2006,32,"Space Pirates","Waterflame"),
    OfficialSong.build(2007,33,"Striker","Waterflame"),
    OfficialSong.build(2008,34,"Embers","Dex Arson"),
    OfficialSong.build(2009,35,"Round 1","Dex Arson"),
    OfficialSong.build(2010,36,"Monster Dance Off","F-777"),
    OfficialSong.build(4001,37,"Press Start","MDK"),
    OfficialSong.build(4002,38,"Nock Em","Bossfight"),
    OfficialSong.build(4003,39,"Power Trip","Boom Kitty")]
    
    for song in songs:
        OFFICIAL_SONGS[song.id]=song
        
load_official_songs()