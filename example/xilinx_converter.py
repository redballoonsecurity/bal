import six

from bal.context_ioc import AbstractConverter
from bal.data_object import DataObject
from example.xilinx_model import XilinxBitstream, XilinxBitstreamHeaderInterface, \
    XilinxBitstreamSyncMarkerInterface, XilinxPacketsInterface


def hex_to_bytes(hex):
    """
    Convert a hex value to the bytes representation used by the interpreter.

    :param str hex:
    :rtype: bytes
    """
    if six.PY2:
        return hex.decode("hex")
    else:
        return bytes.fromhex(hex)


class XilinxBitstreamConverter(AbstractConverter):
    """
    Converter for a Xilinx FPGA bitstream

    :param BALContext context: The BAL context.
    """

    def __init__(self, context):
        super(XilinxBitstreamConverter, self).__init__(context)
        self.context = context

    def unpack(self, data_bytes):
        sync_marker = hex_to_bytes("AA995566")
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