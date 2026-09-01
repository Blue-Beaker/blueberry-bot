from plugins.gd_api.gd.models import Length, Difficulty, Level, Song, PlayerInfo


def test_models():
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
