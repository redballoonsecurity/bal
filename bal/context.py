from abc import ABCMeta, abstractmethod
from typing import Dict, Any, TypeVar

import six

from bal.context_ioc import BALIoCContext, BALIoCContextFactory
from bal.data_object import DataObject

T = TypeVar("T")


class BALContext(BALIoCContext):
    """
    This class is responsible for instantiating interface implementation (see
    :py:class:`bal.context_ioc.BALIoCContext`) and creating the root data object.
    """

    @abstractmethod
    def get_data(self):
        """
        Get the data object wrapping the data. The returned object starts out packed but may
        be modified by user call.

        :rtype: DataObject
        """
        raise NotImplementedError


class BALContextFactory(BALIoCContextFactory):
    """
    The BAL context factory is used to create new :py:class:`BALContext` object for given binary
    data. The factory is used to configure all the created :py:class:`BALContext`
    throughout the lifetime of the factory.

    This class is abstract and must be implemented for specific families of binary data.
    """

    @abstractmethod
    def create(self, bytes):
        """
        Create a BAL context from the provided bytes.

        :param bytes bytes: The bytes for the binary data
        :rtype: BALContext
        """
        raise NotImplementedError


class BALManager:
    """
    Manages multiple :py:class:`BALContextFactory` instances to return the appropriate
    factory based on a user provided key (ie "xilinx", "altera").
    """

    def __init__(self):
        self._bals = {}  # type: Dict[Any, BALContextFactory]

    def register(self, key, context_factory):
        """
        Register an BAL implementation with the manager

        :param Any key: The key associated with the Implementation.
        :param BALContextFactory context_factory: An BAL implementation instance.
        """
        if key in self._bals:
            raise ValueError("A BAL implementation is already registered for {}".format(key))
        self._bals[key] = context_factory

    def get(self, key):
        """
        Retrieve the context factory registered for the provided key.

        :param Any key: The key associated with the context factory.
        :rtype: BALContextFactory
        """
        bal = self._bals.get(key)
        if bal is None:
            raise ValueError("No BAL implementation is registered for {}".format(key))
        return bal
