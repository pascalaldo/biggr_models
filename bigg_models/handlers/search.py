from bigg_models.handlers import general
from bigg_models import queries
import simplejson as json

from cobradb.parse import hash_metabolite_dictionary
from tornado.web import HTTPError


class SearchHandler(general.BaseHandler):
    def get(self):
        # get arguments
        query_string = self.get_argument("query")
        page = self.get_argument("page", None)
        size = self.get_argument("size", None)
        search_type = self.get_argument("search_type", None)
        multistrain_off = self.get_argument("multistrain", None) == "off"
        include_link_urls = "include_link_urls" in self.request.query_arguments

        # defaults
        sort_column = None
        sort_direction = "ascending"

        # get the sorting column
        columns = general._parse_col_arg(self.get_argument("columns", None))
        sort_column, sort_direction = general._get_col_name(
            self.request.query_arguments,
            columns,
            sort_column,
            sort_direction,
        )

        # run the queries
        session = queries.Session()
        result = None

        if search_type == "reactions":
            # reactions
            raw_results = queries.search_for_universal_reactions(
                query_string,
                session,
                page,
                size,
                sort_column,
                sort_direction,
                multistrain_off,
            )
            if include_link_urls:
                raw_results = [
                    dict(
                        x,
                        link_urls={
                            "bigg_id": "/universal/reactions/{bigg_id}".format(**x)
                        },
                    )
                    for x in raw_results
                ]
            result = {
                "results": [
                    dict(x, model_bigg_id="Universal", organism="") for x in raw_results
                ],
                "results_count": queries.search_for_universal_reactions_count(
                    query_string,
                    session,
                    multistrain_off,
                ),
            }

        elif search_type == "metabolites":
            raw_results = queries.search_for_universal_metabolites(
                query_string,
                session,
                page,
                size,
                sort_column,
                sort_direction,
                multistrain_off,
            )
            if include_link_urls:
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
                "results": [
                    dict(x, model_bigg_id="Universal", organism="") for x in raw_results
                ],
                "results_count": queries.search_for_universal_metabolites_count(
                    query_string,
                    session,
                    multistrain_off,
                ),
            }

        elif search_type == "genes":
            raw_results = queries.search_for_genes(
                query_string,
                session,
                page,
                size,
                sort_column,
                sort_direction,
                multistrain_off=multistrain_off,
            )
            if include_link_urls:
                raw_results = [
                    dict(
                        x,
                        link_urls={
                            "bigg_id": "/models/{model_bigg_id}/genes/{bigg_id}".format(
                                **x
                            )
                        },
                    )
                    for x in raw_results
                ]

            result = {
                "results": raw_results,
                "results_count": queries.search_for_genes_count(
                    query_string,
                    session,
                    multistrain_off=multistrain_off,
                ),
            }

        elif search_type == "models":
            raw_results = queries.search_for_models(
                query_string,
                session,
                page,
                size,
                sort_column,
                sort_direction,
                multistrain_off,
            )
            if include_link_urls:
                raw_results = [
                    dict(
                        x,
                        link_urls={
                            "bigg_id": "/models/{bigg_id}".format(**x),
                            "metabolite_count": "/models/{bigg_id}/metabolites".format(
                                **x
                            ),
                            "reaction_count": "/models/{bigg_id}/reactions".format(**x),
                            "gene_count": "/models/{bigg_id}/genes".format(**x),
                        },
                    )
                    for x in raw_results
                ]

            result = {
                "results": raw_results,
                "results_count": queries.search_for_models_count(
                    query_string,
                    session,
                    multistrain_off,
                ),
            }

        else:
            raise HTTPError(400, "Bad search_type %s" % search_type)

        session.close()
        self.write(result)
        self.finish()


class SearchDisplayHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def get(self):
        data = {
            "results": {
                "models": "ajax",
                "reactions": "ajax",
                "metabolites": "ajax",
                "genes": "ajax",
            },
            "tablesorter_size": 20,
        }
        self.write(self.template.render(data))
        self.finish()


class AdvancedSearchHandler(general.BaseHandler):
    template = general.env.get_template("advanced_search.html")

    def get(self):
        model_list = general.safe_query(queries.get_model_list)
        database_sources = general.safe_query(queries.get_database_sources)

        self.write(
            self.template.render(
                {"models": model_list, "database_sources": database_sources}
            )
        )
        self.finish()


class AdvancedSearchExternalIDHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def post(self):
        query_string = self.get_argument("query", "")
        database_source = self.get_argument("database_source", "")
        session = queries.Session()
        metabolites = queries.get_metabolites_for_database_id(
            session, query_string, database_source
        )
        reactions = queries.get_reactions_for_database_id(
            session, query_string, database_source
        )
        genes = queries.get_genes_for_database_id(
            session, query_string, database_source
        )
        session.close()
        dictionary = {
            "results": {
                "metabolites": metabolites,
                "reactions": reactions,
                "genes": genes,
            },
            "no_pager": True,
            "hide_organism": True,
            "page_name": "advanced_search_external_id_results",
        }

        self.write(self.template.render(dictionary))
        self.finish()


class AdvancedSearchResultsHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def post(self):
        query_strings = [
            x.strip() for x in self.get_argument("query", "").split(",") if x != ""
        ]
        # run the queries
        session = queries.Session()

        def checkbox_arg(name):
            return self.get_argument(name, None) == "on"

        all_models = queries.get_model_list(session)
        model_list = [m for m in all_models if checkbox_arg(m)]
        include_metabolites = checkbox_arg("include_metabolites")
        include_reactions = checkbox_arg("include_reactions")
        include_genes = checkbox_arg("include_genes")
        metabolite_results = []
        reaction_results = []
        gene_results = []

        # genes
        for query_string in query_strings:
            if include_genes:
                gene_results += queries.search_for_genes(
                    query_string, session, limit_models=model_list
                )
            if include_reactions:
                reaction_results += queries.search_for_reactions(
                    query_string, session, limit_models=model_list
                )
            if include_metabolites:
                metabolite_results += queries.search_for_metabolites(
                    query_string, session, limit_models=model_list
                )
        result = {
            "results": {
                "reactions": reaction_results,
                "metabolites": metabolite_results,
                "genes": gene_results,
            },
            "no_pager": True,
            "page_name": "advanced_search_results",
        }

        session.close()
        self.write(self.template.render(result))
        self.finish()


class AdvancedSearchSequences(general.BaseHandler):
    def post(self):
        reaction_bigg_id = self.get_argument("query", "")
        session = queries.Session()
        results = queries.sequences_for_reaction(reaction_bigg_id, session)
        session.close()
        self.set_header("Content-Type", "application/octet-stream")
        self.write(json.dumps(results))
        self.finish()
