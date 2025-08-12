import tornado
from tornado.web import RedirectHandler, RequestHandler, HTTPError
from tornado.escape import json_decode

from bigg_models.handlers import utils
from bigg_models.queries import gene_queries, genome_queries

from sqlalchemy import inspect

class BaseInteropQueryHandler(tornado.web.RequestHandler):

    def _parse_json(self):
        try:
            return tornado.escape.json_decode(self.request.body or b"{}")
        except ValueError:
            raise tornado.web.HTTPError(400, reason="Invalid JSON payload.")

    def write_error(self, status_code: int, **kwargs):
        exc_info = kwargs.get("exc_info")
        if exc_info is not None:
            err = exc_info[1]
            self.write({"error": str(err)})
        else:
            self.write({"error": self._reason})


class QueryByGeneHandler(BaseInteropQueryHandler):
    async def post(self):
        print("interop-query: query-by-gene")

        data = self._parse_json()
        gene_names = data.get("ids")
        if not isinstance(gene_names, list):
            raise tornado.web.HTTPError(400, reason="'ids' must be a list.")

        gene_ids = [
            row[0]
            for gene in gene_names
            for row in utils.safe_query(gene_queries.get_gene_ids_for_gene_name, gene)
        ]

        if not gene_ids:
            self.finish({"results": []})
            return

        genes_info = utils.safe_query(gene_queries.get_genes, gene_ids)
        gene_info_map = {g["id"]: g for g in genes_info}

        regions = utils.safe_query(gene_queries.get_genome_region_for_gene_id, gene_ids)

        results = []
        for region in regions:
            gid   = region["id"]
            ginfo = gene_info_map.get(gid, {})

            results.append({
                "gene_id":      gid,
                "name":         ginfo.get("name"),
                "bigg_id":      ginfo.get("bigg_id"),
                "locus_tag":    ginfo.get("locus_tag"),
                "mapped_to_genbank": ginfo.get("mapped_to_genbank"),
                "genome_region": {k: v for k, v in region.items()},
            })

        self.finish({"results": results})


class QueryByStrainHandler(BaseInteropQueryHandler):
    async def post(self):
        print("interop-query: query-by-strain")

        data = self._parse_json()
        taxon_ids = data.get("ids")
        if not isinstance(taxon_ids, list):
            raise tornado.web.HTTPError(400, reason="'ids' must be a list.")

        taxon_ids = {str(tid) for tid in taxon_ids}
        if not taxon_ids:
            self.finish({"results": []})
            return

        results = utils.safe_query(
            genome_queries.get_genomes_with_chromosomes,
            taxon_ids,
        )

        self.finish({"results": results})

class QueryByPairHandler(BaseInteropQueryHandler):
    async def post(self):
        print("interop-query: query-by-pair")
        data = self._parse_json()
        pairs = data.get("pairs")
        if not isinstance(pairs, list):
            raise tornado.web.HTTPError(400, reason="'pairs' must be a list of objects.")

        for i, pair in enumerate(pairs):
            if not isinstance(pair, dict) or "gene" not in pair or "strain" not in pair:
                raise tornado.web.HTTPError(
                    400,
                    reason=f"Each element in 'pairs' must be an object with 'gene' and 'strain' keys (error at index {i}).",
                )

        pair_results = []
        for pair in pairs:
            gene_name  = pair["gene"]
            strain_id  = str(pair["strain"])

            gene_ids = {
                row[0]
                for row in utils.safe_query(
                    gene_queries.get_gene_ids_for_gene_name,
                    gene_name,
                )
            }

            if not gene_ids:
                pair_results.append({"gene": gene_name, "strain": strain_id, "genomes": []})
                continue

            genomes = utils.safe_query(
                genome_queries.get_genomes_with_chromosomes,
                {strain_id},
                gene_ids 
            )

            pair_results.append(
                {
                    "gene":   gene_name,
                    "strain": strain_id,
                    "genomes": genomes,
                }
            )

        self.finish({"pairs": pair_results})