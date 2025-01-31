from bigg_models.handlers import general
from bigg_models import queries
import re
from cobradb.parse import hash_metabolite_dictionary


# reactions
class UniversalReactionListHandler(general.PageableHandler):
    def get(self):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the queries
        raw_results = general.safe_query(queries.get_universal_reactions, **kwargs)

        if "include_link_urls" in self.request.query_arguments:
            raw_results = [
                dict(
                    x,
                    link_urls={"bigg_id": "/universal/reactions/{bigg_id}".format(**x)},
                )
                for x in raw_results
            ]
        result = {
            "results": [dict(x, model_bigg_id="Universal") for x in raw_results],
            "results_count": general.safe_query(queries.get_universal_reactions_count),
        }

        self.write(result)
        self.finish()


class UniversalReactionListDisplayHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def get(self):
        dictionary = {
            "results": {"reactions": "ajax"},
            "hide_organism": True,
            "page_name": "universal_reaction_list",
        }
        self.write(self.template.render(dictionary))
        self.finish()


class UniversalReactionHandler(general.BaseHandler):
    template = general.env.get_template("universal_reaction.html")

    def get(self, reaction_bigg_id):
        try:
            result = general.safe_query(
                queries.get_reaction_and_models, reaction_bigg_id
            )
        except queries.RedirectError as e:
            self.redirect(
                re.sub(self.request.path, "%s$" % reaction_bigg_id, e.args[0])
            )
        else:
            self.return_result(result)


class ReactionListHandler(general.PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = general.safe_query(
            queries.get_model_reactions, model_bigg_id, **kwargs
        )
        # add the URL
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [
                dict(
                    x,
                    link_urls={
                        "bigg_id": "/models/{model_bigg_id}/reactions/{bigg_id}".format(
                            **x
                        )
                    },
                )
                for x in raw_results
            ]
        result = {
            "results": raw_results,
            "results_count": general.safe_query(
                queries.get_model_reactions_count,
                model_bigg_id,
            ),
        }

        self.write(result)
        self.finish()


class ReactionListDisplayHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def get(self, model_bigg_id):
        results = {
            "results": {"reactions": "ajax"},
            "page_name": "reaction_list",
        }
        self.return_result(results)


class ReactionHandler(general.BaseHandler):
    template = general.env.get_template("reaction.html")

    def get(self, model_bigg_id, reaction_bigg_id):
        results = general.safe_query(
            queries.get_model_reaction, model_bigg_id, reaction_bigg_id
        )
        self.return_result(results)


class ReactionWithStoichHandler(general.BaseHandler):
    def get(self):
        metabolite_dict = {
            k: float(v[0]) for k, v in self.request.query_arguments.items()
        }
        hash = hash_metabolite_dictionary(metabolite_dict)
        session = queries.Session()
        try:
            results = {
                "results": [queries.reaction_with_hash(hash, session)],
                "results_count": 1,
            }
        except queries.NotFoundError:
            results = {"results": [], "results_count": 0}
        session.close()
        self.write(results)
        self.finish()
