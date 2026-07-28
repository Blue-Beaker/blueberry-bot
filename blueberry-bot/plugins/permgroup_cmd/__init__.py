"""permgroup 全局命令 — 管理权限组及其与群组的绑定关系。

独立于具体 GroupConfig 实例，所有权限组配置和映射全局共享。
需要 SUPERUSER 权限。
"""

from nonebot import on_command, logger, require
from nonebot.adapters import Bot, Event, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.exception import FinishedException

require("bbot_api")

from ..bbot_api import get_group_id
from ..bbot_api.argparse import ArgParser, ArgumentError, ShowHelp as ArgShowHelp
from ..bbot_api.group_config.permgroup_manager import get_permgroup_manager
from ..bbot_api.group_config import GroupConfig, ConfigItem


# ── 指令定义 ──────────────────────────────────────────

permgroup_cmd = on_command("permgroup", permission=SUPERUSER, priority=1)

# ── 构建解析器 ───────────────────────────────────────

parser = ArgParser(command_name="permgroup", add_help=False)
sub = parser.add_subparsers(dest="action", metavar="<操作>")

p_create = sub.add_parser("create", help="创建权限组", add_help=False)
p_create.add_argument("name", help="权限组名")

p_delete = sub.add_parser("delete", help="删除权限组", add_help=False)
p_delete.add_argument("name", help="权限组名")

sub.add_parser("list", help="列出所有权限组", add_help=False)

p_bind = sub.add_parser("bind", help="将权限组附加到群组", add_help=False)
p_bind.add_argument("name", help="权限组名")
p_bind.add_argument("groups", nargs="*", metavar="<group>", help="群组 ID（不指定时默认当前群）")

p_unbind = sub.add_parser("unbind", help="解除群组的权限组附加", add_help=False)
p_unbind.add_argument("name", help="权限组名")
p_unbind.add_argument("groups", nargs="*", metavar="<group>", help="群组 ID（不指定时默认当前群）")

p_show = sub.add_parser("show-bind", help="查看当前或指定群组的权限组", add_help=False)
p_show.add_argument("group", nargs="?", default=None, metavar="<group>", help="群组 ID（不指定时默认当前群）")

p_list_binds = sub.add_parser("list-binds", help="查看权限组绑定到的所有群组", add_help=False)
p_list_binds.add_argument("name", help="权限组名")

help_text = (
    "permgroup create <name>\n"
    "permgroup delete <name>\n"
    "permgroup list\n"
    "permgroup bind <name> [<group> ...]\n"
    "permgroup unbind <name> [<group> ...]\n"
    "permgroup show-bind [<group>]\n"
    "permgroup list-binds <name>"
)


def _resolve_current_group(event: Event) -> str:
    """从事件解析当前群组 ID。"""
    gid = get_group_id(event)
    if gid == "private":
        raise ValueError("私聊中必须指定群组 ID")
    return gid


@permgroup_cmd.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    raw_text = args.extract_plain_text().strip()
    if not raw_text:
        await permgroup_cmd.finish(help_text)

    try:
        parsed = parser.parse_args(raw_text.split())
    except (ArgumentError, ArgShowHelp) as e:
        await permgroup_cmd.finish(str(e))

    action = parsed.action
    pg_mgr = get_permgroup_manager()

    try:
        if action == "create":
            pg_name = parsed.name
            # 检查是否已存在同名权限组（扫描所有 GroupConfig 不太现实，
            # 这里只确保 permgroup_groups_map 中有占位）
            if pg_name in pg_mgr.permgroup_groups_map:
                await permgroup_cmd.finish(f"权限组 '{pg_name}' 已存在")
            # 在映射中注册（实际配置项由各 GroupConfig 按需创建）
            pg_mgr.permgroup_groups_map.setdefault(pg_name, [])
            pg_mgr.save()
            await permgroup_cmd.finish(f"已创建权限组: {pg_name}")

        elif action == "delete":
            pg_name = parsed.name
            pg_mgr.clear_permgroup_binds(pg_name)
            pg_mgr.save()
            # 注意：各 GroupConfig 中的 permgroup_<name> 配置项不会自动删除，
            # 需要管理员自行用对应配置命令清理
            await permgroup_cmd.finish(f"已删除权限组映射: {pg_name}")

        elif action == "list":
            names = sorted(pg_mgr.permgroup_groups_map.keys())
            if not names:
                await permgroup_cmd.finish("没有权限组")
            await permgroup_cmd.finish("权限组:\n" + "\n".join(f"  {n}" for n in names))

        elif action == "bind":
            pg_name = parsed.name
            group_ids = parsed.groups
            if not group_ids:
                try:
                    group_ids = [_resolve_current_group(event)]
                except ValueError as e:
                    await permgroup_cmd.finish(str(e))
            for gid in group_ids:
                pg_mgr.bind(gid, pg_name)
            pg_mgr.save()
            if len(group_ids) == 1:
                await permgroup_cmd.finish(f"已将权限组 '{pg_name}' 附加到群组 '{group_ids[0]}'")
            else:
                await permgroup_cmd.finish(f"已将权限组 '{pg_name}' 附加到 {len(group_ids)} 个群组: {', '.join(group_ids)}")

        elif action == "unbind":
            pg_name = parsed.name
            group_ids = parsed.groups
            if not group_ids:
                try:
                    group_ids = [_resolve_current_group(event)]
                except ValueError as e:
                    await permgroup_cmd.finish(str(e))
            results = []
            for gid in group_ids:
                removed = pg_mgr.unbind(gid, pg_name)
                if removed:
                    results.append(f"已解除群组 '{gid}' 的权限组 '{pg_name}' 附加")
                else:
                    results.append(f"群组 '{gid}' 未附加权限组 '{pg_name}'")
            pg_mgr.save()
            await permgroup_cmd.finish("\n".join(results))

        elif action == "show-bind":
            gid = parsed.group
            if gid is None:
                try:
                    gid = _resolve_current_group(event)
                except ValueError as e:
                    await permgroup_cmd.finish(str(e))
            pgns = pg_mgr.get_group_permgroups(gid)
            if not pgns:
                await permgroup_cmd.finish(f"群组 '{gid}' 未附加任何权限组")
            await permgroup_cmd.finish(
                f"群组 '{gid}' 的权限组:\n" +
                "\n".join(f"  {n}" for n in pgns)
            )

        elif action == "list-binds":
            pg_name = parsed.name
            bound_groups = pg_mgr.list_permgroup_binds(pg_name)
            if not bound_groups:
                await permgroup_cmd.finish(f"权限组 '{pg_name}' 未绑定到任何群组")
            lines = [f"权限组 '{pg_name}' 绑定到的群组:"]
            for g in sorted(bound_groups):
                lines.append(f"  {g}")
            await permgroup_cmd.finish("\n".join(lines))

        else:
            await permgroup_cmd.finish(f"未知操作: {action}")

    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"permgroup 错误: {e}")
        await permgroup_cmd.finish(f"错误: {e}")
