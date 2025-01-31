from bigg_models.handlers import general
from bigg_models import queries


# Genomes
class GenomeListHandler(general.BaseHandler):
    def get(self):
        results = general.safe_query(queries.get_genome_list)
        self.write(results)
        self.finish()


class GenomeListDisplayHandler(general.BaseHandler):
    template = general.env.get_template("genomes.html")

    def get(self):
        results = general.safe_query(queries.get_genome_list)
        self.write(self.template.render({"genomes": results}))
        self.finish()


class GenomeHandler(general.BaseHandler):
    template = general.env.get_template("genome.html")

    def get(self, genome_ref_string):
        result = general.safe_query(queries.get_genome_and_models, genome_ref_string)
        self.return_result(result)
