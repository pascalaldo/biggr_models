from bigg_models.queries import utils
from cobradb.util import ref_tuple_to_str, ref_str_to_tuple
from cobradb.models import Genome, Chromosome, Model
from sqlalchemy import func


def get_genomes_count(session, **kwargs):
    """Return the number of models in the database."""
    query = session.query(Genome)
    return query.count()


def get_genomes(
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    multistrain_off=False,
):
    # get the sort column
    columns = {
        "name": func.lower(Genome.accession_value),
        "organism": func.lower(Model.organism),
        "genome_type": func.lower(Genome.accession_type),
    }

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    query = session.query(Genome)
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [
        {
            "name": x.accession_value,
            "genome_ref_string": ref_tuple_to_str(x.accession_type, x.accession_value),
            "genome_type": x.accession_type,
            "organism": x.organism,
        }
        for x in query
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
        "models": [x.id for x in models_db],
        "chromosomes": [x.ncbi_accession for x in chromosomes_db],
    }
