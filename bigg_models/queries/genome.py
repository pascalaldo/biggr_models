from cobradb.util import ref_tuple_to_str, ref_str_to_tuple
from cobradb.models import Genome, Chromosome, Model


def get_genome_list(session):
    genome_db = session.query(Genome)
    return [
        {
            "name": x.accession_value,
            "genome_ref_string": ref_tuple_to_str(x.accession_type, x.accession_value),
            "organism": x.organism,
        }
        for x in genome_db
    ]


def get_genome_and_models(genome_ref_string, session):
    accession_type, accession_value = ref_str_to_tuple(genome_ref_string)
    genome_db = (
        session.query(Genome)
        .filter(Genome.accession_type == accession_type)
        .filter(Genome.accession_value == accession_value)
        .first()
    )
    models_db = session.query(Model).filter(Model.genome_id == genome_db.id)
    chromosomes_db = session.query(Chromosome).filter(
        Chromosome.genome_id == genome_db.id
    )
    return {
        "name": genome_db.accession_value,
        "genome_ref_string": ref_tuple_to_str(
            genome_db.accession_type, genome_db.accession_value
        ),
        "organism": genome_db.organism,
        "models": [x.bigg_id for x in models_db],
        "chromosomes": [x.ncbi_accession for x in chromosomes_db],
    }
