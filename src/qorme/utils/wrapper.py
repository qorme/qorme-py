from collections.abc import Generator, Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any
from weakref import WeakKeyDictionary, ref

from wrapt import ObjectProxy, wrap_function_wrapper

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Protocol
    from weakref import ReferenceType

    class WrapperProtocol(Protocol):
        """wrapt passes (wrapped, instance, args, kwargs) to the wrapper."""

        def __call__(
            self,
            wrapped: Callable[..., Any],
            instance: Any,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Any: ...


class WrappingError(RuntimeError): ...


class AlreadyWrappedError(WrappingError): ...


class DuplicateWrapperError(WrappingError): ...


class Wrapper:
    """
    Helper to wrap/unwrap objects.

    The actual wrapping is managed by the `wrapt` library which
    handles various edge cases (methods, classmethods, staticmethods...).

    Wrappers are required to follow the `WrapperProtocol` (see `qorme/types.py`).

    Stores weak references to wrapped objects to prevent leaks.

    Example usage:

    >>> class Item:
    ...     def __init__(self):
    ...         self._list = []
    ...
    ...     @property
    ...     def list(self):
    ...         return self._list
    ...
    ...     def append(self, val):
    ...         self._list.append(val)
    ...
    >>> def append_wrapper(wrapped, instance, args, kwargs):
    ...     doubled_args = (args[0] * 2,)
    ...     return wrapped(*doubled_args, **kwargs)
    ...
    >>> wrapper = Wrapper()
    >>> wrapper.wrap(Item, "append", append_wrapper)
    >>> item = Item()
    >>> item.append(1)
    >>> item.list
    [2]
    >>> wrapper.unwrap(Item, "append")
    True
    >>> item.append(1)
    >>> item.list
    [2, 1]
    """

    __slots__ = "_wrapped"

    def __init__(self) -> None:
        self._wrapped: WeakKeyDictionary[
            Any, dict[str, tuple[ReferenceType[WrapperProtocol], bool]]
        ] = WeakKeyDictionary()

    def wrap(
        self,
        obj: Any,
        member: str,
        wrapper: "WrapperProtocol",
    ) -> None:
        """
        Wraps the specified member of an object with the wrapper function.

        Args:
            obj: The object containing the member to wrap
            member: Name of the member to wrap
            wrapper: The wrapper function
        """
        owned = member not in obj.__dict__
        to_wrap = getattr(obj, member, None)
        if isinstance(to_wrap, ObjectProxy) and to_wrap._self_wrapper is wrapper:
            raise DuplicateWrapperError(obj, member, wrapper)

        if not (wrapped_members := self._wrapped.get(obj)):
            wrapped_members = self._wrapped[obj] = {}
        elif member in wrapped_members:
            raise AlreadyWrappedError(obj, member, wrapper, wrapped_members[member])

        wrapped_members[member] = ref(wrapper), owned

        try:
            wrap_function_wrapper(obj, member, wrapper)
        except Exception as e:
            self.unwrap(obj, member)
            raise WrappingError(obj, member, wrapper) from e

    def maybe_wrap(self, obj, member, wrapper):
        try:
            self.wrap(obj, member, wrapper)
        except DuplicateWrapperError:
            return

    def unwrap(self, obj: Any, member: str) -> bool:
        """
        Remove a wrapper from an object's member.

        Args:
            obj: The object containing the wrapped member
            member: Name of the member to unwrap

        Returns:
            bool: True if the member was successfully unwrapped, False otherwise.
        """
        if not (wrapped_members := self._wrapped.get(obj)) or not (
            wrap_info := wrapped_members.pop(member, None)
        ):
            return False

        # Remove `obj` from wrapped objects when there are
        # no longer wrappers attached to it.
        if not wrapped_members:
            del self._wrapped[obj]

        wrapper_ref, owned = wrap_info
        wrapped = getattr(obj, member, None)
        if not isinstance(wrapped, ObjectProxy) or wrapped._self_wrapper is not wrapper_ref():
            return False

        if owned:
            # Remove attribute from object's __dict__ since we own it.
            delattr(obj, member)
        else:
            # Restore wrapped attribute.
            setattr(obj, member, wrapped.__wrapped__)

        return True

    @contextmanager
    def wrap_temp(
        self,
        obj: Any,
        member: str,
        wrapper: "WrapperProtocol",
    ) -> Generator[None, None, None]:
        """
        Temporarily wrap an object's member with the wrapper function.

        Functions as a context manager that automatically unwraps the member
        when exiting the context.

        Args:
            obj: The object containing the member to wrap
            member: Name of the member to wrap
            wrapper: The wrapper function

        Yields:
            None
        """
        self.wrap(obj, member, wrapper)
        try:
            yield
        finally:
            self.unwrap(obj, member)

    def clear(self) -> None:
        """Remove all wrappers from all objects."""
        for obj in tuple(self._wrapped):
            for member in tuple(self._wrapped[obj]):
                self.unwrap(obj, member)

    def __iter__(self) -> Iterator["WrapperProtocol"]:
        """Iterate over all active wrapper functions."""
        for wrapped in self._wrapped.values():
            for wrapper_ref, _ in wrapped.values():
                if wrapper := wrapper_ref():
                    yield wrapper

    def __len__(self) -> int:
        """Returns the number of active wrappers."""
        return sum(1 for _ in self)
