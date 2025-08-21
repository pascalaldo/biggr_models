from bigg_models.handlers import utils
from bigg_models.queries import metabolite_queries, utils as query_utils

from cobradb.parse import split_compartment
import re


class UniversalMetaboliteListHandler(utils.PageableHandler):
    def get(self):
        # get arguments
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = utils.safe_query(
            metabolite_queries.get_universal_metabolites, **kwargs
        )

        # add links and universal
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [
                dict(
                    x,
                    link_urls={
                        "bigg_id": "/universal/metabolites/{bigg_id}".format(**x)
                    },
                )
                for x in raw_results
            ]
        result = {
            "results": [dict(x, model_bigg_id="Universal") for x in raw_results],
            "results_count": utils.safe_query(
                metabolite_queries.get_universal_metabolites_count
            ),
        }

        self.write(result)
        self.finish()


class UniversalMetaboliteListDisplayHandler(utils.BaseHandler):
    template = utils.env.get_template("listview.html")

    def get(self):
        data = {
            "results": {"metabolites": "ajax"},
            "hide_organism": True,
            "page_name": "universal_metabolite_list",
        }
        data["breadcrumbs"] = [
            ("Home", "/"),
            ("Universal", None),
            ("Metabolites", "/universal/metabolites/"),
        ]
        self.write(self.template.render(data))
        self.finish()


class UniversalMetaboliteHandler(utils.BaseHandler):
    template = utils.env.get_template("universal_metabolite.html")

    def get(self, met_bigg_id):
        try:
            result = utils.safe_query(metabolite_queries.get_metabolite, met_bigg_id)
        except query_utils.RedirectError as e:
            self.redirect(re.sub(self.request.path, "%s$" % met_bigg_id, e.args[0]))
        else:
            result["breadcrumbs"] = [
                ("Home", "/"),
                ("Universal", None),
                ("Metabolites", f"/universal/metabolites/"),
                (met_bigg_id, f"/universal/metabolites/{met_bigg_id}"),
            ]
            self.return_result(result)


class MetaboliteListHandler(utils.PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the metabolite_queries
        raw_results = utils.safe_query(
            metabolite_queries.get_model_metabolites, model_bigg_id, **kwargs
        )
        # add the URL
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [
                dict(
                    x,
                    link_urls={
                        "bigg_id": "/models/{model_bigg_id}/metabolites/{bigg_id}".format(
                            **x
                        )
                    },
                )
                for x in raw_results
            ]
        result = {
            "results": raw_results,
            "results_count": utils.safe_query(
                metabolite_queries.get_model_metabolites_count,
                model_bigg_id,
            ),
        }

        self.write(result)
        self.finish()


class MetabolitesListDisplayHandler(utils.BaseHandler):
    template = utils.env.get_template("listview.html")

    def get(self, model_bigg_id):
        data = {
            "results": {"metabolites": "ajax"},
            "page_name": "metabolite_list",
        }
        data["breadcrumbs"] = [
            ("Home", "/"),
            ("Models", "/models/"),
            (model_bigg_id, f"/models/{model_bigg_id}"),
            ("Metabolites", f"/models/{model_bigg_id}/metabolites/"),
        ]

        self.write(self.template.render(data))
        self.finish()


class MetaboliteHandler(utils.BaseHandler):
    template = utils.env.get_template("metabolite.html")

    def get(self, model_bigg_id, comp_met_id):
        results = utils.safe_query(
            metabolite_queries.get_model_comp_metabolite,
            comp_met_id,
            model_bigg_id,
        )
        results["breadcrumbs"] = [
            ("Home", "/"),
            ("Models", "/models/"),
            (model_bigg_id, f"/models/{model_bigg_id}/"),
            ("Metabolites", f"/models/{model_bigg_id}/metabolites/"),
            (comp_met_id, f"/models/{model_bigg_id}/metabolites/{comp_met_id}"),
        ]
        self.return_result(results)
