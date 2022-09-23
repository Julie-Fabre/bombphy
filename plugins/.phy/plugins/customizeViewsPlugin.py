# import from plugins/feature_view_custom_grid.py
"""Show how to customize the subplot grid specifiction in the feature view."""

import re
from phy import IPlugin, connect
from phy.cluster.views import CorrelogramView
import pickle



class customizeViewsPlugin(IPlugin):
    def attach_to_controller(self, controller):
        @connect


        def on_view_attached(view, gui):
            if isinstance(view, CorrelogramView):
                # We change the specification of the subplots here.
                rpvs_dict = controller.context.load_memcache('qMetricsPlugin.fractionRPV')
                rpvs = list(rpvs_dict.items())

                view.set_rpv(rpvs)
