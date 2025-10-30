from bigg_models.handlers import utils
from bigg_models.queries import reaction_queries, utils as query_utils
import re
from cobradb.parse import hash_metabolite_dictionary


# reactions
class UniversalReactionListHandler(utils.PageableHandler):
    def get(self):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the reaction_queries
        raw_results = utils.safe_query(
            reaction_queries.get_universal_reactions, **kwargs
        )

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
            "results_count": utils.safe_query(
                reaction_queries.get_universal_reactions_count
            ),
        }

        self.write(result)
        self.finish()


class UniversalReactionListDisplayHandler(utils.BaseHandler):
    template = utils.env.get_template("listview.html")

    def get(self):
        dictionary = {
            "results": {"reactions": "ajax"},
            "hide_organism": True,
            "page_name": "universal_reaction_list",
        }
        dictionary["breadcrumbs"] = [
            ("Home", "/"),
            ("Universal", None),
            ("Reactions", "/universal/reactions/"),
        ]

        self.write(self.template.render(dictionary))
        self.finish()


class UniversalReactionHandler(utils.BaseHandler):
    template = utils.env.get_template("universal_reaction.html")

    def get(self, reaction_bigg_id):
        try:
            result = utils.do_safe_query(
                reaction_queries.get_universal_reaction_and_models, reaction_bigg_id
            )
        except query_utils.RedirectError as e:
            self.redirect(
                re.sub(self.request.path, "%s$" % reaction_bigg_id, e.args[0])
            )
        else:
            result["breadcrumbs"] = [
                ("Home", "/"),
                ("Universal", None),
                ("Reactions", f"/universal/reactions/"),
                (
                    utils.format_bigg_id(reaction_bigg_id, "reaction"),
                    f"/universal/reactions/{reaction_bigg_id}",
                ),
            ]

            self.return_result(result)


class ReactionListHandler(utils.PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = utils.safe_query(
            reaction_queries.get_model_reactions, model_bigg_id, **kwargs
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
            "results_count": utils.safe_query(
                reaction_queries.get_model_reactions_count,
                model_bigg_id,
            ),
        }

        self.write(result)
        self.finish()


class ReactionListDisplayHandler(utils.BaseHandler):
    template = utils.env.get_template("listview.html")

    def get(self, model_bigg_id):
        results = {
            "results": {"reactions": "ajax"},
            "page_name": "reaction_list",
        }
        results["breadcrumbs"] = [
            ("Home", "/"),
            ("Models", "/models/"),
            (model_bigg_id, f"/models/{model_bigg_id}"),
            ("Reactions", f"/models/{model_bigg_id}/reactions/"),
        ]

        self.return_result(results)


class ReactionHandler(utils.BaseHandler):
    template = utils.env.get_template("reaction.html")

    def get(self, model_bigg_id, reaction_bigg_id):
        results = utils.safe_query(
            reaction_queries.get_model_reaction, model_bigg_id, reaction_bigg_id
        )

        results["breadcrumbs"] = [
            ("Home", "/"),
            ("Models", "/models/"),
            (model_bigg_id, f"/models/{model_bigg_id}/"),
            ("Reactions", f"/models/{model_bigg_id}/reactions/"),
            (
                utils.format_bigg_id(reaction_bigg_id, "reaction"),
                f"/models/{model_bigg_id}/reactions/{reaction_bigg_id}",
            ),
        ]

        self.return_result(results)


class ReactionWithStoichHandler(utils.BaseHandler):
    def get(self):
        metabolite_dict = {
            k: float(v[0]) for k, v in self.request.query_arguments.items()
        }
        hash = hash_metabolite_dictionary(metabolite_dict)
        session = utils.Session()
        try:
            results = {
                "results": [reaction_queries.reaction_with_hash(hash, session)],
                "results_count": 1,
            }
        except query_utils.NotFoundError:
            results = {"results": [], "results_count": 0}
        session.close()
        self.write(results)
        self.finish()
