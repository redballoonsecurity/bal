from example.xilinx_context import XilinxContextFactory
from example.xilinx_converter import XilinxBitstreamConverter
from example.xilinx_model import XilinxBitstream

import wget

def run():
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

if __name__ == "__main__":
    run()
