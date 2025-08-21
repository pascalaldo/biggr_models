from bigg_models.handlers import utils
from bigg_models.queries import model_queries
from os import path


# Models
class ModelListHandler(utils.PageableHandler):
    def get(self):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the model_queries
        raw_results = utils.safe_query(model_queries.get_models, **kwargs)
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
            "results_count": utils.safe_query(model_queries.get_models_count, **kwargs),
        }

        self.write(result)
        self.finish()


class ModelsListDisplayHandler(utils.BaseHandler):
    template = utils.env.get_template("listview.html")

    def get(self):
        template_data = {"results": {"models": "ajax"}}
        self.write(self.template.render(template_data))
        self.finish()


class ModelDownloadHandler(utils.BaseHandler):
    def get(self, model_bigg_id):
        with open(
            path.join(utils.directory, "static", "models", "%s.json" % model_bigg_id)
        ) as f:
            json_str = f.read()
        self.write(json_str)
        self.set_header("Content-type", "application/json; charset=utf-8")
        self.finish()


class ModelHandler(utils.BaseHandler):
    template = utils.env.get_template("model.html")

    def get(self, model_bigg_id):
        result = utils.safe_query(
            model_queries.get_model_and_counts,
            model_bigg_id,
            static_model_dir=utils.static_model_dir,
            static_multistrain_dir=utils.static_multistrain_dir,
        )
        result["breadcrumbs"] = [
            ("Home", "/"),
            ("Models", "/models/"),
            (model_bigg_id, f"/models/{model_bigg_id}"),
        ]

        result["model_metrics"] = [
            {
                "label": "Metabolites",
                "link": f"/models/{model_bigg_id}/metabolites",
                "value": result["metabolite_count"],
            },
            {
                "label": "Reactions",
                "link": f"/models/{model_bigg_id}/reactions",
                "value": result["reaction_count"],
            },
            {
                "label": "Genes",
                "link": f"/models/{model_bigg_id}/genes",
                "value": result["gene_count"],
            },
        ]

        result["model_properties"] = []
        if result["genome_name"] is not None:
            result["model_properties"].append(
                {
                    "label": "Genome",
                    "link": f"/genomes/{result['genome_ref_string']}",
                    "value": result["genome_name"],
                }
            )
        if result["reference_type"] == "pmid":
            result["model_properties"].append(
                {
                    "label": "Publication PMID",
                    "link": f"https://www.ncbi.nlm.nih.gov/pubmed/{result['reference_id']}",
                    "value": result["reference_id"],
                }
            )
        elif result["reference_type"] == "doi":
            result["model_properties"].append(
                {
                    "label": "Publication DOI",
                    "link": f"https://dx.doi.org/{result['reference_id']}",
                    "value": result["reference_id"],
                }
            )

        self.return_result(result)
