from bal.context import BALContext
from bal.context_ioc import AbstractAnalyzer
from bal.data_model import ClassModel, ValueModel, DictModel, ArrayModel
from bal.data_object import DataObject


class VisualizerAnalyzer(AbstractAnalyzer):
    """
    Generate nested native objects (ie objects that can be fed to serialization libraries) that
    are used to configure the visualizer to display the bitstream.

    :param BALContext context: The configured context
    """
    def __init__(self, context):
        super(VisualizerAnalyzer, self).__init__(context)
        self.context = context

    def _is_data_object_empty(self, data_object):
        """
        Determine if the provided data object is empty (ie all its bytes are set to 0)

        :param DataObject data_object:
        :rtype: bool
        """
        is_empty = True
        for byte in data_object.get_bytes():
            if byte == 0 or byte == b"\x00":
                continue
            is_empty = False
            break
        return is_empty

    def _traverse(self, data_object):
        """
        Recurse through the descendant data objects, building a visualizer config node for each.

        :param DataObject data_object:
        :rtype: Dict[str, Any]
        """
        wrapper = {
            "type": data_object.get_model_type(),
            "implementation": data_object.get_model_implementation(),
            "description": data_object.get_model_description(),
            "bit_size": data_object.get_bit_size(),
            "unpacked": data_object.is_convertible() or data_object.is_unpacked(),
        }

        if not data_object.is_convertible() and not data_object.is_unpacked():
            wrapper["is_empty"] = self._is_data_object_empty(data_object)
            return wrapper

        data_model = data_object.unpack()

        if isinstance(data_model, ValueModel):
            wrapper["value_name"] = data_model.value_name
            wrapper["value_description"] = data_model.value_description
            wrapper["value"] = data_model.get_value()
            wrapper["is_empty"] = data_model.get_value() == "" or data_model.get_value() == 0
        elif isinstance(data_model, ArrayModel):
            wrapper["children"] = [
                self._traverse(c)
                for i, c in data_model.iterate()
                if c is not None
            ]
            wrapper["is_empty"] = all([
                item["is_empty"] is True for item in wrapper["children"]
            ])
        elif isinstance(data_model, DictModel) or isinstance(data_model, ClassModel):
            wrapper["children"] = [
                self._traverse(v)
                for k, v in data_model.iterate()
                if v is not None
            ]
            wrapper["is_empty"] = all([
                item["is_empty"] is True for item in wrapper["children"]
            ])
        else:
            raise ValueError("Unknown data object model")
        return wrapper