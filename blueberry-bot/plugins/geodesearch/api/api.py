"""Geode Index API 调用封装。

API 文档: https://api.geode-sdk.org
统一响应格式: {"error": "", "payload": ...}，出错时 error 为字符串、payload 为 ""。

所有函数返回 (结果, 错误信息)，成功时错误信息为 None。
"""

import httpx
from nonebot import logger, get_plugin_config
from pydantic import BaseModel

from .models import Mod, ModSearchResult, Version, VersionListResult
from .search_args import ModSearchArgs, Platform

GEODE_ENDPOINT_BASE = "https://api.geode-sdk.org"

_HEADERS = {
    "User-Agent": "",
    "accept": "application/json",
}


class Config(BaseModel):
    geode_endpoint_base: str = GEODE_ENDPOINT_BASE


try:
    plugin_cfg = get_plugin_config(Config)
except Exception:
    plugin_cfg = Config()

GEODE_ENDPOINT_BASE = plugin_cfg.geode_endpoint_base


async def _request(path: str, params: dict | None = None):
    """发起 GET 请求并解开 {"error","payload"} 包装。

    返回 (payload, error)。网络错误 / 非 200 / API 返回 error 时 payload 为 None，
    error 为错误消息（响应体截断到 200 字符）。
    """
    url = GEODE_ENDPOINT_BASE + path
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=_HEADERS, params=params)
        except httpx.HTTPError as e:
            logger.error(f"Geode API 请求失败 {url}: {e}")
            return None, f"{type(e).__name__}: {e}"
    if resp.status_code != 200:
        logger.error(f"HTTP {resp.status_code}: {resp.text[:200]}")
        return None, f"HTTP {resp.status_code}: {resp.text[:200]}"
    try:
        body = resp.json()
    except ValueError as e:
        logger.error(f"响应解析失败: {e}\n{resp.text[:200]}")
        return None, f"响应解析失败: {e}"
    if body.get("error"):
        return None, str(body["error"])
    return body.get("payload"), None


async def searchMods_async(
    query: str | None = None,
    page: int = 1,
    per_page: int = 10,
    developer: str | None = None,
    tags: str | list[str] | None = None,
    gd: str | None = None,
    geode: str | None = None,
    platform: Platform | str | None = None,
):
    """搜索 mod。

    :param query: 关键词（匹配 mod id / 名称 / 描述）
    :param developer: 按开发者用户名过滤
    :param tags: 按标签过滤，字符串逗号分隔或列表，如 "utility,api"
    :param gd: 按 GD 版本过滤
    :param geode: 按 Geode 版本过滤
    :param platform: 见 Platform 枚举
    """
    args = ModSearchArgs()
    args.page = page
    args.per_page = per_page
    args.query = query
    args.developer = developer
    args.tags = tags
    args.gd = gd
    args.geode = geode
    args.platform = platform
    return await searchModsWithArgs_async(args)


async def searchModsWithArgs_async(args: ModSearchArgs):
    """使用 ModSearchArgs 搜索 mod。"""
    payload, err = await _request("/v1/mods", args.getData())
    if payload is None:
        return None, err
    return ModSearchResult.from_dict(payload), None


async def getMod_async(mod_id: str):
    """获取 mod 详情（含全部内嵌版本、about、changelog）。"""
    payload, err = await _request(f"/v1/mods/{mod_id}")
    if payload is None:
        return None, err
    return Mod.from_dict(payload), None


async def getModVersions_async(mod_id: str, page: int = 1, per_page: int = 10):
    """获取 mod 的版本列表（分页，含依赖 / 冲突信息）。"""
    payload, err = await _request(
        f"/v1/mods/{mod_id}/versions", {"page": page, "per_page": per_page}
    )
    if payload is None:
        return None, err
    return VersionListResult.from_dict(payload), None


async def getModVersion_async(mod_id: str, version: str):
    """获取 mod 的单个版本详情（含依赖 / 冲突信息、开发者、标签）。"""
    payload, err = await _request(f"/v1/mods/{mod_id}/versions/{version}")
    if payload is None:
        return None, err
    return Version.from_dict(payload), None


def getModDownloadUrl(mod_id: str, version: str) -> str:
    """返回版本下载链接（302 重定向到 .geode 文件）。"""
    return f"{GEODE_ENDPOINT_BASE}/v1/mods/{mod_id}/versions/{version}/download"


def getModIconUrl(mod_id: str, version: str | None = None) -> str:
    """返回 mod 图标 URL（PNG）。

    version 可选；不传或传无效版本时返回最新版图标。
    """
    url = f"{GEODE_ENDPOINT_BASE}/v1/mods/{mod_id}/logo"
    return f"{url}?version={version}" if version else url


async def getModIcon_async(mod_id: str, version: str | None = None):
    """下载 mod 图标，返回 (png_bytes, error)。

    mod 不存在时返回 (None, "HTTP 404")。
    """
    url = getModIconUrl(mod_id, version)
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            resp = await client.get(url, headers=_HEADERS)
        except httpx.HTTPError as e:
            logger.error(f"Geode API 请求失败 {url}: {e}")
            return None, f"{type(e).__name__}: {e}"
    if resp.status_code != 200:
        return None, f"HTTP {resp.status_code}"
    return resp.content, None