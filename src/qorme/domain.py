import logging
from typing import TYPE_CHECKING, ClassVar

from qorme.utils.wrapper import Wrapper

if TYPE_CHECKING:
    from qorme.deps import Deps
    from qorme.utils.config import Config

logger = logging.getLogger(__name__)


class Domain:
    """
    Base class for all tracking domains.
    Each domain is responsible for tracking a specific aspect of the system
    (e.g. database queries, HTTP requests, relational operations...).
    It does so by installing method wrappers and/or registering event handlers.
    """

    # Name of the domain, used for logging and registration purposes.
    # Should be overridden by subclasses.
    name: ClassVar[str] = ""

    __slots__ = "deps", "config", "enabled", "_wrapper"

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        if "__slots__" not in cls.__dict__:
            logger.warning("%s domain doesn't define __slots__", cls)

    def __init__(self, deps: "Deps", config: "Config") -> None:
        self.deps = deps
        self.config = config
        self.enabled = False
        self._wrapper: Wrapper | None = None
        self.setup()

    def setup(self): ...

    @property
    def wrapper(self) -> Wrapper:
        if not self._wrapper:
            self._wrapper = Wrapper()
        return self._wrapper

    def register_event_handlers(self) -> None:
        """Register event handlers needed for this tracking domain."""
        ...

    def unregister_event_handlers(self) -> None:
        """Unregister event handlers."""
        ...

    def install_wrappers(self) -> None:
        """
        Install all required wrappers for this tracking implementation.

        This method should be implemented by subclasses to set up all necessary
        method wrapper when tracking is enabled. It is called automatically
        during the enable() process.
        """
        ...

    def uninstall_wrappers(self) -> None:
        """
        Remove installed wrappers, if any.

        This method removes all tracking wrappers that were previously installed,
        restoring the original methods. It is called automatically during the
        disable() process.
        """
        if wrapper := self._wrapper:
            wrapper.clear()

    def enable(self) -> bool:
        """
        Enable tracking functionality.

        Enables tracking by:
        1. Installing all necessary wrappers via install_wrappers()
        2. Registering event handlers
        3. Setting the enabled flag to True

        Returns:
            bool: True if tracking was enabled, False if it was already enabled

        Note:
            This is an atomic operation. If install_wrappers() fails, all wrappers
            will be removed. If register_event_handlers() fails, all wrappers will be removed
            and unregister_event_handlers() will be called to ensure cleanup.
        """
        if self.enabled:
            logger.info("Tracking for the %s domain is already enabled", self.name)
            return False

        # Step 1: Install wrappers
        try:
            self.install_wrappers()
        except Exception as e:
            # Roll back any wrappers that were installed
            self.uninstall_wrappers()
            logger.warning(
                "Failed to install wrappers for the %s domain: %s",
                self.name,
                repr(e),
                exc_info=True,
            )
            return False

        # Step 2: Register event handlers
        try:
            self.register_event_handlers()
        except Exception as e:
            # Roll back any event handler that were registered
            self.unregister_event_handlers()
            self.uninstall_wrappers()
            logger.warning(
                "Failed to register event handlers for the %s domain: %s",
                self.name,
                repr(e),
                exc_info=True,
            )
            return False

        # Step 3: Mark as enabled
        self.enabled = True
        logger.info("Enabled domain tracking for %s", self.name)
        return True

    def disable(self) -> bool:
        """
        Disable tracking functionality.

        Disables tracking by:
        1. Unregistering event handlers
        2. Removing all installed wrappers
        3. Setting the enabled flag to False

        Returns:
            bool: True if tracking was disabled, False if it was already disabled
        """
        if not self.enabled:
            logger.info("Tracking for the %s domain isn't enabled", self.name)
            return False

        # Step 1: Unregister event handlers
        unregister_handlers_ok = True
        try:
            self.unregister_event_handlers()
        except Exception as e:
            logger.warning(
                "Failed to unregister event handlers for the %s domain: %s",
                self.name,
                repr(e),
                exc_info=True,
            )
            unregister_handlers_ok = False

        # Step 2: Uninstall wrappers
        uninstall_wrappers_ok = True
        try:
            self.uninstall_wrappers()
        except Exception as e:
            logger.warning(
                "Failed to uninstall wrappers for the %s domain: %s",
                self.name,
                repr(e),
                exc_info=True,
            )
            uninstall_wrappers_ok = False

        # Step 3: Mark as disabled even if previous steps failed.
        self.enabled = False

        logger.info(
            "Disabled domain tracking for the %s domain. Event handlers: %s, Wrappers: %s",
            self.name,
            unregister_handlers_ok,
            uninstall_wrappers_ok,
        )
        return unregister_handlers_ok and uninstall_wrappers_ok

    def __repr__(self) -> str:
        return f"<Domain {self.name!r}, enabled: {self.enabled}"

    def __del__(self) -> None:
        if getattr(self, "enabled", False):
            logger.warning("Tracking domain %s was not disabled before deletion", self)
