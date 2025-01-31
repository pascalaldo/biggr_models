from bigg_models.handlers import utils
from bigg_models.queries import genome_queries


# Genomes
class GenomeListHandler(utils.BaseHandler):
    def get(self):
        results = utils.safe_query(genome_queries.get_genome_list)
        self.write(results)
        self.finish()


class GenomeListDisplayHandler(utils.BaseHandler):
    template = utils.env.get_template("genomes.html")

    def get(self):
        results = utils.safe_query(genome_queries.get_genome_list)
        self.write(self.template.render({"genomes": results}))
        self.finish()


class GenomeHandler(utils.BaseHandler):
    template = utils.env.get_template("genome.html")

    def get(self, genome_ref_string):
        result = utils.safe_query(
            genome_queries.get_genome_and_models, genome_ref_string
        )
        self.return_result(result)
