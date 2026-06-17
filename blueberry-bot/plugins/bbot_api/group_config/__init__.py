import os, json
from typing import Any, Generic, TypeVar, Optional

from pydantic import BaseModel

# Sentinel 用于区分"未设置"和"值为 None"
_UNSET = object()


class ConfigItem(BaseModel):
    """配置项的基类。
    
    子类定义字段及其默认值，默认值即为 global 层的 fallback。
    """
    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()
    
    def load_dict(self, data: dict[str, Any]) -> "ConfigItem":
        self.__dict__.update(data)
        return self


_C = TypeVar("_C", bound=ConfigItem)


class GroupConfig(Generic[_C]):
    """三层配置管理器：group 层 → global 层 → 类默认值。
    
    查找顺序：group 覆盖值（非 None）→ global 层值 → Config 类变量默认值
    
    工作方式：
    - global_config: 全局默认配置实例
    - group_overrides: 每个 group 的覆盖字段 dict（只存有差异的字段）
    - get(group) 返回合并后的完整配置对象；group="global" 时返回 global 配置
    - set(group, **kwargs) 设置 group 层的覆盖字段
    - set_global(**kwargs) 设置 global 层默认值
    - reset(group, *keys) 重置 group 的指定字段（回退到 global）
    - reset_all(group) 重置 group 所有字段
    """
    
    config_class: type[_C]
    global_config: _C
    group_overrides: dict[str, dict[str, Any]]
    config_path: str | None = None
    
    def __init__(self, config_class: type[_C], config_path: str | None = None) -> None:
        self.config_class = config_class
        self.global_config = config_class()
        self.group_overrides = {}
        self.config_path = config_path
    
    # ── 读取 ─────────────────────────────────────────────
    
    def get(self, group: str) -> _C:
        """获取 group 的合并配置。group="global" 时直接返回 global 配置。"""
        if group == "global":
            return self.global_config
        config = self.config_class()
        # 1) 先加载 global 默认值
        config.load_dict(self.global_config.to_dict())
        # 2) 再覆盖 group 层的非 None 字段
        overrides = self.group_overrides.get(group, {})
        # 只覆盖值不是 None 的字段
        merged = {k: v for k, v in overrides.items() if v is not None}
        config.load_dict(merged)
        return config
    
    def get_global(self) -> _C:
        return self.global_config
    
    def get_value(self, group: str, key: str) -> Any:
        """获取某个字段的值：group → global → 类默认值。"""
        overrides = self.group_overrides.get(group, {}) if group != "global" else {}
        if key in overrides and overrides[key] is not None:
            return overrides[key]
        global_val = getattr(self.global_config, key, _UNSET)
        if global_val is not _UNSET:
            return global_val
        return getattr(self.config_class, key, None)
    
    # ── 写入 ─────────────────────────────────────────────
    
    def set(self, group: str, **kwargs: Any) -> None:
        """设置 group 层的覆盖字段。
        
        group="global" 时等同于 set_global。
        传入 None 的字段会被直接删除（从 overrides 中移除），回退到 global 层。
        不传入的字段保持原有 group 覆盖值不变。
        """
        if group == "global":
            self.set_global(**kwargs)
            return
        if group not in self.group_overrides:
            self.group_overrides[group] = {}
        for key, value in kwargs.items():
            if value is None:
                self.group_overrides[group].pop(key, None)
            else:
                self.group_overrides[group][key] = value
    
    def override_with(self, group: str, config: _C) -> None:
        """用 Config 实例设置 group 覆盖字段（有 IDE 自动补全和类型提示）。
        
        所有显式赋值的字段都会存入 group_overrides，即使值与类默认值相同。
        值为 None 的字段会被直接删除（从 overrides 中移除），回退到 global 层。
        
        用法:
            overrides = MyConfig()
            overrides.cooldown = 30
            cfg.override_with("group1", overrides)
        """
        self.set(group, **config.to_dict())
    
    def set_global(self, **kwargs: Any) -> None:
        """更新 global 层默认值。"""
        self.global_config.load_dict(kwargs)
    
    # ── 重置 ─────────────────────────────────────────────
    
    def reset(self, group: str, *keys: str) -> None:
        """重置 group 的指定字段（从 overrides 中移除），使其回退到 global。"""
        if group == "global":
            return
        if group not in self.group_overrides:
            return
        for key in keys:
            self.group_overrides[group].pop(key, None)
    
    def reset_all(self, group: str) -> None:
        """重置 group 的所有覆盖字段。"""
        if group == "global":
            return
        self.group_overrides.pop(group, None)
    
    # ── 持久化 ───────────────────────────────────────────
    
    def save(self) -> None:
        if not self.config_path:
            return
        data = {
            "global_config": self.global_config.to_dict(),
            "group_overrides": self.group_overrides,
        }
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load(self) -> None:
        if not self.config_path or not os.path.exists(self.config_path):
            return
        try:
            with open(self.config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(data, dict):
            return
        
        global_data = data.get("global_config")
        if isinstance(global_data, dict):
            self.global_config.load_dict(global_data)
        
        overrides = data.get("group_overrides")
        if isinstance(overrides, dict):
            self.group_overrides.update(overrides)


# ── 可复用的配置指令处理函数 ───────────────────────────

from collections.abc import Awaitable, Callable

def make_config_handler(
    cmd_name: str,
    config_class: type[_C],
    config: GroupConfig[_C],
    get_groupid_function: Callable[[Any],str]|None=None
):
    """创建一个配置指令的处理函数。
    
    返回 (handler, help_text)，调用方自行注册到 matcher：
    
        from nonebot import on_command
        from nonebot.permission import SUPERUSER
        matcher = on_command("myconfig", permission=SUPERUSER)
        handler, help_text = make_config_handler("myconfig", MyConfigItem, my_config)
        matcher.handle()(handler)
    
    参数:
        cmd_name: 指令名称，用于帮助提示
        config_class: ConfigItem 子类，用于 model_fields 校验
        config: GroupConfig 实例
    返回:
        (handler, help_text) 元组
    """
    from nonebot.internal.adapter import Bot,Event,Message
    from nonebot.adapters.onebot.v11 import Bot as OBBot, GroupMessageEvent
    from nonebot.params import CommandArg
    from nonebot.adapters.onebot.v11.message import Message as OBMessage
    from nonebot.matcher import Matcher
    from pydantic import TypeAdapter
    from ...bbot_api import get_group_id
    help_text = (
        f"{cmd_name} get [-g <group>] <field>\n"
        f"{cmd_name} set [-g <group>] <field> <value>\n"
        f"{cmd_name} list [-g <group>]\n"
        f"{cmd_name} list-groups\n"
        f"\n-g 指定 group (群号/global/private)，不指定时默认当前群\n"
        f"group 名为 global 时直接操作 global 层"
    )

    async def handler(
        bot: Bot,
        event: Event,
        matcher: Matcher,
        args: Message = CommandArg(),
    ):
        parts = args.extract_plain_text().strip().split()
        if not parts:
            await matcher.finish(help_text)

        subcmd = parts[0]

        # 解析 -g 参数
        group: str | None = None
        rest: list[str] = []
        i = 1
        while i < len(parts):
            if parts[i] == "-g" and i + 1 < len(parts):
                group = parts[i + 1]
                i += 2
            else:
                rest.append(parts[i])
                i += 1

        # 未指定 group 时尝试从事件获取当前群
        if group is None:
            if get_groupid_function:
                group=get_groupid_function(event)
            else:
                group=get_group_id(event)
            if group == "private":
                await matcher.finish("私聊中必须用 -g 参数指定 group")

        # ── list-groups ────────────────────────────────
        if subcmd == "list-groups":
            groups = sorted(config.group_overrides.keys())
            if not groups:
                await matcher.finish("没有 group 有覆盖配置")
            lines = ["有覆盖配置的 group:"] + [f"  {g}" for g in groups]
            await matcher.finish("\n".join(lines))

        # ── list ────────────────────────────────────────
        if subcmd == "list":
            cfg = config.get(group)
            overrides = config.group_overrides.get(group, {}) if group != "global" else {}
            lines = [f"配置项 ({group}):"]
            for field in config_class.model_fields:
                val = getattr(cfg, field)
                is_overridden = field in overrides
                marker = " *" if is_overridden else ""
                source = "(group)" if is_overridden else "(global/class)"
                lines.append(f"  {field}: {val!r}{marker}  {source}")
            await matcher.finish("\n".join(lines))

        # ── get ─────────────────────────────────────────
        if subcmd == "get":
            if len(rest) < 1:
                await matcher.finish(f"用法: get [-g <group>] <field>")
            field = rest[0]
            if field not in config_class.model_fields:
                await matcher.finish(f"无效字段: {field}")
            val = config.get_value(group, field)
            overrides = config.group_overrides.get(group, {}) if group != "global" else {}
            source = "group" if field in overrides and overrides[field] is not None else "global/class"
            await matcher.finish(f"{group} 的 {field} = {val!r} ({source})")

        # ── set ─────────────────────────────────────────
        if subcmd == "set":
            if len(rest) < 2:
                await matcher.finish(f"用法: set [-g <group>] <field> <value>")
            field, raw_val = rest[0], rest[1]
            if field not in config_class.model_fields:
                await matcher.finish(f"无效字段: {field}")
            try:
                field_type = config_class.model_fields[field].annotation
                if raw_val.lower() == "none":
                    value = None
                else:
                    value = TypeAdapter(field_type).validate_python(raw_val)
                    
            except Exception as e:
                await matcher.finish(f"无效值: {raw_val}\n错误: {e}")
            config.set(group, **{field: value})
            config.save()
            await matcher.finish(f"已设置 {group} 的 {field} = {value!r}")

        await matcher.finish(f"未知子命令: {subcmd}")

    return handler


if __name__ == "__main__":
    class MyConfig(ConfigItem):
        a: int = 1
        b: str = "hello"
    
    cfg = GroupConfig(MyConfig)
    
    # 测试 global 默认值
    print("=== Global default ===")
    c = cfg.get("session1")
    print(f"  a={c.a}, b={c.b}")  # 1, hello
    
    # 测试 group 覆盖
    cfg.set("group1", a=2, b="world")
    c = cfg.get("group1")
    print("=== After group set ===")
    print(f"  a={c.a}, b={c.b}")  # 2, world
    
    # 测试 group 层 None → fallback 到 global
    cfg.set("group1", a=None)
    c = cfg.get("group1")
    print("=== Group a=None (fallback) ===")
    print(f"  a={c.a}, b={c.b}")  # 1, world
    
    # 测试 get_value
    print("=== get_value ===")
    print(f"  a={cfg.get_value('group1', 'a')}")  # 1 (fallback)
    print(f"  b={cfg.get_value('group1', 'b')}")  # world
    
    # 测试 reset
    cfg.reset("group1", "b")
    c = cfg.get("group1")
    print("=== After reset b ===")
    print(f"  a={c.a}, b={c.b}")  # 1, hello
    
    # 测试 save / load
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        tmp = f.name
    cfg.config_path = tmp
    cfg.save()
    print(f"\nSaved to {tmp}")
    
    cfg2 = GroupConfig(MyConfig, tmp)
    cfg2.load()
    c = cfg2.get("group1")
    print("=== After load ===")
    print(f"  a={c.a}, b={c.b}")  # 1, hello
    
    # 测试 group="global" 直接操作 global 层
    cfg.set("global", b="from_global")
    c = cfg.get("group1")
    print("=== After set global via group='global' ===")
    print(f"  a={c.a}, b={c.b}")  # 1, from_global
    os.unlink(tmp)