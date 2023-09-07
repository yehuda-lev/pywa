"""
This module contains the handlers for incoming updates.
"""

from __future__ import annotations

__all__ = [
    "MessageHandler",
    "CallbackButtonHandler",
    "CallbackSelectionHandler",
    "RawUpdateHandler",
    "MessageStatusHandler"
]

from typing import Callable, Any, TYPE_CHECKING, Iterable, cast
from pywa import filters as fil
from pywa.types import Message, CallbackButton, CallbackSelection, MessageStatus
from pywa.types.callback import CallbackDataT, CallbackData, CALLBACK_SEP

if TYPE_CHECKING:
    from pywa.client import WhatsApp


def _resolve_callback_data(factory: CallbackDataT) -> tuple[CallbackDataT, tuple[Callable[[WhatsApp, Any], bool]]]:
    """Internal function to resolve the callback data into a factory and a filter."""
    clb_filter = None
    if issubclass(factory, CallbackData):
        factories = factory.from_str
        clb_filter = fil.callback.data_startswith(cast(str, factory.__callback_id__))
    elif callable(factory):
        factories = factory
    elif isinstance(factory, Iterable):
        _factories = (f.from_str if issubclass(f, CallbackData) else f for f in factory)
        callback_datas = tuple(bool(issubclass(f, CallbackData)) for f in factory)
        factories = lambda _, data: tuple(map(lambda f, s: f(s), zip(_factories, data.split(CALLBACK_SEP))))  # noqa
        if any(callback_datas):
            clb_filter = fil.callback.data_startswith(factories[callback_datas.index(True)].__callback_id__)
    else:
        raise ValueError(f"Unsupported factory type {factory}.")
    return factories, ((clb_filter,) if clb_filter else ())


class Handler:
    """Base class for all handlers."""
    __handler_type__: str

    def __init__(
            self,
            handler: Callable[[WhatsApp, Any], Any],
            *filters: Callable[[WhatsApp, Any], bool]
    ):
        """
        Initialize a new handler.
        """
        self.handler = handler
        self.filters = filters

    def __call__(self, wa: WhatsApp, data: Any):
        if all((f(wa, data) for f in self.filters)):
            self.handler(wa, data)


class MessageHandler(Handler):
    """
    Handler for incoming messages (text, image, video, etc.).
        - You can use the :func:`~pywa.client.WhatsApp.on_message` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_text_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageHandler(print_text_messages, fil.text))

    Args:
        handler: The handler function. (gets the WhatsApp instance and the message as arguments)
        *filters: The filters to apply to the handler. (gets the WhatsApp instance and
            the message as arguments and returns a boolean)
    """
    __handler_type__ = "message"

    def __init__(
            self,
            handler: Callable[[WhatsApp, Message], Any],
            *filters: Callable[[WhatsApp, Message], bool]
    ):
        super().__init__(handler, *filters)


class CallbackButtonHandler(Handler):
    """
    A button callback handler.
        - You can use the :func:`~pywa.client.WhatsApp.on_callback_button` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_btn = lambda _, btn: print(btn)
        >>> wa.add_handlers(CallbackButtonHandler(print_btn, fil.callback.data_startswith('id:')))

    Args:
        handler: The handler function. (gets the WhatsApp instance and the callback as arguments)
        *filters: The filters to apply to the handler. (gets the WhatsApp instance and
            the callback as arguments and returns a boolean)
        factory: The constructor/s to use to construct the callback data.
    """
    __handler_type__ = "button"

    def __init__(
            self,
            handler: Callable[[WhatsApp, CallbackButton], Any],
            *filters: Callable[[WhatsApp, CallbackButton], bool],
            factory: CallbackDataT = str
    ):
        self.factory, clb_filter = _resolve_callback_data(factory)
        super().__init__(handler, *clb_filter, *filters)


class CallbackSelectionHandler(Handler):
    """
    A selection callback handler.
        - You can use the :func:`~pywa.client.WhatsApp.on_callback_selection` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_selection = lambda _, sel: print(sel)
        >>> wa.add_handlers(CallbackSelectionHandler(print_selection, fil.callback.data_startswith('id:')))

    Args:
        handler: The handler function. (gets the WhatsApp instance and the callback as arguments)
        *filters: The filters to apply to the handler. (gets the WhatsApp instance and the callback as arguments and
            returns a boolean)
        factory: The constructor/s to use to construct the callback data.
    """
    __handler_type__ = "selection"

    def __init__(
            self,
            handler: Callable[[WhatsApp, CallbackSelection], Any],
            *filters: Callable[[WhatsApp, CallbackSelection], bool],
            factory: CallbackDataT = str
    ):
        self.factory, clb_filter = _resolve_callback_data(factory)
        super().__init__(handler, *clb_filter, *filters)


class MessageStatusHandler(Handler):
    """
    A message status handler.
        - You can use the :func:`~pywa.client.WhatsApp.on_message_status` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_failed_messages = lambda _, msg: print(msg)
        >>> wa.add_handlers(MessageStatusHandler(print_failed_messages, fil.message_status.failed))

    Args:
        handler: The handler function. (gets the WhatsApp instance and the message status as arguments)
        *filters: The filters to apply to the handler. (gets the WhatsApp instance and
            the message status as arguments and returns a boolean)
    """
    __handler_type__ = "message_status"

    def __init__(
            self,
            handler: Callable[[WhatsApp, MessageStatus], Any],
            *filters: Callable[[WhatsApp, MessageStatus], bool]
    ):
        super().__init__(handler, *filters)


class RawUpdateHandler(Handler):
    """
    A raw update handler.
        - This handler is called for **EVERY** update received from WhatsApp, even if it's not sent to the client phone number.
        - You can use the :func:`~pywa.client.WhatsApp.on_raw_update` decorator to register a handler for this type.

    Example:

        >>> from pywa import WhatsApp, filters as fil
        >>> wa = WhatsApp(...)
        >>> print_updates = lambda _, data: print(data)
        >>> wa.add_handlers(RawUpdateHandler(print_updates))

    Args:
        handler: The handler function. (gets the WhatsApp instance and the data-dict as arguments)
        *filters: The filters to apply to the handler. (gets the WhatsApp instance and
            the data-dict as arguments and returns a boolean)
    """
    __handler_type__ = "raw_update"

    def __init__(
            self,
            handler: Callable[[WhatsApp, dict], Any],
            *filters: Callable[[WhatsApp, dict], bool]
    ):
        super().__init__(handler, *filters)
