from bigg_models.handlers import general
from bigg_models import queries


class GeneListHandler(general.PageableHandler):
    def get(self, model_bigg_id):
        kwargs = self._get_pager_args(default_sort_column="bigg_id")

        raw_results = general.safe_query(
            queries.get_model_genes, model_bigg_id, **kwargs
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
            "results_count": general.safe_query(
                queries.get_model_genes_count, model_bigg_id
            ),
        }
        self.write(result)
        self.finish()


class GeneListDisplayHandler(general.BaseHandler):
    template = general.env.get_template("list_display.html")

    def get(self, model_bigg_id):
        data = {
            "results": {"genes": "ajax"},
            "page_name": "gene_list",
        }
        self.write(self.template.render(data))
        self.finish()


class GeneHandler(general.BaseHandler):
    template = general.env.get_template("gene.html")

    def get(self, model_bigg_id, gene_bigg_id):
        result = general.safe_query(queries.get_model_gene, gene_bigg_id, model_bigg_id)
        self.return_result(result)
