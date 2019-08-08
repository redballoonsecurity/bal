import logging
from abc import ABCMeta, abstractmethod
from typing import Type, Any, TypeVar, Dict

import six

T = TypeVar("T")
LOGGER = logging.getLogger("bal")


@six.add_metaclass(ABCMeta)
class AbstractAnalyzer(object):
    """
    Analyze binary data to extract information.

    :param BALIoCContext context: The BAL context that can be read/modified by the analyzer.
    """
    def __init__(self, context):
        self.context = context

    @abstractmethod
    def analyze(self, *args, **kwargs):
        """
        Perform the analysis.

        :rtype: Any
        """
        raise NotImplemented


@six.add_metaclass(ABCMeta)
class AbstractConverter(object):
    """
    Converts bytes to data model and vice-versa. It is instantiated by the BAL context.

    :param BALIoCContext context: The BAL context that can be read/modified by the converter.
    """
    def __init__(self, context):
        self.context = context

    @abstractmethod
    def unpack(self, data_bytes):
        """
        Deserialize a model from bytes.

        :param bytes data_bytes: The data to unpack
        :rtype: DataModel
        """
        raise NotImplemented

    @abstractmethod
    def pack(self, data_model):
        """
        Serialize a model to bytes.

        :param DataModel data_model: The model to pack
        :rtype: bytes
        """
        raise NotImplemented


@six.add_metaclass(ABCMeta)
class AbstractModifier(object):
    """
    Modifies binary data. It is instantiated by the BAL context.

    :param BALIoCContext context: The BAL context that can be used by the converter.
    """

    def __init__(self, context):
        self.context = context

    @abstractmethod
    def modify(self, *args, **kwargs):
        """
        Perform the modification.

        :rtype: Any
        """
        raise NotImplemented


class BALIoCContext(object):
    """
    A IoC Interface implementation is responsible for instantiating the appropriate
    implementation of converters, analyzers, and modifiers. The context may store
    extra information extracted from the binary data and/or config data used to unpack the
    binary data.
    A new context is instantiated for each binary data instance.

    It provides basic `IoC <https://en.wikipedia.org/wiki/Inversion_of_control>`_ for
    converters, analyzers and modifiers by holding a mapping of interfaces to implementation.
    This mapping should not be configured on the :py:class:`BALContext` directly, it should be
    configured on the :py:class:`BALContextFactory`. Code that requests a new
    converter/analyzer/modifier instance can rely on knowing just the interface while the actual
    implementation can be defined at run time.

    :param Dict[Type[DataModel],Type[AbstractConverter]] converters_by_type: The converter
        interfaces mapped to their implementation.
    :param Dict[Type[AbstractAnalyzer],Type[AbstractAnalyzer]] analyzers_by_type: The analyzer
        interfaces mapped to their implementation.
    :param Dict[Type[AbstractModifier],Type[AbstractModifier]] modifiers_by_type: The modifier
        interfaces mapped to their implementation.
    """
    def __init__(self, converters_by_type, analyzers_by_type, modifiers_by_type):
        self._converters_by_type = converters_by_type
        self._analyzers_by_type = analyzers_by_type
        self._modifiers_by_type = modifiers_by_type

    def create_converter(self, TargetDataModelType, *args, **kwargs):
        # type: (Type[T], Any, Any) -> T
        """
        Create a converter instance that implements the provided interface.

        :param Type[DataModel] TargetDataModelType: The interface of the data module handled by the
        converter.
        :rtype: Optional[AbstractConverter]
        """
        ConverterImplementation = self._converters_by_type.get(TargetDataModelType)
        if ConverterImplementation is None:
            LOGGER.debug("No converter registered for interface {}".format(
                TargetDataModelType.__name__
            ))
            return None
        return ConverterImplementation(self, *args, **kwargs)

    def create_analyzer(self, AnalyzerType, *args, **kwargs):
        # type: (Type[T], Any, Any) -> T
        """
        Create an analyzer instance that implements the provided interface.

        :param Type[AbstractAnalyzer] AnalyzerType: The interface of the requested analyzer.
        :rtype: Optional[AbstractAnalyzer]
        """
        AnalyzerImplementation = self._analyzers_by_type.get(AnalyzerType)
        if AnalyzerImplementation is None:
            LOGGER.debug("No analyzer registered for interface {}".format(
                AnalyzerType.__name__
            ))
            return None
        return AnalyzerImplementation(self, *args, **kwargs)

    def create_modifier(self, ModifierType, *args, **kwargs):
        # type: (Type[T], Any, Any) -> T
        """
        Create a modifier instance of the provided type.

        :param Type[AbstractModifier] ModifierType: The interface of the requested modifier.
        :rtype: Optional[AbstractModifier]
        """
        ModifierImplementation = self._modifiers_by_type.get(ModifierType)
        if ModifierImplementation is None:
            LOGGER.debug("No modifier registered for interface {}".format(
                ModifierType.__name__
            ))
            return None
        return ModifierImplementation(self, *args, **kwargs)


class BALIoCContextFactory(object):
    """
    The BAL IoC context factory is used to create new :py:class:`BALIoCContext` object for a
    given instance of binary data.
    The factory is used to configure all the created
    :py:class:`BALIoCContext` throughout the lifetime of the factory.

    The only configuration taken care of by this abstract class is the mapping of interfaces to
    implementations for analyzers and modifiers, as well as mapping data model interfaces to converter
    implementations which convert each data model interface. The mapping is provided to the
    created context to provide a simple `IoC <https://en.wikipedia.org/wiki/Inversion_of_control>`_
    mechanism.

    """
    def __init__(self):
        self._converters_by_type = {}
        # type: Dict[Type[DataModel], Type[DataModel]]
        self._analyzers_by_type = {}
        # type: Dict[Type[AbstractAnalyzer], Type[AbstractAnalyzer]]
        self._modifiers_by_type = {}
        # type: Dict[Type[AbstractModifier], Type[AbstractModifier]]

    def register_converter(self, DataModelInterface, ConverterImplementation):
        """
        Register a converter implementation.

        :param Type[DataModel] DataModelInterface: The interface of the data model which
        ConvertImplementation serializes and deserializes
        :param Type[AbstractConverter] ConverterImplementation: The converter class that
            implements the interface.
        """
        self._converters_by_type[DataModelInterface] = ConverterImplementation

    def register_analyzer(self, AbstractAnalyzer, AnalyzerImplementation):
        """
        Register an anlyzer implementation.

        :param Type[AbstractAnalyzer] AbstractAnalyzer: The analyzer interface for which an
            implementation is registered.
        :param Type[AbstractAnalyzer] AnalyzerImplementation: The analyzer class that
            implements the interface.
        """
        self._analyzers_by_type[AbstractAnalyzer] = AnalyzerImplementation

    def register_modifier(self, AbstractModifier, ModifierImplementation):
        """
        Register a modifier implementation.

        :param Type[AbstractModifier] AbstractModifier: The modifier interface for which an
            implementation is registered.
        :param Type[AbstractModifier] ModifierImplementation: The modifier interface for which an
            implementation is registered.
        """
        self._modifiers_by_type[AbstractModifier] = ModifierImplementation