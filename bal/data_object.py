import inspect
import textwrap
import typing
from typing import TypeVar

from bal.context_ioc import BALIoCContext, AbstractConverter
from bal.data_model import DataModel

T = TypeVar("T")


class DataObject(typing.Generic[T]):
    """
    The data object wraps either bytes or a model or both. Note that a data object does not
    define the structure of the data that it wraps.

    :param BALIoCContext context: The model wrapped by the data object
    :param T model: The model wrapped by the data object
    :param bytes bytes: The bytes wrapped by the data object.
    :param AbstractConverter converter: The converter used to convert the model to bytes and back.
    :param int bit_size: The number of bits in the bytes. If the value is not provided,
        it is calculated from the bytes property.
    """
    def __init__(
            self,
            context,
            converter,
            ModelInterface,
            model=None,
            bytes=None,
            bit_size=None,
    ):
        if bytes is None and model is None:
            raise ValueError("Either the bytes or the model must be provided")
        if ModelInterface is None:
            raise ValueError("The model interface must be provided.")
        self._context = context
        self._synced = True
        self._bytes = bytes
        self._bit_size = bit_size
        self._model = model # type: DataModel[DataObject]
        self._ModelInterface = ModelInterface
        self.converter = converter

    @staticmethod
    def create_unpacked(context, model, bit_size=None, bytes=None):
        """
        Create a new unpacked data object.

        :param BALIoCContext context: The model wrapped by the data object.
        :param T model: The model wrapped by the data object.
        :param int bit_size: If the value is not provided, it is calculated from the bytes property
            after the object is packed.
        :param bytes bytes: The bytes wrapped by the data object.
        
        :rtype DataObject[T]
        """
        converter = None
        ModelInterface = type(model)
        for Interface in inspect.getmro(type(model)):
            converter = context.create_converter(Interface)
            if converter is not None:
                ModelInterface = Interface
                break
        return DataObject(context, converter, ModelInterface, model, bytes, bit_size=bit_size)

    @staticmethod
    def create_packed(context, bytes, ModelInterface, converter_args=()):
        """
        Create a new packed data object.

        :param BALIoCContext context: The model wrapped by the data object.
        :param bytes bytes: The bytes wrapped by the data object.
        :param Type[T] ModelInterface: The interface for the model wrapped by the data object.
        :param Any converter_args: Extra arguments to provide to the converter.
        
        :rtype DataObject[T]
        """
        converter = context.create_converter(ModelInterface, *converter_args)
        return DataObject(context, converter, ModelInterface, bytes=bytes)

    def is_unpacked(self):
        """
        Returns true if the DataObject has been unpacked (or was created unpacked)

        :rtype: bool
        """
        return self._model is not None

    def is_packed(self):
        """
        Returns true if the DataObject has been packed (or was created packed)

        :rtype: bool
        """
        return self._bytes is not None

    def is_convertible(self):
        """
        Returns true if the DataObject can be unpacked/packed, false otherwise.

        :rtype: bool
        """
        return self.converter is not None

    def get_bit_size(self):
        """
        Get the number of bits making up the packed data object.

        :rtype: int
        """
        if self._bit_size is not None:
            return self._bit_size
        elif not self.is_packed():
            return 0
        else:
            return len(self._bytes) * 8

    def get_model_type(self):
        """
        Get the type of the model wrapped by the data object. The type is akin to the name of the
        interface implemented by the data model.

        :rtype: str
        """
        return self._ModelInterface.__name__

    def get_model_implementation(self):
        """
        Get the implementation of the model wrapped by the data object. The implementation is
        akin to the class name of the data model.

        :rtype: str
        """
        return self._model.get_implementation() if self._model is not None else None

    def get_model_description(self):
        """
        Get a description of the data model wrapped by the data object.

        :rtype: Optional[str]
        """
        if self._model is not None:
            return self._model.get_description()
        docstring = self._ModelInterface.__doc__
        if not docstring:
            return None
        return " ".join(textwrap.dedent(docstring).split("\n")).strip(" ")

    def get_bytes(self):
        """
        Returns the bytes for the data object. This value may be outdated if pack hasn't been
        called.

        :rtype: Optional[bytes]
        :raises ValueError: If the data object is not packed.
        :raises ValueError: If the data object's bytes are out of sync with the model.
        """
        if not self.is_packed():
            raise ValueError("The data object must be packed before get_bytes can be called.")
        return self._bytes

    def set_bytes(self, data_bytes):
        """
        Set the bytes representation of the data object's model. The bytes must represent the
        current values of the model as it is marked as synced.

        :param bytes data_bytes: The byte representation of the data object's model
        """
        if self.is_unpacked():
            raise ValueError("The bytes cannot be set for an unpacked data object.")
        self._bytes = data_bytes
        self._synced = False
        return data_bytes

    def get_model(self):
        """
        Returns the model for the data object.

        :rtype: T
        :raises ValueError: If the data object is not unpacked.
        """
        if not self.is_unpacked():
            raise ValueError("The data object must be unpacked before get_model can be called.")
        return self._model

    def set_model(self, model):
        """
        Set the model for the data object. If a model did not exist, it's assumed the model
        corresponds to the data object bytes and it is marked as synced. If a model did exist,
        it's assumed the updated model is a modification of the previous one and it is marked as
        unsynced.

        These assumptions can be invalid if we are reverting a model to its original value. In
        that case, the model would be unnecessarily repacked.

        :param T model: The unpacked data.
        :rtype: DataObject[T]

        :raises ValueError: If the provided model is not an instance of DataModel
        """
        if model is None or not isinstance(model, DataModel):
            raise ValueError("A DataModel instance must be provided for the ")
        model._set_synced(self._model is None)
        self._model = model
        return self

    def unpack(self):
        """
        Create and store a data model from the bytes stored on the data object. It is a noop if
        the data model is already unpacked.

        :rtype: T

        :raises ValueError: If the data object is not convertible (ie no :py:class:`Converter`
            is set for the :py:class:`DataObjectModel`).
        """
        if self.is_unpacked():
            return self._model
        if not self.is_convertible():
            raise ValueError("No converter registered for data object {}".format(
                self.get_model_type()
            ))
        self.set_model(self.converter.unpack(self._bytes))
        return self._model

    def unpack_all(self):
        """
        Recursively unpack all data object contained by the data model.

        :rtype: T
        """
        if not self.is_unpacked():
            if not self.is_convertible():
                return
            self.unpack()
        for k, child in self._model.iterate():
            if child is None:
                continue
            child.unpack_all()
        return self._model

    def pack(self):
        """
        Create and store a bytes representation of the data model stored on the data object. It
        is a noop if the data object is marked as synced or if it is not unpacked. The call to
        `Converter.pack()` usually means that the `pack()` method will be called recursively on
        all descendants that are out of sync.

        :rtype: bytes, bool
        :raises ValueError: If the data object is not convertible (ie no :py:class:`Converter`
            is set for data object).
        """
        if not self.is_unpacked() or (self._synced is True and self.is_packed()):
            return self._bytes
        if not self.is_convertible():
            raise ValueError("No converter registered for data object {}".format(
                self.get_model_type())
            )
        self._bytes = self.converter.pack(self._model)
        self._synced = True
        return self._bytes

    def synchronize(self, force_desync=False):
        """
        Ensure that for a given data object, it is marked as out of sync if any of its
        descendants are marked as out of sync. This check is performed recursively for each
        descendant of the data object.

        This method should be called before calling :py:meth:`ObjectModel.pack` to make sure that
        out of sync descendants get repacked.

        :param bool force_desync: If set to true, mark all children data object as out of sync.
        """
        if not self.is_unpacked():
            self._synced = self._synced and not force_desync
            return self._synced
        children_synced = True
        for _, child in self._model.iterate():
            if child is None:
                continue
            if child.synchronize(force_desync) is False:
                children_synced = False
        self._synced = children_synced and self._model._is_synced() and not force_desync
        return self._synced

    def to_str(self, indent_count=0, indent_size=2, recurse=True):
        """
        Builds a string representation of the data object

        :param int indent_count: The number of indents to use when rendering the object
        :param int indent_size: The size (in spaces) of an indent
        :param bool recurse: If False, does not include child data in the string representation
        :rtype: str
        """
        if not self.is_unpacked():
            return "Packed{}({})".format(self.get_model_type(), len(self._bytes))

        model_type = self.get_model_type()
        model_children = list(self._model.iterate())
        if len(model_children) > 0:
            indent = " " * indent_count * indent_size
            values_str_parts = []
            for key, value in model_children:
                values_str_parts.extend([
                    indent + " " * indent_size,
                    str(key),
                    ": ",
                    value.to_str(indent_count + 1, indent_size,
                                 recurse) if value is not None else "None",
                    ", \n"
                ])
            model_str = "{\n" + "".join(values_str_parts) + indent + "}"
        else:
            model_str = str(self._model)
        if model_type is None:
            return model_str
        return "{}({})".format(model_type, model_str)

    def __str__(self):
        return self.to_str()


