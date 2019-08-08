from bal.context import BALContext, BALContextFactory
from bal.data_object import DataObject
from example.xilinx_model import XilinxBitstream


class XilinxContext(BALContext):
    """
    :param Dict[Type[ConverterInterface],Type[AbstractConverter]] converters_by_type:
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