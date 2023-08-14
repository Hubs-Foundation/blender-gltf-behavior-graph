from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import NodeType, PanelType
from ..utils import do_register, do_unregister


class Capturable(HubsComponent):
    _definition = {
        'name': 'capturable',
        'display_name': 'Capturable',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'version': (1, 0, 0),
        'deps': ['networked-transform']
    }


def register():
    do_register(Capturable)


def unregister():
    do_unregister(Capturable)
