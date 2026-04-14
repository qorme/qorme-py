from __future__ import annotations

import atexit
import logging
import threading
from operator import attrgetter

from qorme.deps import Deps
from qorme.domain import Domain
from qorme.utils.config import Config, ConfigurationError

logger = logging.getLogger(__name__)


class TrackingManager:
    """
    This class orchestrates the tracking process by managing
    the lifecycle of tracking domains and their dependencies.
    """

    _instance = None
    _lock = threading.Lock()

    @classmethod
    def install(cls, **kwargs) -> TrackingManager | None:
        if cls._instance:
            return cls._instance

        with cls._lock:
            if cls._instance:
                return cls._instance

            manager = cls(**kwargs)
            if not manager.start():
                return

            cls._instance = manager
            atexit.register(cls.uninstall)
            return manager

    @classmethod
    def uninstall(cls) -> bool:
        if not cls._instance:
            return False

        with cls._lock:
            manager = cls._instance
            cls._instance = None

        return manager.stop()

    @classmethod
    def instance(cls) -> TrackingManager | None:
        return cls._instance

    def __init__(self, settings, defaults) -> None:
        self.config = Config(name="qorme", data=settings, defaults=defaults)
        self.deps: Deps | None = None
        self.active = False
        self.domain_handlers: dict[str, Domain] = {}

    @property
    def domains(self) -> set[str]:
        return set(self.config.domains)

    def get_domain_handler(self, domain: str) -> Domain | None:
        return self.domain_handlers.get(domain)

    def start(self) -> bool:
        """
        Start tracking for all configured domains.

        This method initializes tracking handlers for each active domain
        in the configuration. If tracking is already active, it returns False.

        Args:
            config: Configuration object containing tracking settings

        Returns:
            bool: True if tracking was started, False if already active
        """
        if self.active or not getattr(self.config, "active", True):
            return False

        self.deps = Deps(self.config.deps)
        domains = self.domains
        for domain in domains:
            self.start_domain_tracking(domain)

        self.active = True
        return True

    def stop(self) -> bool:
        """
        Stop all active tracking domains.

        This method properly shuts down all active tracking handlers and
        cleans up the tracking state. If tracking is already inactive,
        it returns False.

        Returns:
            bool: True if tracking was stopped, False if already inactive
        """
        if not self.active:
            return False

        for domain in tuple(self.domains):
            self.stop_domain_tracking(domain)

        if (deps := self.deps) is not None:
            deps.close()

        self.deps = None
        self.active = False
        return True

    def start_domain_tracking(self, domain: str) -> bool:
        """
        Initialize and start tracking for a specific domain.

        Args:
            domain: Name of the tracking domain to start

        Note:
            - Only starts if the domain is valid and not already enabled
            - Creates and enables the appropriate handler for the domain
            - Stores the handler in the handlers dictionary
        """
        if self.get_domain_handler(domain):
            logger.warning("%s domain is already enabled", domain)
            return False

        try:
            # Use attrgetter to follow dotted paths in config
            domain_config = attrgetter(domain)(self.config)
        except AttributeError:
            logger.warning("No configuration found for domain %s", domain)
            return False

        try:
            handler_class = domain_config.handler_class
        except (ConfigurationError, AttributeError):
            logger.warning("Failed to import handler class for %s domain", domain, exc_info=True)
            return False

        if not issubclass(handler_class, Domain):
            logger.warning("Handler class %s is not a subclass of Domain", handler_class)
            return False

        if (deps := self.deps) is None:
            deps = self.deps = Deps(self.config.deps)

        assert deps is not None

        try:
            handler = handler_class(deps, domain_config)
        except Exception:
            logger.warning("Failed initializing %s domain handler", domain, exc_info=True)
            return False

        try:
            enabled = handler.enable()
        except Exception:
            logger.warning("Caught error while enabling the %s domain", domain, exc_info=True)
            return False

        if not enabled:
            logger.warning("Failed to enable the %s domain", domain)
            return False

        self.domain_handlers[domain] = handler
        return True

    def stop_domain_tracking(self, domain: str) -> bool:
        """
        Stop and cleanup tracking for a specific domain.

        Args:
            domain: Name of the tracking domain to stop

        Returns:
            bool: True if the domain was stopped, False if it was not active
        """
        if not (handler := self.domain_handlers.pop(domain, None)):
            return False

        try:
            disabled = handler.disable()
        except Exception as e:
            logger.warning(
                "Caught %s while disabling the %s domain", repr(e), domain, exc_info=True
            )
            return False

        if not disabled:
            logger.warning("Domain %s was already disabled", domain)
            return False

        return True

    def __repr__(self) -> str:
        return f"TrackingManager(active={self.active}, handlers={self.domain_handlers})"

    def __del__(self) -> None:
        if getattr(self, "active", False):
            logger.warning("TrackingManager instance %s was not properly stopped", self)
