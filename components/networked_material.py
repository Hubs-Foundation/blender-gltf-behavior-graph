from io_hubs_addon.components.hubs_component import HubsComponent
from io_hubs_addon.components.types import NodeType, PanelType
from ..utils import do_register, do_unregister


class NetworkedMaterial(HubsComponent):
    _definition = {
        'name': 'networked-material',
        'display_name': 'Networked Material',
        'node_type': NodeType.MATERIAL,
        'panel_type': [PanelType.MATERIAL],
        'icon': 'MATERIAL_DATA',
        'deps': ['networked'],
        'version': (1, 0, 0)
    }

    def gather(self, export_settings, object):
        return {
            "networked": "true"
        }

    def draw(self, context, layout, panel):
        row = layout.row()
        row.label(text="Network material updates")


def register():
    do_register(NetworkedMaterial)


def unregister():
    do_unregister(NetworkedMaterial)
