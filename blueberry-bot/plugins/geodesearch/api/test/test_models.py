import pytest
from datetime import datetime, timezone
from plugins.geodesearch.api.models import (
    Dependency,
    Developer,
    Mod,
    ModLinks,
    ModSearchResult,
    Version,
    VersionListResult,
)

MOD_DATA = {
    "id": "geode.node-ids",
    "repository": None,
    "featured": False,
    "download_count": 13980455,
    "developers": [
        {"id": 3, "username": "geode-sdk", "display_name": "Geode Team", "is_owner": True},
        {"id": 1, "username": "fleeym", "display_name": "Fleym", "is_owner": False},
        {"id": 2, "username": "matcool", "display_name": "mat", "is_owner": False},
    ],
    "versions": [
        {
            "name": "Node IDs",
            "description": "Standard node IDs to be used by other mods.",
            "version": "1.24.0-beta.1",
            "download_link": "https://api.geode-sdk.org/v1/mods/geode.node-ids/versions/1.24.0-beta.1/download",
            "hash": "64f87d56f8e6ad667c79690fc2846642dacdb6a3f9d67f279f023debcdd77fb5",
            "geode": "6.0.0-beta.1",
            "download_count": 120775,
            "early_load": False,
            "requires_patching": False,
            "api": False,
            "mod_id": "geode.node-ids",
            "gd": {"win": "2.2091", "android32": "2.2091"},
            "status": "accepted",
            "created_at": "2026-11-21T09:30:33Z",
            "updated_at": "2026-11-21T09:30:33Z",
        }
    ],
    "tags": [],
    "about": "# Node IDs",
    "changelog": "# Node IDs Changelog",
    "created_at": "2024-06-18T23:27:55Z",
    "updated_at": "2026-11-21T09:30:33Z",
    "links": {
        "community": None,
        "homepage": None,
        "source": "https://github.com/geode-sdk/NodeIDs",
    },
}


class TestDeveloper:
    def test_from_dict(self):
        dev = Developer.from_dict({"id": 8, "username": "coopeeo", "display_name": "august", "is_owner": True})
        assert dev.id == 8
        assert dev.username == "coopeeo"
        assert dev.is_owner is True
        assert str(dev) == "august"

    def test_str_fallback_to_username(self):
        dev = Developer.from_dict({"username": "coopeeo", "display_name": ""})
        assert str(dev) == "coopeeo"


class TestDependency:
    def test_dependency(self):
        dep = Dependency.from_dict(
            {"mod_id": "geode.node-ids", "version": "=1.24.0-beta.1", "importance": "required", "required": True}
        )
        assert dep.mod_id == "geode.node-ids"
        assert dep.is_dependency is True
        assert dep.is_incompatibility is False

    def test_incompatibility(self):
        dep = Dependency.from_dict(
            {"mod_id": "beat.pack-installer", "version": "<2.1.2", "importance": "breaking", "breaking": True}
        )
        assert dep.is_dependency is False
        assert dep.is_incompatibility is True


class TestVersion:
    def test_from_dict(self):
        ver = Version.from_dict(MOD_DATA["versions"][0])
        assert ver.version == "1.24.0-beta.1"
        assert ver.geode == "6.0.0-beta.1"
        assert ver.gd["win"] == "2.2091"
        assert ver.dependencies == []
        assert ver.incompatibilities == []
        assert str(ver) == "Node IDs v1.24.0-beta.1"

    def test_load_dependencies(self):
        data = dict(MOD_DATA["versions"][0])
        data["dependencies"] = [{"mod_id": "geode.node-ids", "version": "=1.24.0", "importance": "required"}]
        data["incompatibilities"] = [{"mod_id": "beat.click_sounds_lite", "version": ">=1.0.0", "importance": "conflicting"}]
        ver = Version.from_dict(data)
        assert isinstance(ver.dependencies[0], Dependency)
        assert ver.dependencies[0].mod_id == "geode.node-ids"
        assert ver.incompatibilities[0].is_incompatibility is True

    def test_datetime(self):
        ver = Version.from_dict(MOD_DATA["versions"][0])
        assert isinstance(ver.created_datetime, datetime)
        assert ver.created_datetime == datetime(2026, 11, 21, 9, 30, 33, tzinfo=timezone.utc)
        assert ver.updated_datetime == datetime(2026, 11, 21, 9, 30, 33, tzinfo=timezone.utc)

    def test_datetime_invalid(self):
        data = dict(MOD_DATA["versions"][0])
        data["created_at"] = ""
        data["updated_at"] = "not-a-date"
        ver = Version.from_dict(data)
        assert ver.created_datetime is None
        assert ver.updated_datetime is None


class TestMod:
    def test_from_dict(self):
        mod = Mod.from_dict(MOD_DATA)
        assert mod.id == "geode.node-ids"
        assert mod.download_count == 13980455
        assert mod.tags == []
        assert mod.about == "# Node IDs"
        assert isinstance(mod.developers[0], Developer)
        assert isinstance(mod.versions[0], Version)
        assert isinstance(mod.links, ModLinks)
        assert mod.links.source == "https://github.com/geode-sdk/NodeIDs"

    def test_owner(self):
        mod = Mod.from_dict(MOD_DATA)
        owner = mod.owner
        assert owner is not None
        assert owner.username == "geode-sdk"

    def test_owner_fallback(self):
        data = dict(MOD_DATA)
        data["developers"] = [{"id": 1, "username": "a", "display_name": "A", "is_owner": False}]
        mod = Mod.from_dict(data)
        owner = mod.owner
        assert owner is not None
        assert owner.username == "a"

    def test_latest_version(self):
        mod = Mod.from_dict(MOD_DATA)
        latest = mod.latest_version
        assert latest is not None
        assert latest.version == "1.24.0-beta.1"

    def test_latest_version_empty(self):
        data = dict(MOD_DATA)
        data["versions"] = []
        assert Mod.from_dict(data).latest_version is None

    def test_links_none(self):
        data = dict(MOD_DATA)
        data["links"] = None
        assert Mod.from_dict(data).links is None

    def test_datetime(self):
        mod = Mod.from_dict(MOD_DATA)
        assert isinstance(mod.created_datetime, datetime)
        assert isinstance(mod.updated_datetime, datetime)
        assert mod.updated_datetime == datetime(2026, 11, 21, 9, 30, 33, tzinfo=timezone.utc)

    def test_datetime_invalid(self):
        data = dict(MOD_DATA)
        data["created_at"] = ""
        data["updated_at"] = ""
        mod = Mod.from_dict(data)
        assert mod.created_datetime is None
        assert mod.updated_datetime is None

    def test_str(self):
        mod = Mod.from_dict(MOD_DATA)
        assert str(mod) == "geode.node-ids by Geode Team"

    def test_ignore_unknown_field(self):
        data = dict(MOD_DATA)
        data["unknown_field"] = "x"
        mod = Mod.from_dict(data)
        assert not hasattr(mod, "unknown_field")

    def test_to_dict_roundtrip(self):
        mod = Mod.from_dict(MOD_DATA)
        back = mod.to_dict()
        assert back["id"] == "geode.node-ids"
        assert back["links"]["source"] == "https://github.com/geode-sdk/NodeIDs"
        assert back["versions"][0]["version"] == "1.24.0-beta.1"
        assert back["developers"][0]["username"] == "geode-sdk"


class TestResults:
    def test_mod_search_result(self):
        result = ModSearchResult.from_dict({"data": [MOD_DATA], "count": 10})
        assert result.count == 10
        assert isinstance(result.data[0], Mod)

    def test_mod_search_result_empty(self):
        result = ModSearchResult.from_dict({"data": [], "count": 0})
        assert result.data == []
        assert result.count == 0

    def test_version_list_result(self):
        result = VersionListResult.from_dict({"data": [MOD_DATA["versions"][0]], "count": 38})
        assert result.count == 38
        assert isinstance(result.data[0], Version)
