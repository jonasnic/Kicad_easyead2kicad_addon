"""KiCad scripting entrypoint for the EasyEDA to KiCad plugin."""

from plugins import EasyEDA2KiCadPlugin


plugin = EasyEDA2KiCadPlugin()
if hasattr(plugin, "register"):
    plugin.register()