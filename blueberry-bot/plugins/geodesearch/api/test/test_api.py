import pytest
from plugins.geodesearch.api import (
    searchMods_async,
    searchModsWithArgs_async,
    searchModsCached_async,
    getMod_async,
    getModVersions_async,
    getModVersion_async,
    getModDownloadUrl,
    getModIcon_async,
    getModIconCached_async,
    getModIconUrl,
)
from plugins.geodesearch.api.search_args import ModSearchArgs, Platform

MOD_ID = "geode.node-ids"


@pytest.mark.asyncio
async def test_search_mods():
    result, err = await searchMods_async(query="click", per_page=2)
    assert err is None
    assert result is not None
    assert result.count > 0
    assert len(result.data) <= 2
    print(result.count, [m.id for m in result.data])


@pytest.mark.asyncio
async def test_search_mods_pagination():
    page1, err = await searchMods_async(query="click", page=1, per_page=1)
    assert err is None
    assert page1 is not None
    page2, err = await searchMods_async(query="click", page=2, per_page=1)
    assert err is None
    assert page2 is not None
    assert page1.data[0].id != page2.data[0].id


@pytest.mark.asyncio
async def test_search_mods_with_args():
    args = ModSearchArgs()
    args.query = "click"
    args.per_page = 2
    result, err = await searchModsWithArgs_async(args)
    assert err is None
    assert result is not None
    assert result.count > 0
    assert len(result.data) <= 2
    print(result.count, [m.id for m in result.data])


@pytest.mark.asyncio
async def test_search_mods_with_args_developer():
    args = ModSearchArgs()
    args.developer = "geode-sdk"
    args.per_page = 5
    result, err = await searchModsWithArgs_async(args)
    assert err is None
    assert result is not None
    assert result.count > 0
    assert all(any(d.username == "geode-sdk" for d in m.developers) for m in result.data)
    print(result.count, [m.id for m in result.data])


@pytest.mark.asyncio
async def test_search_mods_with_args_tags_and_platform():
    args = ModSearchArgs()
    args.tags = ["utility"]
    args.platform = Platform.WIN
    args.per_page = 2
    result, err = await searchModsWithArgs_async(args)
    assert err is None
    assert result is not None
    assert result.count > 0
    print(result.count, [m.id for m in result.data])


@pytest.mark.asyncio
async def test_get_mod():
    mod, err = await getMod_async(MOD_ID)
    assert err is None
    assert mod is not None
    assert mod.id == MOD_ID
    assert mod.developers
    assert mod.owner is not None
    assert mod.latest_version is not None
    assert mod.latest_version.version
    print(mod, mod.tags, mod.owner, mod.latest_version)


@pytest.mark.asyncio
async def test_get_mod_not_found():
    mod, err = await getMod_async("geode.loader")
    assert mod is None
    assert err is not None
    print(err)


@pytest.mark.asyncio
async def test_get_mod_versions():
    versions, err = await getModVersions_async(MOD_ID, per_page=2)
    assert err is None
    assert versions is not None
    assert versions.count > 0
    assert len(versions.data) <= 2
    print(versions.count, [v.version for v in versions.data])


@pytest.mark.asyncio
async def test_get_mod_version():
    versions, err = await getModVersions_async(MOD_ID, per_page=1)
    assert err is None
    assert versions is not None
    latest = versions.data[0].version

    version, err = await getModVersion_async(MOD_ID, latest)
    assert err is None
    assert version is not None
    assert version.version == latest
    assert version.mod_id == MOD_ID
    assert version.geode
    assert version.gd
    print(version, version.geode, version.gd)


def test_get_mod_download_url():
    url = getModDownloadUrl(MOD_ID, "1.23.3")
    assert url.endswith(f"/v1/mods/{MOD_ID}/versions/1.23.3/download")


def test_get_mod_icon_url():
    url = getModIconUrl(MOD_ID)
    assert url.endswith(f"/v1/mods/{MOD_ID}/logo")
    assert "?" not in url


def test_get_mod_icon_url_with_version():
    url = getModIconUrl(MOD_ID, "1.23.3")
    assert url.endswith(f"/v1/mods/{MOD_ID}/logo?version=1.23.3")


@pytest.mark.asyncio
async def test_get_mod_icon():
    png, err = await getModIcon_async(MOD_ID)
    assert err is None
    assert png is not None
    assert png.startswith(b"\x89PNG")
    print(len(png))


@pytest.mark.asyncio
async def test_get_mod_icon_with_version():
    versions, err = await getModVersions_async(MOD_ID, per_page=1)
    assert err is None
    assert versions is not None
    png, err = await getModIcon_async(MOD_ID, versions.data[0].version)
    assert err is None
    assert png is not None
    assert png.startswith(b"\x89PNG")


@pytest.mark.asyncio
async def test_get_mod_icon_not_found():
    png, err = await getModIcon_async("geode.loader")
    assert png is None
    assert err is not None
    print(err)


@pytest.mark.asyncio
async def test_search_mods_cached():
    args = ModSearchArgs()
    args.query = "node"
    first, err = await searchModsCached_async(args)
    assert err is None
    assert first is not None

    # 相同参数应命中缓存，返回同一对象
    second, err = await searchModsCached_async(args)
    assert err is None
    assert second is first


@pytest.mark.asyncio
async def test_get_mod_icon_cached():
    first, err = await getModIconCached_async(MOD_ID)
    assert err is None
    assert first is not None

    second, err = await getModIconCached_async(MOD_ID)
    assert err is None
    assert second is first


@pytest.mark.asyncio
async def test_error_not_cached():
    """错误结果不应被缓存 —— 不存在 mod 的请求每次都会重新发起。"""
    from plugins.geodesearch.api import api

    calls = 0
    original = api._request

    async def counting_request(*args, **kwargs):
        nonlocal calls
        calls += 1
        return await original(*args, **kwargs)

    api._request = counting_request
    try:
        first, err1 = await api.getMod_async("geode.loader")
        second, err2 = await api.getMod_async("geode.loader")
    finally:
        api._request = original

    assert first is None and err1 is not None
    assert second is None and err2 is not None
    assert calls == 2
