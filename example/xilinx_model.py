from bal.data_model import DataModel, ClassModel
from bal.data_object import DataObject


class XilinxPacketsInterface(DataModel):
    """
    An array of Xilinx register configuration packet.
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
    The root model for a Xilinx bitstream. It contains a header and packets data objects.
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