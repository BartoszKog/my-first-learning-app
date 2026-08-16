"""Store shared tile bodies used by home and export screens (and in-place search)."""

from learning_app.ui.components.tiles_container import TilesContainer


class BodyRegistry:
    """Process-wide registry for reusable home and export tile containers."""

    _home: TilesContainer | None = None
    _export: TilesContainer | None = None

    @classmethod
    def set_home(cls, body: TilesContainer):
        """Register the tile container used by the home route.

        Args:
            body: Home tile container to retain.
        """
        cls._home = body

    @classmethod
    def get_home(cls) -> TilesContainer:
        """Return the registered home tile container.

        Returns:
            The current home tile container.

        Raises:
            AssertionError: If no home body has been registered.
        """
        assert cls._home is not None, "Home body is not set"
        return cls._home

    @classmethod
    def has_home(cls) -> bool:
        """Return whether a home tile container is registered.

        Returns:
            ``True`` when a home body is available.
        """
        return cls._home is not None

    @classmethod
    def set_export(cls, body: TilesContainer):
        """Register the tile container used by the export workflow.

        Args:
            body: Export tile container to retain.
        """
        cls._export = body

    @classmethod
    def get_export(cls) -> TilesContainer:
        """Return the registered export tile container.

        Returns:
            The current export tile container.

        Raises:
            AssertionError: If no export body has been registered.
        """
        assert cls._export is not None, "Export body is not set"
        return cls._export

    @classmethod
    def has_export(cls) -> bool:
        """Return whether an export tile container is registered.

        Returns:
            ``True`` when an export body is available.
        """
        return cls._export is not None
