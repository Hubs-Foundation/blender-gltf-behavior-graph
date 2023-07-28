from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import Category, NodeType, PanelType
from ..utils import do_register, do_unregister


class NetworkedTransform(HubsComponent):
    _definition = {
        'name': 'networked-transform',
        'display_name': 'BG Networked Transform',
        'category': Category.OBJECT,
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'NODETREE',
        'version': (1, 0, 0)
    }


def register():
    do_register(NetworkedTransform)


def unregister():
    do_unregister(NetworkedTransform)
