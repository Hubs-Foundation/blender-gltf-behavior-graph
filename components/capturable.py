from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import NodeType, PanelType, Category
from ..utils import do_register, do_unregister


class Capturable(HubsComponent):
    _definition = {
        'name': 'capturable',
        'display_name': 'BG Capturable',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'version': (1, 0, 0),
        'icon': 'OBJECT_DATA'
    }


def register():
    do_register(Capturable)


def unregister():
    do_unregister(Capturable)
