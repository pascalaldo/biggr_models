from bigg_models.handlers import general
from bigg_models import queries

from cobradb.parse import split_compartment
import re


class UniversalMetaboliteListHandler(general.PageableHandler):
    def get(self):
        # get arguments
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = general.safe_query(queries.get_universal_metabolites, **kwargs)

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
            "results_count": general.safe_query(
                queries.get_universal_metabolites_count
            ),
        }

        self.write(result)
        self.finish()


class UniversalMetaboliteListDisplayHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def get(self):
        data = {
            "results": {"metabolites": "ajax"},
            "hide_organism": True,
            "page_name": "universal_metabolite_list",
        }
        self.write(self.template.render(data))
        self.finish()


class UniversalMetaboliteHandler(general.BaseHandler):
    template = general.env.get_template("universal_metabolite.html")

    def get(self, met_bigg_id):
        try:
            result = general.safe_query(queries.get_metabolite, met_bigg_id)
        except queries.RedirectError as e:
            self.redirect(re.sub(self.request.path, "%s$" % met_bigg_id, e.args[0]))
        else:
            self.return_result(result)


class MetaboliteListHandler(general.PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the queries
        raw_results = general.safe_query(
            queries.get_model_metabolites, model_bigg_id, **kwargs
        )
        # add the URL
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [
                dict(
                    x,
                    link_urls={
                        "bigg_id": "/models/{model_bigg_id}/metabolites/{bigg_id}_{compartment_bigg_id}".format(
                            **x
                        )
                    },
                )
                for x in raw_results
            ]
        result = {
            "results": raw_results,
            "results_count": general.safe_query(
                queries.get_model_metabolites_count,
                model_bigg_id,
            ),
        }

        self.write(result)
        self.finish()


class MetabolitesListDisplayHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def get(self, model_bigg_id):
        data = {
            "results": {"metabolites": "ajax"},
            "page_name": "metabolite_list",
        }
        self.write(self.template.render(data))
        self.finish()


class MetaboliteHandler(general.BaseHandler):
    template = general.env.get_template("metabolite.html")

    def get(self, model_bigg_id, comp_met_id):
        met_bigg_id, compartment_bigg_id = split_compartment(comp_met_id)
        results = general.safe_query(
            queries.get_model_comp_metabolite,
            met_bigg_id,
            compartment_bigg_id,
            model_bigg_id,
        )
        self.return_result(results)
