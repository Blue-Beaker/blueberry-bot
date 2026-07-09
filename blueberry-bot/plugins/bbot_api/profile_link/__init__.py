from nonebot import on_command, logger, get_driver
from nonebot.adapters import Bot, Event, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.exception import FinishedException

from .profile_link import get_profile_link_manager


driver = get_driver()

@driver.on_startup
async def load_profile_links():
    manager = get_profile_link_manager()
    manager.load()
    logger.info(f"已加载 {len(manager.user_links)} 个用户绑定, {len(manager.group_links)} 个群绑定.")

@driver.on_shutdown
async def save_profile_links():
    manager = get_profile_link_manager()
    manager.save()
    logger.info(f"已保存 {len(manager.user_links)} 个用户绑定, {len(manager.group_links)} 个群绑定.")


# ── account 指令 ──────────────────────────────────────

profile_link_cmd = on_command("account", permission=SUPERUSER, priority=1)

@profile_link_cmd.handle()
async def _(bot: Bot, event: Event, args: Message = CommandArg()):
    manager = get_profile_link_manager()
    cmd_args = args.extract_plain_text().strip().split()
    
    if not cmd_args:
        await profile_link_cmd.finish(
            "用法:\n"
            "account create <通用ID> [实际ID ...] - 创建通用用户 ID (可选绑定)\n"
            "account delete <通用ID> - 删除通用用户 ID\n"
            "account list - 列出所有绑定\n"
            "account show <通用ID> - 查看绑定详情\n"
            "account link <通用ID> <实际ID> [实际ID ...] - 批量绑定实际用户 ID\n"
            "account unlink <通用ID> <实际ID> [实际ID ...] - 批量解除用户绑定\n"
            "account create-group <通用ID> [实际群ID ...] - 创建通用群 ID (可选绑定)\n"
            "account delete-group <通用ID> - 删除通用群 ID\n"
            "account link-group <通用ID> <群ID> [群ID ...] - 批量绑定群 ID\n"
            "account unlink-group <通用ID> <群ID> [群ID ...] - 批量解除群绑定"
        )
    
    try:
        action = cmd_args[0]
        
        # ── 用户绑定 ──────────────────────────────────
        
        if action == "create":
            if len(cmd_args) < 2:
                await profile_link_cmd.finish("用法: account create <通用ID> [实际ID ...]")
            name = cmd_args[1]
            manager.create_user_profile(name)
            for raw_id in cmd_args[2:]:
                try:
                    manager.link_user_id(name, raw_id)
                except ValueError as e:
                    await profile_link_cmd.send(f"绑定 '{raw_id}' 失败: {e}")
            manager.save()
            if len(cmd_args) > 2:
                await profile_link_cmd.finish(f"已创建通用用户 ID '{name}' 并绑定了 {len(cmd_args) - 2} 个ID")
            else:
                await profile_link_cmd.finish(f"已创建通用用户 ID: {name}")
        
        elif action == "delete":
            if len(cmd_args) < 2:
                await profile_link_cmd.finish("用法: account delete <通用ID>")
            name = cmd_args[1]
            if manager.delete_user_profile(name):
                manager.save()
                await profile_link_cmd.finish(f"已删除通用用户 ID: {name}")
            else:
                await profile_link_cmd.finish(f"通用用户 ID '{name}' 不存在")
        
        elif action == "link":
            if len(cmd_args) < 3:
                await profile_link_cmd.finish("用法: account link <通用ID> <实际ID> [实际ID ...]")
            name = cmd_args[1]
            linked = []
            errors = []
            for raw_id in cmd_args[2:]:
                try:
                    manager.link_user_id(name, raw_id)
                    linked.append(raw_id)
                except ValueError as e:
                    errors.append(f"'{raw_id}': {e}")
            manager.save()
            msg = ""
            if linked:
                msg += f"已将 {len(linked)} 个ID绑定到 '{name}': {', '.join(linked)}"
            if errors:
                msg += "\n" + "\n".join(errors)
            await profile_link_cmd.finish(msg)
        
        elif action == "unlink":
            if len(cmd_args) < 3:
                await profile_link_cmd.finish("用法: account unlink <通用ID> <实际ID> [实际ID ...]")
            name = cmd_args[1]
            unlinked = []
            errors = []
            for raw_id in cmd_args[2:]:
                try:
                    manager.unlink_user_id(name, raw_id)
                    unlinked.append(raw_id)
                except ValueError as e:
                    errors.append(f"'{raw_id}': {e}")
            manager.save()
            msg = ""
            if unlinked:
                msg += f"已解除 {len(unlinked)} 个ID与 '{name}' 的绑定: {', '.join(unlinked)}"
            if errors:
                msg += "\n" + "\n".join(errors)
            await profile_link_cmd.finish(msg)
        
        # ── 群组绑定 ──────────────────────────────────
        
        elif action == "create-group":
            if len(cmd_args) < 2:
                await profile_link_cmd.finish("用法: account create-group <通用ID> [实际群ID ...]")
            name = cmd_args[1]
            manager.create_group_profile(name)
            for raw_gid in cmd_args[2:]:
                try:
                    manager.link_group_id(name, raw_gid)
                except ValueError as e:
                    await profile_link_cmd.send(f"绑定群 '{raw_gid}' 失败: {e}")
            manager.save()
            if len(cmd_args) > 2:
                await profile_link_cmd.finish(f"已创建通用群 ID '{name}' 并绑定了 {len(cmd_args) - 2} 个群")
            else:
                await profile_link_cmd.finish(f"已创建通用群 ID: {name}")
        
        elif action == "delete-group":
            if len(cmd_args) < 2:
                await profile_link_cmd.finish("用法: account delete-group <通用ID>")
            name = cmd_args[1]
            if manager.delete_group_profile(name):
                manager.save()
                await profile_link_cmd.finish(f"已删除通用群 ID: {name}")
            else:
                await profile_link_cmd.finish(f"通用群 ID '{name}' 不存在")
        
        elif action == "link-group":
            if len(cmd_args) < 3:
                await profile_link_cmd.finish("用法: account link-group <通用ID> <群ID> [群ID ...]")
            name = cmd_args[1]
            linked = []
            errors = []
            for raw_gid in cmd_args[2:]:
                try:
                    manager.link_group_id(name, raw_gid)
                    linked.append(raw_gid)
                except ValueError as e:
                    errors.append(f"'{raw_gid}': {e}")
            manager.save()
            msg = ""
            if linked:
                msg += f"已将 {len(linked)} 个群绑定到 '{name}': {', '.join(linked)}"
            if errors:
                msg += "\n" + "\n".join(errors)
            await profile_link_cmd.finish(msg)
        
        elif action == "unlink-group":
            if len(cmd_args) < 3:
                await profile_link_cmd.finish("用法: account unlink-group <通用ID> <群ID> [群ID ...]")
            name = cmd_args[1]
            unlinked = []
            errors = []
            for raw_gid in cmd_args[2:]:
                try:
                    manager.unlink_group_id(name, raw_gid)
                    unlinked.append(raw_gid)
                except ValueError as e:
                    errors.append(f"'{raw_gid}': {e}")
            manager.save()
            msg = ""
            if unlinked:
                msg += f"已解除 {len(unlinked)} 个群与 '{name}' 的绑定: {', '.join(unlinked)}"
            if errors:
                msg += "\n" + "\n".join(errors)
            await profile_link_cmd.finish(msg)
        
        # ── 查询 ──────────────────────────────────────
        
        elif action == "list":
            lines = []
            if manager.user_links:
                lines.append("用户绑定:")
                for name, p in manager.user_links.items():
                    lines.append(f"  {name}: {len(p.linked_ids)} 个ID")
            if manager.group_links:
                lines.append("群绑定:")
                for name, p in manager.group_links.items():
                    lines.append(f"  {name}: {len(p.linked_ids)} 个群")
            if not lines:
                await profile_link_cmd.finish("暂无绑定记录")
            await profile_link_cmd.finish("\n".join(lines))
        
        elif action == "show":
            if len(cmd_args) < 2:
                await profile_link_cmd.finish("用法: account show <通用ID>")
            name = cmd_args[1]
            user_p = manager.get_user_profile(name)
            group_p = manager.get_group_profile(name)
            if not user_p and not group_p:
                await profile_link_cmd.finish(f"通用 ID '{name}' 不存在")
            lines = []
            if user_p:
                lines.append(f"通用用户 ID: {name}")
                if user_p.linked_ids:
                    for lid in user_p.linked_ids:
                        lines.append(f"  - {lid}")
            if group_p:
                lines.append(f"通用群 ID: {name}")
                if group_p.linked_ids:
                    for gid in group_p.linked_ids:
                        lines.append(f"  - {gid}")
            await profile_link_cmd.finish("\n".join(lines))
        
        else:
            await profile_link_cmd.finish(f"未知操作: {action}")
    
    except FinishedException:
        raise
    except Exception as e:
        logger.error(f"account 错误: {e}")
        await profile_link_cmd.finish(f"错误: {e}")
