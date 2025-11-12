from tornado.web import HTTPError
from bigg_models.handlers import utils
from escher import plots
import json
from cobradb.api.escher import ESCHER_MODULE_DEFINITIONS

from bigg_models.queries.escher_queries import get_model_reactions_for_escher_map


def builder_to_html_string(builder: plots.Builder):
    # This is the same as the Builder.save_html method,
    # except it does not write the html to a file.
    options = {}
    for key in builder.traits(option=True):
        val = getattr(builder, key)
        if val is not None:
            options[key] = val
    options_json = json.dumps(options)

    template = plots.env.get_template("standalone.html")
    embedded_css_b64 = (
        plots.b64dump(builder.embedded_css)
        if builder.embedded_css is not None
        else None
    )
    html = template.render(
        escher_url=plots.get_url("escher_min"),
        embedded_css_b64=embedded_css_b64,
        map_data_json_b64=plots.b64dump(builder._loaded_map_json),
        model_data_json_b64=plots.b64dump(builder._loaded_model_json),
        options_json_b64=plots.b64dump(options_json),
    )

    return html.encode("utf-8")


class EscherHandler(utils.BaseHandler):
    name = None

    def initialize(self, **kwargs):
        self.name = kwargs.get("name")

    def prepare(self):
        self.api = self.path_kwargs.get("api") is not None

    def get(self, model_bigg_id: str, map_bigg_id: str, **kwargs):
        escher_module = ESCHER_MODULE_DEFINITIONS.get(map_bigg_id)
        if escher_module is None:
            raise HTTPError(status_code=404, reason="Map BiGG ID not found.")
        model_reactions = utils.do_safe_query(
            get_model_reactions_for_escher_map, model_bigg_id, map_bigg_id
        )
        escher_map = utils.do_safe_query(escher_module.build_map, model_reactions)
        escher_map.fit_canvas(expand_only=True)
        escher_map_json = escher_map.to_escher()
        if self.api:
            self.write(escher_map_json)
            self.finish()
        else:
            self.write_map(json.dumps(escher_map_json))

    def write_map(self, map_json: str):
        builder = plots.Builder(map_json=map_json)
        html = builder_to_html_string(builder)
        self.write(html)
