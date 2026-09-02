import pytest
from plugins.gd_api.gddl.models import GDDLTags, GDDLDifficulty


class TestGDDLDifficulty:
    """测试 GDDLDifficulty 枚举"""

    def test_difficulty_values(self):
        assert GDDLDifficulty.OFFICIAL.value == "Official"
        assert GDDLDifficulty.EASY.value == "Easy"
        assert GDDLDifficulty.MEDIUM.value == "Medium"
        assert GDDLDifficulty.HARD.value == "Hard"
        assert GDDLDifficulty.INSANE.value == "Insane"
        assert GDDLDifficulty.EXTREME.value == "Extreme"

    def test_difficulty_from_value(self):
        assert GDDLDifficulty("Official") == GDDLDifficulty.OFFICIAL
        assert GDDLDifficulty("Extreme") == GDDLDifficulty.EXTREME


class TestGDDLTags:
    """测试 GDDLTags 枚举及其元数据"""

    # === 基础值测试 ===

    def test_tag_values(self):
        """测试枚举成员的基础整数值"""
        assert GDDLTags.CUBE.value == 1
        assert GDDLTags.SHIP.value == 2
        assert GDDLTags.BALL.value == 3
        assert GDDLTags.UFO.value == 4
        assert GDDLTags.WAVE.value == 5
        assert GDDLTags.ROBOT.value == 6
        assert GDDLTags.SPIDER.value == 7
        assert GDDLTags.NERVE_CONTROL.value == 8
        assert GDDLTags.MEMORY.value == 9
        assert GDDLTags.LEARNY.value == 10
        assert GDDLTags.DUALS.value == 11
        assert GDDLTags.CHOKEPOINTS.value == 12
        assert GDDLTags.HIGH_CPS.value == 13
        assert GDDLTags.TIMINGS.value == 14
        assert GDDLTags.FLOW.value == 15
        assert GDDLTags.OVERALL.value == 16
        assert GDDLTags.GIMMICKY.value == 17
        assert GDDLTags.FAST_PACED.value == 18
        assert GDDLTags.SLOW_PACED.value == 19
        assert GDDLTags.SWING.value == 20

    def test_tag_from_value(self):
        """通过整数值创建枚举成员"""
        assert GDDLTags(1) == GDDLTags.CUBE
        assert GDDLTags(20) == GDDLTags.SWING
        assert GDDLTags(8) == GDDLTags.NERVE_CONTROL

    # === tag_name 测试 ===

    def test_cube_tag_name(self):
        assert GDDLTags.CUBE.tag_name == "Cube"

    def test_ship_tag_name(self):
        assert GDDLTags.SHIP.tag_name == "Ship"

    def test_nerve_control_tag_name(self):
        assert GDDLTags.NERVE_CONTROL.tag_name == "Nerve Control"

    def test_all_tags_have_names(self):
        """所有标签都有非空名称"""
        for tag in GDDLTags:
            assert tag.tag_name, f"{tag.name} has empty tag_name"
            assert isinstance(tag.tag_name, str)

    # === tag_desc 测试 ===

    def test_cube_tag_desc(self):
        assert "cube sections" in GDDLTags.CUBE.tag_desc.lower()

    def test_memory_tag_desc(self):
        assert "remembering" in GDDLTags.MEMORY.tag_desc.lower()

    def test_all_tags_have_descriptions(self):
        """所有标签都有非空描述"""
        for tag in GDDLTags:
            assert tag.tag_desc, f"{tag.name} has empty tag_desc"
            assert isinstance(tag.tag_desc, str)

    # === tag_order 测试 ===

    def test_cube_tag_order(self):
        assert GDDLTags.CUBE.tag_order == 1

    def test_ship_tag_order(self):
        assert GDDLTags.SHIP.tag_order == 2

    def test_swing_tag_order(self):
        # SWING 的 value=20（API ID），但 tag_order=8（显示排序）
        assert GDDLTags.SWING.tag_order == 8

    def test_all_tags_have_orders(self):
        """所有标签都有有效的排序值"""
        for tag in GDDLTags:
            assert isinstance(tag.tag_order, int)
            assert 1 <= tag.tag_order <= 20

    def test_orders_are_sequential(self):
        """排序值应该是 1-20 连续的"""
        orders = sorted([tag.tag_order for tag in GDDLTags])
        assert orders == list(range(1, 21))

    # === 综合测试 ===

    def test_all_members_complete(self):
        """所有枚举成员都有完整的元数据"""
        # 注意：GDDLTags() 按 value (API ID) 查找，不是 tag_order
        expected_tags = {
            1: ("Cube", "This level has cube sections"),
            2: ("Ship", "This level has ship sections"),
            3: ("Ball", "This level has ball sections"),
            4: ("UFO", "This level has UFO sections"),
            5: ("Wave", "This level has wave sections"),
            6: ("Robot", "This level has robot sections"),
            7: ("Spider", "This level has spider sections"),
            8: ("Nerve Control", "This level tests your consistency"),
            9: ("Memory", "This level requires remembering"),
            10: ("Learny", "This level needs a significant time investment"),
            11: ("Duals", "This level has duals"),
            12: ("Chokepoints", "This level contains parts with very condensed"),
            13: ("High CPS", "This level has several sections that require very fast"),
            14: ("Timings", "This level tests your ability to perform many very precise"),
            15: ("Flow", "This level has many dynamic gameplay transitions"),
            16: ("Overall", "This level has no specific skillset"),
            17: ("Gimmicky", "This level primarily focuses on developing an experimental"),
            18: ("Fast-Paced", "This level has fast-moving sections"),
            19: ("Slow-Paced", "This level has slower-moving sections"),
            20: ("Swing", "This level has swing sections"),
        }

        for api_id, (name, desc_prefix) in expected_tags.items():
            tag = GDDLTags(api_id)
            assert tag.tag_name == name
            assert desc_prefix.lower() in tag.tag_desc.lower()

    def test_total_count(self):
        """应该有 20 个标签"""
        assert len(list(GDDLTags)) == 20

    def test_iteration_order(self):
        """迭代顺序应该按定义顺序"""
        tags = list(GDDLTags)
        assert tags[0] == GDDLTags.CUBE
        assert tags[1] == GDDLTags.SHIP
