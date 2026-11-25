from typing import Any, ClassVar, get_type_hints
from typing_extensions import Self


class _GeodeModel:
    """Geode Index 数据模型的通用加载基类。

    与 gd_api 的 BaseAdaptingModel 不同，这里不做类型强转：Geode API 返回的字段
    类型已经稳定，直接按字段名赋值即可；仅忽略未知字段、缺失字段保留类默认值。
    """

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        inst = cls()
        inst.load_dict(data)
        return inst

    def load_dict(self, data: dict) -> Self:
        hints = get_type_hints(type(self))
        for k, v in data.items():
            if k not in hints:
                continue
            setattr(self, k, v)
        return self

    def to_dict(self) -> dict:
        data: dict[str, Any] = {}
        for k in get_type_hints(type(self)):
            v = getattr(self, k, None)
            if v is None:
                continue
            if isinstance(v, _GeodeModel):
                v = v.to_dict()
            elif isinstance(v, list):
                v = [i.to_dict() if isinstance(i, _GeodeModel) else i for i in v]
            data[k] = v
        return data

    def __repr__(self) -> str:
        return f"[{self.__class__.__name__}]{self.__dict__}"


class Developer(_GeodeModel):
    """mod 开发者。"""

    id: int = -1
    username: str = ""
    display_name: str = ""
    is_owner: bool = False

    def __str__(self) -> str:
        return self.display_name or self.username


class Dependency(_GeodeModel):
    """版本依赖 / 冲突关系。

    importance 取值: required / recommended / suggested / breaking / conflicting
    """

    mod_id: str = ""
    version: str = ""
    importance: str = ""
    required: bool = False
    breaking: bool = False

    @property
    def is_dependency(self) -> bool:
        return self.importance in ("required", "recommended", "suggested")

    @property
    def is_incompatibility(self) -> bool:
        return self.importance in ("breaking", "conflicting")


class ModLinks(_GeodeModel):
    """mod 相关链接，字段可能为 None。"""

    community: str | None = None
    homepage: str | None = None
    source: str | None = None


class Version(_GeodeModel):
    """mod 的一个发布版本。

    注意: gd 字段是按平台的 GD 版本映射，如 {"win": "2.2091", ...}。
    """

    name: str = ""
    description: str = ""
    version: str = ""
    download_link: str = ""
    hash: str = ""
    geode: str = ""
    download_count: int = 0
    early_load: bool = False
    requires_patching: bool = False
    api: bool = False
    mod_id: str = ""
    gd: dict[str, str] = {}
    status: str = ""
    dependencies: list[Dependency] = []
    incompatibilities: list[Dependency] = []
    created_at: str = ""
    updated_at: str = ""

    def load_dict(self, data: dict) -> Self:
        super().load_dict(data)
        self.dependencies = [
            Dependency.from_dict(d) for d in data.get("dependencies") or []
        ]
        self.incompatibilities = [
            Dependency.from_dict(d) for d in data.get("incompatibilities") or []
        ]
        return self

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class Mod(_GeodeModel):
    """Geode Index 中的一个 mod。

    搜索接口返回的 about / changelog 恒为 None，只有详情接口才有内容。
    """

    id: str = ""
    repository: str | None = None
    featured: bool = False
    download_count: int = 0
    developers: list[Developer] = []
    versions: list[Version] = []
    tags: list[str] = []
    about: str | None = None
    changelog: str | None = None
    links: ModLinks | None = None
    created_at: str = ""
    updated_at: str = ""

    def load_dict(self, data: dict) -> Self:
        super().load_dict(data)
        self.developers = [Developer.from_dict(d) for d in data.get("developers") or []]
        self.versions = [Version.from_dict(v) for v in data.get("versions") or []]
        links = data.get("links")
        self.links = ModLinks.from_dict(links) if links else None
        return self

    @property
    def latest_version(self) -> Version | None:
        return self.versions[0] if self.versions else None

    @property
    def owner(self) -> Developer | None:
        for dev in self.developers:
            if dev.is_owner:
                return dev
        return self.developers[0] if self.developers else None

    def __str__(self) -> str:
        owner = self.owner
        return f"{self.id}" + (f" by {owner}" if owner else "")


class ModSearchResult(_GeodeModel):
    """mod 搜索 / 列表结果。count 为符合条件的总数。"""

    data: list[Mod] = []
    count: int = 0

    def load_dict(self, data: dict) -> Self:
        super().load_dict(data)
        self.data = [Mod.from_dict(m) for m in data.get("data") or []]
        return self


class VersionListResult(_GeodeModel):
    """mod 版本列表结果。count 为版本总数。"""

    data: list[Version] = []
    count: int = 0

    def load_dict(self, data: dict) -> Self:
        super().load_dict(data)
        self.data = [Version.from_dict(v) for v in data.get("data") or []]
        return self
