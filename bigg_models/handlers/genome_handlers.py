from bigg_models.handlers import utils
from bigg_models.queries import genome_queries


# Genomes
class GenomeListHandler(utils.PageableHandler):
    def get(self):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        # run the model_queries
        raw_results = utils.safe_query(genome_queries.get_genomes, **kwargs)
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [
                dict(
                    x,
                    link_urls={
                        "name": f"/genomes/{x['genome_ref_string']}",
                    },
                )
                for x in raw_results
            ]
        result = {
            "results": raw_results,
            "results_count": utils.safe_query(
                genome_queries.get_genomes_count, **kwargs
            ),
        }

        self.write(result)
        self.finish()


class GenomeListDisplayHandler(utils.BaseHandler):
    template = utils.env.get_template("listview.html")

    def get(self):
        template_data = {"results": {"genomes": "ajax"}}
        template_data["breadcrumbs"] = [("Home", "/"), ("Genomes", "/genomes/")]
        self.write(self.template.render(template_data))
        self.finish()


class GenomeHandler(utils.BaseHandler):
    template = utils.env.get_template("genome.html")

    def get(self, genome_ref_string):
        result = utils.safe_query(
            genome_queries.get_genome_and_models, genome_ref_string
        )
        result["breadcrumbs"] = [
            ("Home", "/"),
            ("Genomes", "/genomes/"),
            (result["name"], f"/genomes/{genome_ref_string}"),
        ]
        self.return_result(result)
