from cobradb.models import Chromosome, Gene, Model, ModelGene
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


class GeneListViewHandler(utils.DataHandler):
    title = "Genes"
    columns = [
        utils.DataColumnSpec(
            Gene.bigg_id,
            "BiGG ID",
            hyperlink="/models/${row['model__bigg_id']}/genes/${row['gene__bigg_id']}",
            requires=ModelGene.gene,
        ),
        utils.DataColumnSpec(
            Gene.name,
            "Name",
            requires=[
                ModelGene.gene,
            ],
        ),
        utils.DataColumnSpec(
            Model.bigg_id,
            "Model",
            requires=[
                ModelGene.model,
            ],
        ),
        utils.DataColumnSpec(
            Gene.mapped_to_genbank,
            "Mapped",
            requires=[
                ModelGene.gene,
            ],
            search_type="bool",
        ),
        utils.DataColumnSpec(
            Chromosome.ncbi_accession,
            "Chromosome",
            requires=[
                Gene.chromosome,
            ],
        ),
    ]

    def prepare(self):
        self.model_bigg_id = self.path_args[0]
        super().prepare()

    def pre_filter(self, query):
        return query.filter(Model.bigg_id == self.model_bigg_id)

    def breadcrumbs(self):
        return [
            ("Home", "/"),
            ("Models", "/models/"),
            (self.model_bigg_id, f"/models/{self.model_bigg_id}"),
            ("Genes", f"/models/{self.model_bigg_id}/genes/"),
        ]


class GeneHandler(utils.BaseHandler):
    template = utils.env.get_template("gene.html")

    def get(self, model_bigg_id, gene_bigg_id):
        result = utils.safe_query(
            gene_queries.get_model_gene, gene_bigg_id, model_bigg_id
        )
        self.return_result(result)
