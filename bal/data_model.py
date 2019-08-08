import textwrap
import typing
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from typing import Dict, Generic, Optional, List, Iterator

import six

T = typing.TypeVar("T")


class DataModel(Generic[T]):
    """
    A data model defines the structure of data. This is an abstract definition that must be
    implemented for specific data types.
    """

    def __init__(self):
        self._synced = True

    def _is_synced(self):
        """
        Returns true if the data in the model stayed the same since the last call to `set_synced`.

        :rtype: bool
        """
        return self._synced

    def _set_synced(self, synced=True):
        """
        Marked the model as synced/unsynced. This is is not meant to be called externally.

        :param bool synced: True if the data model is currently synced, false otherwise.
        """
        self._synced = synced

    def get_implementation(self):
        """
        Get the implementation of the model. By default, it returns the class name of the model.

        :rtype: Optional[str]
        """
        return type(self).__name__

    def get_description(self):
        """
        Get a description of the data represented by the model.

        :rtype: Optional[str]
        """
        docstring = type(self).__doc__
        if not docstring:
            return None
        return " ".join(textwrap.dedent(docstring).split("\n")).strip(" ")

    @abstractmethod
    def iterate(self):
        """
        Create an iterator of direct children. Each item is a tuple in which the fist value is
        the key/index of the child and the second value is the child.

        :rtype: Iterator[(Any, T)]
        """
        raise NotImplemented

    def __str__(self):
        return self._to_str()


class ClassModel(DataModel[T]):
    """
    An abstract definition of a data model targeting classes. It is useful when representing
    the model as a Python class, providing the iterate implementation. Any setters defined by the
    child class should set :py:attr:`self._synced` to False.

    :param List[Tuple[str,Callable[[],T]]] getters: A list of getters for the
        properties defined by the child class. Each item in the list is a tuple, the first item
        is the name of the property, the second item is the getter.
    """
    def __init__(self, getters):
        super(ClassModel, self).__init__()
        self._getters = getters

    def iterate(self):
        """
        Create an iterator for the object's properties. Each item is a tuple in which the fist
        value is property name and the second value is the child.

        :rtype: Iterator[Tuple[str, T]]
        """
        for k, getter in self._getters:
            yield k, getter()


class ValueModel(DataModel):
    """
    An implementation of a data model that contains a single value with no children. It also
    wraps documentation for value's name and description (ie value 0x2 is named "FOO" and its
    description is "The bitstream targets the FOO device").

    :param Any value: The value wrapped by the model. It should be a native value (ie str, int,
        bytes etc...)
    :param str value_name: A name for the value wrapped by the data object.
    :param str value_description: A description for the value wrapped by the data object
    """

    type = "Value"

    def __init__(
            self,
            value,
            value_name=None,
            value_description=None,
    ):
        super(ValueModel, self).__init__()
        if value is not None and not isinstance(value, int):
            raise ValueError(
                "The unpacked data for a ValueModel is expected to be an int"
            )
        self._value = value
        self.value_name = value_name
        self.value_description = value_description

    def get_value(self):
        """
        Get the value wrapped by the model.

        :rtype: Any
        """
        return self._value

    def set_value(self, value):
        """
        Set the value wrapped by the model. The model is marked as out of synch so that it is
        repacked when `pack()` is called on the parent data object.

        :param Any value: The updated value wrapped by the model
        :rtype: ValueModel
        """
        self._value = value
        self._synced = False
        return self

    def __str__(self):
        """
        Build a string representation of the value.

        :rtype: str
        """
        str_value = hex(self._value)
        if self.value_name is not None:
            str_value = "{} ({})".format(str_value, self.value_name)
        return str_value

    def iterate(self):
        """
        Return an empty iterator.

        :rtype: Iterator[]
        """
        return iter([])


class DictModel(DataModel[T]):
    """
    A DataModel implementation that wraps a generic Python dict. Just like regular Python
    dictionary, it should be avoided as when the value types change as the typing information is
    lost.

    :param OrderedDict[str,T] attributes: The dict data wrapped by the model.
    """
    def __init__(self, attributes):
        super(DictModel, self).__init__()
        if not isinstance(attributes, OrderedDict):
            raise ValueError("The attributes should be an ordered dict")
        self._attributes = attributes  # type: Optional[OrderedDict[str, T]]

    def iterate(self):
        """
        Create an iterator of the dictionary items. Each item is a tuple in which the fist
        value is the key of the child and the second value is the child.

        :rtype: Iterator[Tuple[str, T]]
        """
        return iter(self._attributes.items())

    def get(self, key):
        """
        Get a value from the dictionary.

        :param str key:
        :rtype: T
        """
        return self._attributes.get(key)

    def __getitem__(self, key):
        """
        :param str key:
        :rtype: T
        """
        return self._attributes[key]

    def __len__(self):
        """
        :rtype: int
        """
        return len(self._attributes)

    def __setitem__(self, key, value):
        """
        :param str key:
        :param T value:
        """
        self._synced = False
        self._attributes[key] = value

    def __delitem__(self, key):
        """
        :param str key:
        :return:
        """
        self._synced = False
        del self._attributes[key]

    def __iter__(self):
        """
        :rtype: Iterator[T]
        """
        return iter(self._attributes)


class ArrayModel(DataModel[T]):
    """
    A DataModel implementation that wraps a generic Python list.

    :param List[T] items: The array wrapped by the model
    """
    def __init__(self, items):
        super(ArrayModel, self).__init__()
        self._items = items  # type: List[T]

    def iterate(self):
        """
        Create an iterator of the array items. Each item is a tuple in which the fist
        value is the index of the child and the second value is the child.

        :rtype: Iterator[Tuple[int, T]]
        """
        return enumerate(self)

    def insert(self, index, object):
        """
        Insert an item at a given position.

        :param int index: The index at which the item should be added
        :param T object: The item to add.
        """
        self._synced = False
        self._items.insert(index, object)

    def append(self, object):
        """
        Add an item at the end of the list.

        :param T object: The item to add.
        """
        self._synced = False
        self._items.append(object)

    def pop(self, index=None):
        """
        Remove the item at the given position in the list, and return it. If no index is
        specified, a.pop() removes and returns the last item in the list.

        :param Optional[int] index:
        :rtype: T
        """
        self._synced = False
        return self._items.pop(index)

    def __iter__(self):
        """
        :rtype: Iterator[T]
        """
        return iter(self._items)

    def __getitem__(self, index):
        """
        :param int index:
        :rtype: T
        """
        return self._items[index]

    def __len__(self):
        """
        :rtype: int
        """
        return len(self._items)

    def __setitem__(self, index, object):
        """
        :param int index:
        :param T object:
        """
        self._synced = False
        self._items[index] = object

    def __delitem__(self, index):
        """
        :param int index:
        """
        self._synced = False
        del self._items[index]