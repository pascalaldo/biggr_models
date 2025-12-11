from cobradb.api.escher import ESCHER_MODULE_DEFINITIONS
from bigg_models.handlers import utils
from bigg_models.handlers.object_handlers import MODELS_CLASS_MAP, MODELS_PROPERTY_MAP


class DataAccessPageHandler(utils.BaseHandler):
    template = utils.env.get_template("data_access.html")

    def get(self):
        data = {
            "biggr_address": "biggr.org",
            "data_models": MODELS_CLASS_MAP.keys(),
            "data_attributes": MODELS_PROPERTY_MAP.keys(),
            "escher_maps": ESCHER_MODULE_DEFINITIONS.keys(),
        }
        self.return_result(data)
