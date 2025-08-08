from cobradb.util import ref_tuple_to_str, ref_str_to_tuple
from cobradb.models import Genome, Chromosome, Model, GenomeRegion

from sqlalchemy import inspect

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

def get_genomes_with_chromosomes(taxon_ids, gene_id_filter=None, session=None):
    if not taxon_ids:
        return []

    genomes = (
        session.query(Genome)
        .filter(Genome.taxon_id.in_(list(taxon_ids)))
        .all()
    )
    if not genomes:
        return []

    genome_ids = [g.id for g in genomes]

    chromosomes = (
        session.query(Chromosome)
        .filter(Chromosome.genome_id.in_(genome_ids))
        .all()
    )
    if not chromosomes:
        chrom_map = {}
    else:
        chrom_ids = [c.id for c in chromosomes]

        region_query = session.query(GenomeRegion).filter(
            GenomeRegion.chromosome_id.in_(chrom_ids)
        )
        
        if gene_id_filter is not None:
            filt_ids = set(map(int, gene_id_filter))
            if filt_ids:
                region_query = region_query.filter(GenomeRegion.id.in_(filt_ids))
            else:
                region_query = region_query.filter(False)

        regions = region_query.all()

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
            col.key: getattr(g, col.key)
            for col in inspect(Genome).mapper.column_attrs
        }
        genome_dict["chromosome"] = chrom_map.get(g.id, [])
        results.append(genome_dict)

    return results