from typing import Optional
from cobradb.models import Chromosome, Gene, Model, ModelGene
from bigg_models.handlers import utils
from bigg_models.queries import gene_queries


class GeneListViewHandler(utils.DataHandler):
    title = "Genes"
    model_bigg_id: Optional[str] = None
    page_data = {"row_icon": "gene_S"}
    column_specs = [
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
        result["breadcrumbs"] = [
            ("Home", "/"),
            ("Models", "/models/"),
            (result["model_bigg_id"], f"/models/{result['model_bigg_id']}"),
            ("Genes", f"/models/{result['model_bigg_id']}/genes/"),
            (gene_bigg_id, f"/models/{result['model_bigg_id']}/genes/{gene_bigg_id}"),
        ]
        self.return_result(result)
