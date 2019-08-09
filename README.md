# Binary Abstraction Layer (BAL)

The Binary Abstraction Layer (BAL) package is a tiny framework for analyzing and manipulating 
binary data. 
Its guiding principle is that a tree is a natural representation for binary data. 
For example a firmware may look as follow:

 - Zip Data
    - ELF
        - Header
        - Code
        - Data
    - Images
    - Config
    
It defines 3 broad categories of operations on the tree: **convert**, **analyze** and **modify**.

 - *Converters* handle serializing and deserializing binary data.
 - *Analyzers* handle extracting information from the tree representation.
 - *Modifiers* handle arbitrary modification of the binary.

## Installation

The BAL package can be installed from PyPi with the following command:
```
pip install bal
```

To install the BAL module from the repository, clone the repo and run:

```
pip install .
```

To install the BAL package and generate a local copy of its documentation, run:

```
pip install .[docs]
make html-docs
```

To install the core BAL module as well as dependencies for the example, run:

```
pip install .[examples]
```

## Concepts

Each node in the tree is represented as a `DataObject`. 
A `DataObject` can wrap either an unstructured string of raw binary data or a `DataModel` (or both). 
A `DataModel` is an abstract class defining some sort of structured data. 
The `DataModel` is created when deserializing raw binary data. 
It fits the typical definition of data model.


In addition, the BAL framework defines a few interfaces:

 - `bal.context_ioc.AbstractConverter` A converter takes care of unpacking bytes into a `DataModel` 
  (i.e. deserializing) and packing its `DataModel` into bytes (i.e. serializing). Its method 
  signatures are inflexible so that they may be called directly by the `DataObject`.
 - `bal.context_ioc.AbstractModifier` A modifier updates the content of any node within the tree.
  It may modify the packed or unpacked data. It contains a single `modify()` method with an 
  undefined signature. It may walk the entire tree, unpacking on the way.
 - `bal.context_ioc.AbstractAnalyzer` An analyzer extracts data from a tree. The type of 
  the returned data is defined by the concrete analyzer implementation. It contains a single 
  `analyze()` method with an undefined signature. It may walk the entire tree, unpacking on the way.
 - `bal.context_ioc.BALIocContext` The IoC context provides a simple implementation of the 
  [Inversion of Control](https://en.wikipedia.org/wiki/Inversion_of_control) pattern. It looks up
  the implementation of a given interface and returns a new instance. It is used to instantiate 
  an `AbstractConverter`, `AbstractModifier` or `AbstractAnalyzer`. 
   - For `AbstractModifier`s and `AbstractAnalyzer`s, an interface extending the `AbstractModifier` or `AbstractAnalyzer` is supplied and an implementation of the interface is returned.
   - For `AbstractConverters`, an interface extending `DataModel` is supplied and an `AbstractConverter` implementation will be returned. This implementation's `pack()` method will create an instance of the supplied `DataModel` interface, and its `unpack()` method will serialize an instance of the supplied `DataModel` interface.
- `bal.context_ioc.BALIoCContextFactory` Creates a configured instance of the `BALIoCContext`. It
  provides methods for the user to register the implementation of interfaces.
- `bal.context.BALContext` A new context is created for each tree. It inherits from the 
  `BALIoCContext`. The context contains a reference to the root `DataObject`. It may be used as 
  a cache for analyzers that are either expensive or frequently called. It may also be used to 
  store data that does not fit cleanly into a tree (for example relationships between unrelated 
  nodes). 
 - `bal.context.BALContextFactory` As implied, it is responsible for creating a `BALContext`. The
  factory is a good place to load external configuration that will be passed to the context. In 
  most settings, the factory would be created when the application starts and destroyed when it 
  dies.
 - `bal.context.BALManager` The BAL manager offers a way to look up factories using a key. It is 
  not strictly necessary, and should only be used in applications that need to dynamically retrieve multiple different 
  context factories

The full documentation for the API is available on 
 [github.io](https://ballon-rouge.github.io/bal/)



## Guide

All the code for this guide is contained in the [./example](./example) folder.

The first step is to declare a new `DataModel` class that defines the data structure for the root 
node and its children.
For example, a Xilinx bitstream has 3 children: the header, a sync marker and the config packets.
The format of the header is not known, the sync marker does not have a format and the packets 
are an array of unknown data.

```python
class XilinxPacketsInterface(DataModel):
    """
    An array of Xilinx register configuration packets.
    """


class XilinxBitstreamHeaderInterface(DataModel):
    """
    The Xilinx bitstream header contains unknown information.
    """


class  XilinxBitstreamSyncMarkerInterface(DataModel):
    """
    The Xilinx bitstream sync marker
    """


class XilinxBitstream(ClassModel[DataObject]):
    """
    The root model for a Xilinx bitstream. It contains data objects for a header, sync marker, and packets.
    """

    def __init__(
            self,
            header,
            sync_marker,
            packets
    ):
        """
        :param DataObject[XilinxBitstreamHeaderInterface] header:
        :param DataObject[XilinxBitstreamSyncMarker] sync_marker:
        :param DataObject[XilinxPackets] packets:
        """
        super(XilinxBitstream, self).__init__((
            ("header", self.get_header),
            ("sync_marker", self.get_sync_marker),
            ("packets", self.get_packets),
        ))
        self.header = header
        self.sync_marker = sync_marker
        self.packets = packets
        
    def get_header(self):
        return self.header
    
    def get_sync_marker(self):
        return self.sync_marker
    
    def get_packets(self):
        return self.packets
```

It is important to notice that even though the structure of the children is unknown, an interface
 is still created for them. As we will see later, it allows an external developer to later define
 their format as well as their converters.
 
Now that we have the models, we are ready to create the root converter:

```python
class XilinxBitstreamConverter(AbstractConverter):
    """
    Converter for a Xilinx FPGA bitstream

    :param BALContext context: The BAL context.
    """

    def __init__(self, context):
        super(XilinxBitstreamConverter, self).__init__(context)
        self.context = context

    def unpack(self, data_bytes):
        sync_marker = self.context.format.sync_word
        sync_marker_index = data_bytes.find(sync_marker)
        assert sync_marker_index >= 0, \
            "The sync marker is not present in the provided bitstream data"

        assert sync_marker_index + len(sync_marker) < len(data_bytes) - 2, \
            "The configuration data is expected to contain at least one word size worth of data"

        return XilinxBitstream(
            DataObject.create_packed(
                self.context,
                data_bytes[:sync_marker_index],
                XilinxBitstreamHeaderInterface
            ),
            DataObject.create_packed(
                self.context,
                data_bytes[sync_marker_index:sync_marker_index+len(sync_marker)],
                XilinxBitstreamSyncMarkerInterface,
            ),
            DataObject.create_packed(
                self.context,
                data_bytes[sync_marker_index + len(sync_marker):],
                XilinxPacketsInterface,
            )
        )

    def pack(self, data_model):
        """
        :param XilinxBitstream data_model:
        :rtype: bytes
        """
        assert isinstance(data_model, XilinxBitstream)
        return b"".join([
            data_model.get_header().pack(),
            self.context.format.sync_word,
            data_model.get_packets().pack()
        ])
```

This is already getting a bit more complicated. 
The converter takes a `BALContext` as an argument which implies that a converter instance must be 
dedicated to a specific bitstream.
The `unpack()` method does not instantiate any of its children `DataModel`, it only creates a 
`DataObject` that wraps the packed data for that model. 
It provides the `DataObject` with the interface of the wrapped data model.
The `DataObject` uses the interface to extract basic information about the packed data (i.e. type 
and description from the interface name and its docstring). 
It uses the interface when it is unpacked as well, looking up a converter implementation for that 
interface inside the `BALContext` (remember that it inherits from the `BALIoCContext`).
This is an important property as it allows the tree to be "lazily" unpacked. 
The user controls  exactly when a given child is unpacked (if it gets unpacked at all) which can 
lead to significantly better performances in many use cases.

Last but not least, we need a `BALContext` and `BALFactoryContext` implementation:

```python

class XilinxContext(BALContext):
    """
    :param Dict[Type[DataModel],Type[AbstractConverter]] converters_by_type:
    :param Dict[Type[AnalyzerInterface],Type[AbstractAnalyzer]] analyzers_by_type:
    :param Dict[Type[ModifierInterface],Type[AbstractModifier]] modifiers_by_type:
    :param bytes bytes: The bytes making up the bitstream.
    """
    def __init__(
            self,
            converters_by_type,
            analyzers_by_type,
            modifiers_by_type,
            bytes
    ):
        super(XilinxContext, self).__init__(
            converters_by_type,
            analyzers_by_type,
            modifiers_by_type
        )
        self._bitstream = DataObject.create_packed(self, bytes, XilinxBitstream)

    def get_data(self):
        """
        :rtype: DataObject[XilinxBitstream]
        """
        return self._bitstream


class XilinxContextFactory(BALContextFactory):
    def __init__(self):
        super(XilinxContextFactory, self).__init__()

    def create(self, data):
        """
        :param bytes bytes: The bytes for the Xilinx FPGA bitstream
        :rtype: XilinxContext
        """
        return XilinxContext(
            self._converters_by_type,
            self._analyzers_by_type,
            self._modifiers_by_type,
            data
        )
```

Since our Xilinx implementation is pretty limited, both the context and its factory are trivial. 

Let's see our implementation in action:

```python
import wget

context_factory = XilinxContextFactory()
# Register the XilinxBitsreamConverter
context_factory.register_converter(XilinxBitstream, XilinxBitstreamConverter)
lx9_bin = wget.download('https://redballoonsecurity.com/files/JwfEU4veQSNFao8h/lx9.bin')
with open(lx9_bin, "rb") as f:
    data = f.read()
context = context_factory.create(data)
bitstream_object = context.get_data()
print("Bitstream object: {}".format(bitstream_object))
print("Bitstream model type: {}".format(bitstream_object.get_model_type()))
print("Bitstream model description: {}".format(bitstream_object.get_model_description()))

print("\nUNPACKING\n")

bitstream_object.unpack()
print("Bitstream object: {}".format(bitstream_object))

print("\nHEADER\n")

header_object = bitstream_object.get_model().get_header()
print("Bitstream header object: {}".format(header_object))
print("Bitstream header model type: {}".format(header_object.get_model_type()))
print("Bitstream header model description: {}".format(header_object.get_model_description()))
```

This script should print:

```
Bitstream object: PackedXilinxBitstream(340604)
Bitstream model type: XilinxBitstream
Bitstream model description: The root model for a Xilinx bitstream. It contains a header and packets data objects.

UNPACKING

Bitstream object: XilinxBitstream({
  header: PackedXilinxBitstreamHeaderInterface(16), 
  sync_marker: PackedXilinxBitstreamSyncMarkerInterface(4), 
  packets: PackedXilinxPacketsInterface(340584), 
})

HEADER

Bitstream header object: PackedXilinxBitstreamHeaderInterface(16)
Bitstream header model type: XilinxBitstreamHeaderInterface
Bitstream header model description: The Xilinx bitstream header contains unknown information.
```

As you can see from the output, the BAL framework already has a bunch of information about the 
structure of the bitstream. 
It uses the docstring defined on the interfaces to pull a description of the data models, even if
they cannot be unpacked yet. 

This is it for this guide. 
Your next steps might be to implement the XilinxPacketsInterface, XilinxBitstreamHeaderInterface, 
and XilinxBitstreamSyncMarkerInterface interfaces and implement their respective converters. 
If you want to learn more about writing a full chain of converters, analyzers and modifiers, 
head over to the [bal-xilinx](https://github.com/RedBalloonShenanigans/bal-xilinx) project.




