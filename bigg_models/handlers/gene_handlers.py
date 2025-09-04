from bigg_models.handlers import utils
from bigg_models.queries import gene_queries


class GeneListHandler(utils.PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = utils.safe_query(
            gene_queries.get_model_genes, model_bigg_id, **kwargs
        )

        # add the URL
        if "include_link_urls" in self.request.query_arguments:
            raw_results = [
                dict(
                    x,
                    link_urls={
                        "bigg_id": "/models/{model_bigg_id}/genes/{bigg_id}".format(**x)
                    },
                )
                for x in raw_results
            ]
        result = {
            "results": raw_results,
            "results_count": utils.safe_query(
                gene_queries.get_model_genes_count, model_bigg_id
            ),
        }
        self.write(result)
        self.finish()


class GeneListDisplayHandler(utils.BaseHandler):
    template = utils.env.get_template("listview.html")

    def get(self, model_bigg_id):
        data = {
            "results": {"genes": "ajax"},
            "page_name": "gene_list",
        }
        self.write(self.template.render(data))
        self.finish()


class GeneHandler(utils.BaseHandler):
    template = utils.env.get_template("gene.html")

    def get(self, model_bigg_id, gene_bigg_id):
        result = utils.safe_query(
            gene_queries.get_model_gene, gene_bigg_id, model_bigg_id
        )
        self.return_result(result)
