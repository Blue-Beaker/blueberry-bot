from plugins.geodesearch.api.search_args import ModSearchArgs, ModStatus, Platform, Sort


class TestPlatform:
    def test_values(self):
        assert Platform.WIN.value == "win"
        assert Platform.ANDROID32.value == "android32"
        assert Platform.ANDROID64.value == "android64"
        assert Platform.MAC_INTEL.value == "mac-intel"
        assert Platform.MAC_ARM.value == "mac-arm"
        assert Platform.IOS.value == "ios"


class TestModStatus:
    def test_values(self):
        assert ModStatus.PENDING.value == "pending"
        assert ModStatus.ACCEPTED.value == "accepted"
        assert ModStatus.REJECTED.value == "rejected"
        assert ModStatus.UNLISTED.value == "unlisted"


class TestSort:
    def test_values(self):
        assert Sort.DOWNLOADS.value == "downloads"
        assert Sort.RECENTLY_UPDATED.value == "recently_updated"
        assert Sort.RECENTLY_PUBLISHED.value == "recently_published"
        assert Sort.OLDEST.value == "oldest"
        assert Sort.NAME.value == "name"
        assert Sort.NAME_REVERSE.value == "name_reverse"
        assert Sort.RANDOM.value == "random"


class TestModSearchArgs:
    def test_defaults(self):
        args = ModSearchArgs()
        assert args.page == 1
        assert args.per_page == 10
        assert args.query is None
        assert args.developer is None
        assert args.tags is None
        assert args.gd is None
        assert args.geode is None
        assert args.platform is None

    def test_get_data_defaults(self):
        assert ModSearchArgs().getData() == {"page": 1, "per_page": 10}

    def test_get_data_skips_none(self):
        args = ModSearchArgs()
        args.query = "click"
        assert args.getData() == {"page": 1, "per_page": 10, "query": "click"}

    def test_get_data_platform_enum(self):
        args = ModSearchArgs()
        args.platform = Platform.MAC_ARM
        assert args.getData()["platform"] == "mac-arm"

    def test_get_data_platform_str(self):
        args = ModSearchArgs()
        args.platform = "win"
        assert args.getData()["platform"] == "win"

    def test_get_data_tags_list(self):
        args = ModSearchArgs()
        args.tags = ["utility", "api"]
        assert args.getData()["tags"] == "utility,api"

    def test_get_data_tags_str(self):
        args = ModSearchArgs()
        args.tags = "utility,api"
        assert args.getData()["tags"] == "utility,api"

    def test_get_data_full(self):
        args = ModSearchArgs()
        args.page = 2
        args.per_page = 5
        args.query = "node"
        args.developer = "geode-sdk"
        args.tags = ["utility"]
        args.gd = "2.2091"
        args.geode = "6.0.0"
        args.platform = Platform.WIN
        args.featured = True
        args.status = ModStatus.ACCEPTED
        args.sort = Sort.DOWNLOADS
        assert args.getData() == {
            "page": 2,
            "per_page": 5,
            "query": "node",
            "developer": "geode-sdk",
            "tags": "utility",
            "gd": "2.2091",
            "geode": "6.0.0",
            "platform": "win",
            "featured": "true",
            "status": "accepted",
            "sort": "downloads",
        }

    def test_get_data_featured_false(self):
        args = ModSearchArgs()
        args.featured = False
        assert args.getData()["featured"] == "false"

    def test_get_data_status_str(self):
        args = ModSearchArgs()
        args.status = "accepted"
        assert args.getData()["status"] == "accepted"

    def test_get_data_sort_str(self):
        args = ModSearchArgs()
        args.sort = "random"
        assert args.getData()["sort"] == "random"

    def test_equality_ignores_enum_vs_str(self):
        a = ModSearchArgs()
        a.sort = Sort.NAME
        b = ModSearchArgs()
        b.sort = "name"
        assert a == b
        assert hash(a) == hash(b)
