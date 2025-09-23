from bigg_models.queries import utils
from cobradb.util import ref_tuple_to_str, ref_str_to_tuple
from cobradb.models import Genome, Chromosome, Model, GenomeRegion
from sqlalchemy import func, select

from sqlalchemy import inspect


def get_genomes_count(session, **kwargs):
    """Return the number of models in the database."""
    query = session.scalars(select(func.count(Genome.id))).first()
    return query


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

    query = select(Genome)
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )
    query = session.scalars(query).all()

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
    genome_db = session.scalars(
        select(Genome)
        .filter(Genome.accession_type == accession_type)
        .filter(Genome.accession_value == accession_value)
        .limit(1)
    ).first()
    models_db = session.scalars(
        select(Model).filter(Model.genome_id == genome_db.id)
    ).all()
    chromosomes_db = session.scalars(
        select(Chromosome).filter(Chromosome.genome_id == genome_db.id)
    ).all()
    return {
        "name": genome_db.accession_value,
        "genome_ref_string": ref_tuple_to_str(
            genome_db.accession_type, genome_db.accession_value
        ),
        "organism": genome_db.organism,
        "models": [x.bigg_id for x in models_db],
        "chromosomes": [x.ncbi_accession for x in chromosomes_db],
    }


def get_genomes_with_chromosomes(taxon_ids, session, gene_id_filter=None):
    if not taxon_ids:
        return []

    genomes = session.scalars(
        select(Genome).filter(Genome.taxon_id.in_(list(taxon_ids)))
    ).all()
    if not genomes:
        return []

    genome_ids = [g.id for g in genomes]

    chromosomes = session.scalars(
        select(Chromosome).filter(Chromosome.genome_id.in_(genome_ids))
    ).all()
    if not chromosomes:
        chrom_map = {}
    else:
        chrom_ids = [c.id for c in chromosomes]

        region_query = select(GenomeRegion).filter(
            GenomeRegion.chromosome_id.in_(chrom_ids)
        )

        if gene_id_filter is not None:
            filt_ids = set(map(int, gene_id_filter))
            if filt_ids:
                region_query = region_query.filter(GenomeRegion.id.in_(filt_ids))
            else:
                region_query = region_query.filter(False)

        regions = session.scalars(region_query).all()

        region_map = {}
        for r in regions:
            region_dict = {
                col.key: getattr(r, col.key)
                for col in inspect(GenomeRegion).mapper.column_attrs
            }
            region_map.setdefault(r.chromosome_id, []).append(region_dict)

        chrom_map = {}
        for c in chromosomes:
            chrom_dict = {
                col.key: getattr(c, col.key)
                for col in inspect(Chromosome).mapper.column_attrs
            }
            chrom_dict["genome_region"] = region_map.get(c.id, [])
            chrom_map.setdefault(c.genome_id, []).append(chrom_dict)

    results = []
    for g in genomes:
        genome_dict = {
            col.key: getattr(g, col.key) for col in inspect(Genome).mapper.column_attrs
        }
        genome_dict["chromosome"] = chrom_map.get(g.id, [])
        results.append(genome_dict)

    return results

