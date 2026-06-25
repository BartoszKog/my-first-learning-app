from learning_app.ui.components.tiles_container import TilesContainer


class BodyRegistry:
    _home: TilesContainer | None = None
    _export: TilesContainer | None = None

    @classmethod
    def set_home(cls, body: TilesContainer):
        cls._home = body

    @classmethod
    def get_home(cls) -> TilesContainer:
        assert cls._home is not None, "Home body is not set"
        return cls._home

    @classmethod
    def has_home(cls) -> bool:
        return cls._home is not None

    @classmethod
    def set_export(cls, body: TilesContainer):
        cls._export = body

    @classmethod
    def get_export(cls) -> TilesContainer:
        assert cls._export is not None, "Export body is not set"
        return cls._export

    @classmethod
    def has_export(cls) -> bool:
        return cls._export is not None
