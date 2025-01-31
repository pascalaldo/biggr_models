from bigg_models.handlers import general
from bigg_models import queries
from os import path


# Models
class ModelListHandler(general.PageableHandler):
    def get(self):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the queries
        raw_results = general.safe_query(queries.get_models, **kwargs)
        print(raw_results)
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [
                dict(
                    x,
                    link_urls={
                        "bigg_id": "/models/{bigg_id}".format(**x),
                        "metabolite_count": "/models/{bigg_id}/metabolites".format(**x),
                        "reaction_count": "/models/{bigg_id}/reactions".format(**x),
                        "gene_count": "/models/{bigg_id}/genes".format(**x),
                    },
                )
                for x in raw_results
            ]
        result = {
            "results": raw_results,
            "results_count": general.safe_query(queries.get_models_count, **kwargs),
        }

        self.write(result)
        self.finish()


class ModelsListDisplayHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def get(self):
        template_data = {"results": {"models": "ajax"}}
        self.write(self.template.render(template_data))
        self.finish()


class ModelDownloadHandler(general.BaseHandler):
    def get(self, model_bigg_id):
        with open(
            path.join(general.directory, "static", "models", "%s.json" % model_bigg_id)
        ) as f:
            json_str = f.read()
        self.write(json_str)
        self.set_header("Content-type", "application/json; charset=utf-8")
        self.finish()


class ModelHandler(general.BaseHandler):
    template = general.env.get_template("model.html")

    def get(self, model_bigg_id):
        result = general.safe_query(
            queries.get_model_and_counts,
            model_bigg_id,
            static_model_dir=general.static_model_dir,
            static_multistrain_dir=general.static_multistrain_dir,
        )
        self.return_result(result)
