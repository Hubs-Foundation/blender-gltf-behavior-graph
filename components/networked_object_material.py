from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import NodeType, PanelType
from ..utils import do_register, do_unregister


class NetworkedObjectMaterial(HubsComponent):
    _definition = {
        'name': 'networked-object-material',
        'display_name': 'BG Networked Object Material',
        'node_type': NodeType.NODE,
        'panel_type': [PanelType.OBJECT],
        'icon': 'MATERIAL_DATA',
        'version': (1, 0, 0)
    }

    def draw(self, context, layout, panel):
        row = layout.row()
        row.label(text="Network material changes on this object.")


def register():
    do_register(NetworkedObjectMaterial)


def unregister():
    do_unregister(NetworkedObjectMaterial)
