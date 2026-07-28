import os, json
from typing import Any, Generic, TypeVar, Optional

from pydantic import BaseModel
from . import lifecycle

# Sentinel 用于区分"未设置"和"值为 None"
_UNSET = object()


class ConfigItem(BaseModel):
    """配置项的基类。
    
    子类定义字段及其默认值，默认值即为 global 层的 fallback。
    """
    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()
    
    def load_dict(self, data: dict[str, Any]):
        self.__dict__.update(data)
        return self


_C = TypeVar("_C", bound=ConfigItem)


class GroupConfig(Generic[_C]):
    """四层配置管理器：group 层 → permgroup 层 → global 层 → 类默认值。
    
    查找顺序：group 覆盖值（非 None）→ permgroup 覆盖值 → global 层值 → Config 类变量默认值
    
    层说明：
    - global_config: 全局默认配置实例
    - permgroup 条目以 permgroup_<name> 为 key 存储在 group_overrides 中，
      在 global 之后、group 之前应用
    - group_overrides: 每个 group/群的覆盖字段 ConfigItem 实例（优先级最高）
    - permgroup 映射由全局 PermGroupManager 管理，所有 GroupConfig 实例共用
    - get(group) 返回合并后的完整配置对象；group="global" 时返回 global 配置
    - set(group, **kwargs) 设置 group 层的覆盖字段
    - set_global(**kwargs) 设置 global 层默认值
    - permgroup 操作：get_permgroup / set_permgroup / delete_permgroup / list_permgroups
    - reset(group, *keys) 重置 group 的指定字段（回退到下层）
    - reset_all(group) 重置 group 所有字段
    """
    
    config_class: type[_C]
    global_config: _C
    group_overrides: dict[str, _C]
    config_path: str | None = None
    
    def __init__(self, config_class: type[_C], config_path: str | None = None) -> None:
        self.config_class = config_class
        self.global_config = config_class()
        self.group_overrides = {}
        self.config_path = config_path
    
    # ── 读取 ─────────────────────────────────────────────
    
    def get(self, group: str) -> _C:
        """获取 group 的合并配置。
        
        合并顺序：group 覆盖 → permgroup 覆盖 → global → 类默认值。
        
        permgroup 映射由全局 PermGroupManager 提供。
        group="global" 时直接返回 global 配置。
        """
        if group == "global":
            return self.global_config
        
        config = self.config_class()
        config.load_dict(self.global_config.to_dict())
        
        # 应用 permgroup 覆盖（在 global 之后、group 之前）
        permgroup_key = self._find_matching_permgroup(group)
        if permgroup_key is not None:
            pg_overrides = self.group_overrides.get(permgroup_key)
            if pg_overrides is not None:
                merged = {k: v for k, v in pg_overrides.to_dict().items() if v is not None}
                config.load_dict(merged)
        
        # 应用 group 覆盖（最高优先级）
        overrides = self.group_overrides.get(group)
        if overrides is not None:
            merged = {k: v for k, v in overrides.to_dict().items() if v is not None}
            config.load_dict(merged)
        
        return config
    
    def _get_pg_manager(self):
        """获取全局 PermGroupManager。懒导入避免循环依赖。"""
        from .permgroup_manager import get_permgroup_manager
        return get_permgroup_manager()
    
    def _find_matching_permgroup(self, group: str) -> str | None:
        """查找匹配 group 的 permgroup key（如 permgroup_myperms）。
        
        通过全局 PermGroupManager 查找该群组绑定的权限组，
        返回第一个有覆盖配置的 permgroup key。
        """
        pg_names = self._get_pg_manager().get_group_permgroups(group)
        for pg_name in pg_names:
            key = f"permgroup_{pg_name}"
            if key in self.group_overrides:
                return key
        # 直接匹配（group 本身就是 permgroup key）
        if group.startswith("permgroup_") and group in self.group_overrides:
            return group
        return None
    
    def get_global(self) -> _C:
        return self.global_config
    
    def get_value(self, group: str, key: str) -> Any:
        """获取某个字段的值：group → permgroup → global → 类默认值。"""
        # group 覆盖
        overrides = self.group_overrides.get(group) if group != "global" else None
        if overrides is not None:
            val = getattr(overrides, key, _UNSET)
            if val is not _UNSET and val is not None:
                return val
        # permgroup 覆盖
        if group != "global":
            permgroup_key = self._find_matching_permgroup(group)
            if permgroup_key is not None:
                pg = self.group_overrides.get(permgroup_key)
                if pg is not None:
                    val = getattr(pg, key, _UNSET)
                    if val is not _UNSET and val is not None:
                        return val
        # global
        global_val = getattr(self.global_config, key, _UNSET)
        if global_val is not _UNSET:
            return global_val
        return getattr(self.config_class, key, None)
    
    # ── 权限组 (permgroup) ───────────────────────────────
    
    def get_permgroup(self, name: str) -> _C | None:
        """获取指定权限组的配置（不合并 global 层）。
        
        返回 None 表示权限组不存在或没有任何覆盖字段。
        """
        key = f"permgroup_{name}"
        return self.group_overrides.get(key)
    
    def set_permgroup(self, name: str, **kwargs: Any) -> None:
        """设置权限组的覆盖字段。
        
        权限组以 permgroup_<name> 为 key 存储在 group_overrides 中，
        和普通 group 覆盖完全一样的存储方式。
        不传 kwargs 时仅确保权限组存在。
        """
        self.set(f"permgroup_{name}", **kwargs)
    
    def delete_permgroup(self, name: str) -> bool:
        """删除权限组。返回是否实际删除。"""
        key = f"permgroup_{name}"
        if key in self.group_overrides:
            del self.group_overrides[key]
            return True
        return False
    
    def list_permgroups(self) -> list[str]:
        """返回所有权限组名称列表（不含 permgroup_ 前缀）。"""
        return sorted(
            key[len("permgroup_"):]
            for key in self.group_overrides
            if key.startswith("permgroup_")
        )
    
    # ── 写入 ─────────────────────────────────────────────
    
    def get_for_edit(self, group: str) -> _C:
        """获取指定 override 层的可变引用，修改直接生效，无需额外保存。
        
        与 get() 不同，此方法返回的是 override 层自身的 ConfigItem 引用
        （不合并 global 层），直接修改字段即同步到配置中。
        
        如果 group 没有 override 数据，自动创建一个空实例并注册。
        group="global" 时返回 global 层的引用。
        
        典型用法:
            cfg = config.get_for_edit("group1")
            cfg.cooldown = 60  # 直接生效
        """
        if group == "global":
            return self.global_config
        if group not in self.group_overrides:
            self.group_overrides[group] = self.config_class()
        return self.group_overrides[group]
    
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
            # 新建条目，只保留传入的字段，其余设为 None 不产生覆盖
            self.group_overrides[group] = self.config_class()
            for f in self.config_class.model_fields:
                if f not in kwargs:
                    setattr(self.group_overrides[group], f, None)
        for key, value in kwargs.items():
            if value is None:
                # 设为 None → 从 override 中移除该字段
                if hasattr(self.group_overrides[group], key):
                    setattr(self.group_overrides[group], key, None)
            else:
                setattr(self.group_overrides[group], key, value)
    
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
        overrides = self.group_overrides.get(group)
        if overrides is None:
            return
        for key in keys:
            if hasattr(overrides, key):
                setattr(overrides, key, None)
    
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
            "group_overrides": {
                g: ov.to_dict()
                for g, ov in self.group_overrides.items()
            },
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
            for g, d in overrides.items():
                if isinstance(d, dict):
                    obj = self.config_class()
                    obj.load_dict(d)
                    self.group_overrides[g] = obj


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
    from ...bbot_api.argparse import ArgParser, ArgumentError, ShowHelp as ArgShowHelp
    from .permgroup_manager import get_permgroup_manager
    
    # ── 构建主解析器 ───────────────────────────────────
    parser = ArgParser(command_name=cmd_name, add_help=False)
    sub = parser.add_subparsers(dest="subcmd", metavar="<子命令>")
    
    # get
    p_get = sub.add_parser("get", help="查看字段值", add_help=False)
    p_get.add_argument("-g", metavar="<group>", help="群 ID")
    p_get.add_argument("-p", metavar="<permgroup>", help="权限组名")
    p_get.add_argument("field", help="字段名")
    
    # set
    p_set = sub.add_parser("set", help="设置字段值", add_help=False)
    p_set.add_argument("-g", metavar="<group>", help="群 ID")
    p_set.add_argument("-p", metavar="<permgroup>", help="权限组名")
    p_set.add_argument("field", help="字段名")
    p_set.add_argument("value", help="字段值")
    
    # list
    p_list = sub.add_parser("list", help="列出所有字段", add_help=False)
    p_list.add_argument("-g", metavar="<group>", help="群 ID")
    p_list.add_argument("-p", metavar="<permgroup>", help="权限组名")
    
    # list-groups
    sub.add_parser("list-groups", help="列出有覆盖配置的 group", add_help=False)
    
    # permgroup 子命令树
    p_pg = sub.add_parser("permgroup", help="管理权限组", add_help=False)
    pg_sub = p_pg.add_subparsers(dest="pg_action", metavar="<操作>")
    
    pg_create = pg_sub.add_parser("create", help="创建权限组", add_help=False)
    pg_create.add_argument("name", help="权限组名")
    
    pg_delete = pg_sub.add_parser("delete", help="删除权限组", add_help=False)
    pg_delete.add_argument("name", help="权限组名")
    
    pg_sub.add_parser("list", help="列出所有权限组", add_help=False)
    
    pg_bind = pg_sub.add_parser("bind", help="将权限组附加到群组", add_help=False)
    pg_bind.add_argument("name", help="权限组名")
    pg_bind.add_argument("groups", nargs="*", metavar="<group>", help="群组 ID（不指定时默认当前群）")
    
    pg_unbind = pg_sub.add_parser("unbind", help="解除群组的权限组附加", add_help=False)
    pg_unbind.add_argument("name", help="权限组名")
    pg_unbind.add_argument("groups", nargs="*", metavar="<group>", help="群组 ID（不指定时默认当前群）")
    
    pg_sub.add_parser("show-bind", help="查看所有附加关系", add_help=False)
    
    pg_list_binds = pg_sub.add_parser("list-binds", help="查看权限组绑定到的所有群组", add_help=False)
    pg_list_binds.add_argument("name", help="权限组名")
    
    help_text = (
        f"{cmd_name} get [-g <group>] [-p <permgroup>] <field>\n"
        f"{cmd_name} set [-g <group>] [-p <permgroup>] <field> <value>\n"
        f"{cmd_name} list [-g <group>] [-p <permgroup>]\n"
        f"{cmd_name} list-groups\n"
        f"{cmd_name} permgroup create <name>\n"
        f"{cmd_name} permgroup delete <name>\n"
        f"{cmd_name} permgroup list\n"
        f"{cmd_name} permgroup bind <name> [<group> ...]\n"
        f"{cmd_name} permgroup unbind <name> [<group> ...]\n"
        f"{cmd_name} permgroup show-bind\n"
        f"{cmd_name} permgroup list-binds <name>\n"
        f"\n"
        f"-g <group>      群 ID（不指定时默认当前群）\n"
        f"-p <permgroup>  权限组名（不含 permgroup_ 前缀）\n"
        f"\n"
        f"group 名为 global 时直接操作 global 层\n"
        f"permgroup 在 global 之后、group 之前应用"
    )

    def _resolve_current_group(event: Event, get_groupid_function: Callable | None) -> str:
        """从事件解析当前群组 ID，解析失败时抛出 finish。"""
        if get_groupid_function:
            gid = get_groupid_function(event)
        else:
            gid = get_group_id(event)
        if gid == "private":
            raise ValueError("私聊中必须指定群组 ID")
        return gid

    async def handler(
        bot: Bot,
        event: Event,
        matcher: Matcher,
        args: Message = CommandArg(),
    ):
        raw_text = args.extract_plain_text().strip()
        if not raw_text:
            await matcher.finish(help_text)
        
        # ── 用 ArgParser 解析 ──────────────────────────
        try:
            parsed = parser.parse_args(raw_text.split())
        except Exception as e:
            await matcher.finish(str(e))
        
        subcmd = parsed.subcmd
        
        # ── 确定目标 group ───────────────────────────
        # -p 参数转换为 -g permgroup_<name>，统一用 -g 逻辑处理
        group: str | None = getattr(parsed, "g", None)
        permgroup: str | None = getattr(parsed, "p", None)
        if permgroup is not None:
            group = f"permgroup_{permgroup}"
        
        if group is None and subcmd in ("get", "set", "list"):
            if get_groupid_function:
                group = get_groupid_function(event)
            else:
                group = get_group_id(event)
            if group == "private":
                await matcher.finish("私聊中必须用 -g 参数指定 group")
        
        # ── permgroup 子命令 ───────────────────────────
        if subcmd == "permgroup":
            pg_action = parsed.pg_action
            if pg_action is None:
                await matcher.finish(
                    f"用法:\n"
                    f"  {cmd_name} permgroup create <name>\n"
                    f"  {cmd_name} permgroup delete <name>\n"
                    f"  {cmd_name} permgroup list\n"
                    f"  {cmd_name} permgroup bind <name> [<group> ...]\n"
                    f"  {cmd_name} permgroup unbind <name> [<group> ...]\n"
                    f"  {cmd_name} permgroup show-bind\n"
                    f"  {cmd_name} permgroup list-binds <name>"
                )
            
            pg_mgr = get_permgroup_manager()
            
            if pg_action == "create":
                pg_name = parsed.name
                if config.get_permgroup(pg_name) is not None:
                    await matcher.finish(f"权限组 '{pg_name}' 已存在")
                config.set_permgroup(pg_name)
                config.save()
                await matcher.finish(f"已创建权限组: {pg_name}")
            elif pg_action == "delete":
                pg_name = parsed.name
                pg_mgr.clear_permgroup_binds(pg_name)
                pg_mgr.save()
                if config.delete_permgroup(pg_name):
                    config.save()
                    await matcher.finish(f"已删除权限组: {pg_name}")
                else:
                    await matcher.finish(f"权限组 '{pg_name}' 不存在")
            elif pg_action == "list":
                names = config.list_permgroups()
                if not names:
                    await matcher.finish("没有权限组")
                await matcher.finish("权限组:\n" + "\n".join(f"  {n}" for n in names))
            elif pg_action == "bind":
                pg_name = parsed.name
                group_ids = parsed.groups
                if not group_ids:
                    try:
                        group_ids = [_resolve_current_group(event, get_groupid_function)]
                    except ValueError as e:
                        await matcher.finish(str(e))
                if config.get_permgroup(pg_name) is None:
                    await matcher.finish(f"权限组 '{pg_name}' 不存在")
                for gid in group_ids:
                    pg_mgr.bind(gid, pg_name)
                pg_mgr.save()
                if len(group_ids) == 1:
                    await matcher.finish(f"已将权限组 '{pg_name}' 附加到群组 '{group_ids[0]}'")
                else:
                    await matcher.finish(f"已将权限组 '{pg_name}' 附加到 {len(group_ids)} 个群组: {', '.join(group_ids)}")
            elif pg_action == "unbind":
                pg_name = parsed.name
                group_ids = parsed.groups
                if not group_ids:
                    try:
                        group_ids = [_resolve_current_group(event, get_groupid_function)]
                    except ValueError as e:
                        await matcher.finish(str(e))
                results = []
                for gid in group_ids:
                    removed = pg_mgr.unbind(gid, pg_name)
                    if removed:
                        results.append(f"已解除群组 '{gid}' 的权限组 '{pg_name}' 附加")
                    else:
                        results.append(f"群组 '{gid}' 未附加权限组 '{pg_name}'")
                pg_mgr.save()
                await matcher.finish("\n".join(results))
            elif pg_action == "show-bind":
                mapping = pg_mgr.list_group_binds()
                if not mapping:
                    await matcher.finish("没有附加关系")
                lines = ["group → permgroup 映射:"]
                for g, pgns in mapping.items():
                    lines.append(f"  {g} → {', '.join(pgns)}")
                await matcher.finish("\n".join(lines))
            elif pg_action == "list-binds":
                pg_name = parsed.name
                if config.get_permgroup(pg_name) is None:
                    await matcher.finish(f"权限组 '{pg_name}' 不存在")
                bound_groups = pg_mgr.list_permgroup_binds(pg_name)
                if not bound_groups:
                    await matcher.finish(f"权限组 '{pg_name}' 未绑定到任何群组")
                lines = [f"权限组 '{pg_name}' 绑定到的群组:"]
                for g in sorted(bound_groups):
                    lines.append(f"  {g}")
                await matcher.finish("\n".join(lines))
        
        # ── list-groups ────────────────────────────────
        if subcmd == "list-groups":
            groups = sorted(config.group_overrides.keys())
            if not groups:
                await matcher.finish("没有 group 有覆盖配置")
            await matcher.finish("有覆盖配置的 group:\n" + "\n".join(f"  {g}" for g in groups))
        
        # ── list ────────────────────────────────────────
        if subcmd == "list":
            if group is None:
                await matcher.finish("请指定 -g 或 -p 参数")
            cfg = config.get(group)
            overrides_obj = config.group_overrides.get(group) if group != "global" else None
            lines = [f"配置项 ({group}):"]
            for field in config_class.model_fields:
                val = getattr(cfg, field)
                is_overridden = overrides_obj is not None and getattr(overrides_obj, field, None) is not None
                marker = " *" if is_overridden else ""
                source = "(group)" if is_overridden else "(global/class)"
                lines.append(f"  {field}: {val!r}{marker}  {source}")
            await matcher.finish("\n".join(lines))
        
        # ── get ─────────────────────────────────────────
        if subcmd == "get":
            if group is None:
                await matcher.finish("请指定 -g 或 -p 参数")
            field = parsed.field
            if field not in config_class.model_fields:
                await matcher.finish(f"无效字段: {field}")
            val = config.get_value(group, field)
            overrides_obj = config.group_overrides.get(group) if group != "global" else None
            ov_val = getattr(overrides_obj, field, None) if overrides_obj is not None else None
            source = "group" if ov_val is not None else "global/class"
            await matcher.finish(f"{group} 的 {field} = {val!r} ({source})")
        
        # ── set ─────────────────────────────────────────
        if subcmd == "set":
            if group is None:
                await matcher.finish("请指定 -g 或 -p 参数")
            field = parsed.field
            raw_val = parsed.value
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