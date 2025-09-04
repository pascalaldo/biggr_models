from bigg_models.queries import utils, id_queries
from cobradb.util import ref_tuple_to_str
from cobradb.models import (
    Chromosome,
    Gene,
    GeneReactionMatrix,
    Genome,
    Model,
    ModelGene,
    ModelReaction,
    Reaction,
    UniversalReaction,
    GenomeRegion
)

from sqlalchemy import func


def get_gene_ids_for_gene_name(name, session):
    """Get the gene ids for a gene name."""
    return (
        session.query(Gene.id)
        .filter(func.lower(Gene.name) == func.lower(name))
        .all()
    )

def get_genes(gene_ids, session):
    """Get the genes for a list of gene ids."""
    rows = (
        session.query(Gene.id, Gene.bigg_id, Gene.name, Gene.locus_tag, Gene.mapped_to_genbank)
        .filter(Gene.id.in_(list(gene_ids)))
        .all()
    )

    return [dict(r._mapping) for r in rows]

def get_genome_region_for_gene_id(ids, session):
    """Get the genome region for a gene id."""
    rows = (
        session.query(
            GenomeRegion.id,
            GenomeRegion.chromosome_id,
            GenomeRegion.bigg_id,
            GenomeRegion.leftpos,
            GenomeRegion.rightpos,
            GenomeRegion.strand,
            GenomeRegion.type,
            GenomeRegion.dna_sequence,
            GenomeRegion.protein_sequence,
        )
        .filter(GenomeRegion.id.in_(list(ids)))
        .all()
    )

    return [dict(r._mapping) for r in rows]

    
def get_model_genes_count(model_bigg_id, session):
    """Get the number of gene for the given model."""
    return (
        session.query(Gene)
        .join(ModelGene)
        .join(Model)
        .filter(Model.id == model_bigg_id)
        .count()
    )


def get_model_genes(
    model_bigg_id,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs
):
    """Get model genes.

    Arguments
    ---------

    model_bigg_id: The bigg id of the model to retrieve genes.

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name',
    'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'model_bigg_id', and
    'organism'.

    """
    # get the sort column
    columns = {
        "bigg_id": func.lower(Gene.bigg_id),
        "name": func.lower(Gene.name),
        "model_bigg_id": func.lower(Model.id),
        "organism": func.lower(Model.organism),
    }

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            raise ValueError("Bad sort_column name: %s" % sort_column)

    # set up the query
    query = (
        session.query(Gene.bigg_id, Gene.name, Model.id, Model.organism)
        .join(ModelGene, ModelGene.gene_id == Gene.id)
        .join(Model, Model.id == ModelGene.model_id)
        .filter(Model.id == model_bigg_id)
    )

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [
        {"bigg_id": x[0], "name": x[1], "model_bigg_id": x[2], "organism": x[3]}
        for x in query
    ]


def get_model_gene(gene_bigg_id, model_bigg_id, session):
    result_db = (
        session.query(
            Gene.bigg_id,
            Gene.name,
            Gene.leftpos,
            Gene.rightpos,
            Model.id,
            Gene.strand,
            Chromosome.ncbi_accession,
            Genome.accession_type,
            Genome.accession_value,
            Gene.mapped_to_genbank,
            Gene.dna_sequence,
            Gene.protein_sequence,
        )
        .join(ModelGene, ModelGene.gene_id == Gene.id)
        .join(Model, Model.id == ModelGene.model_id)
        .outerjoin(Genome, Genome.id == Model.genome_id)
        .outerjoin(Chromosome, Chromosome.id == Gene.chromosome_id)
        .filter(Gene.bigg_id == gene_bigg_id)
        .filter(Model.id == model_bigg_id)
        .first()
    )
    if result_db is None:
        raise utils.NotFoundError(
            "Gene %s not found in model %s" % (gene_bigg_id, model_bigg_id)
        )

    reaction_db = (
        session.query(
            Reaction.id,
            ModelReaction.gene_reaction_rule,
            UniversalReaction.name,
            UniversalReaction.id,
        )
        .join(UniversalReaction, UniversalReaction.id == Reaction.universal_id)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .join(
            GeneReactionMatrix, GeneReactionMatrix.model_reaction_id == ModelReaction.id
        )
        .join(ModelGene, ModelGene.id == GeneReactionMatrix.model_gene_id)
        .join(Gene, Gene.id == ModelGene.gene_id)
        .filter(Model.id == model_bigg_id)
        .filter(Gene.bigg_id == gene_bigg_id)
    )
    reaction_results = [
        {"bigg_id": r[3], "reaction_id": r[0], "gene_reaction_rule": r[1], "name": r[2]}
        for r in reaction_db
    ]

    # synonym_db = id_queries._get_db_links_for_model_gene(gene_bigg_id, session)
    synonym_db = {}

    # old_id_results = id_queries._get_old_ids_for_model_gene(
    #     gene_bigg_id, model_bigg_id, session
    # )
    old_id_results = []

    return {
        "bigg_id": result_db[0],
        "name": result_db[1],
        "leftpos": result_db[2],
        "rightpos": result_db[3],
        "model_bigg_id": result_db[4],
        "strand": result_db[5],
        "chromosome_ncbi_accession": result_db[6],
        "genome_ref_string": ref_tuple_to_str(result_db[7], result_db[8]),
        "genome_name": result_db[8],
        "mapped_to_genbank": result_db[9],
        "dna_sequence": result_db[10],
        "protein_sequence": result_db[11],
        "reactions": reaction_results,
        "database_links": synonym_db,
        "old_identifiers": old_id_results,
    }
