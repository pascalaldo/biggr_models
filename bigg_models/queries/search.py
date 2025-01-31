from bigg_models.queries import general

from cobradb.models import (
    Component,
    Compartment,
    CompartmentalizedComponent,
    Chromosome,
    DataSource,
    Gene,
    GeneReactionMatrix,
    Genome,
    GenomeRegion,
    Model,
    ModelCount,
    ModelGene,
    ModelReaction,
    ModelCompartmentalizedComponent,
    Reaction,
    Synonym,
)

from cobradb.model_loading import parse
from sqlalchemy import func, or_, and_
from itertools import chain

name_sim_cutoff = 0.3
bigg_id_sim_cutoff = 0.2
gene_bigg_id_sim_cutoff = 1.0
organism_sim_cutoff = 0.1


def search_for_universal_reactions_count(
    query_string,
    session,
    multistrain_off,
):
    """Count the search results."""
    # similarity functions
    sim_bigg_id = func.similarity(Reaction.bigg_id, query_string)
    sim_name = func.similarity(Reaction.name, query_string)

    query = session.query(Reaction.bigg_id, Reaction.name).filter(
        or_(
            sim_bigg_id >= bigg_id_sim_cutoff,
            and_(sim_name >= name_sim_cutoff, Reaction.name != ""),
        )
    )

    if multistrain_off:
        query = general._add_multistrain_filter(session, query, Reaction)

    return query.count()


def search_for_universal_reactions(
    query_string: str,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    multistrain_off=False,
):
    """Search for universal reactions.

    Arguments
    ---------

    query_string: The string to search for.

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name'.

    """
    # similarity functions
    sim_bigg_id = func.similarity(Reaction.bigg_id, query_string)
    sim_name = func.similarity(Reaction.name, query_string)

    # get the sort column
    columns = {
        "bigg_id": func.lower(Reaction.bigg_id),
        "name": func.lower(Reaction.name),
    }

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_name)
        sort_direction = "descending"
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    # set up the query
    query = session.query(Reaction.bigg_id, Reaction.name).filter(
        or_(
            sim_bigg_id >= bigg_id_sim_cutoff,
            and_(sim_name >= name_sim_cutoff, Reaction.name != ""),
        )
    )

    if multistrain_off:
        query = general._add_multistrain_filter(session, query, Reaction)

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def search_for_reactions(
    query_string,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    limit_models=None,
):
    """Search for model reactions.

    Arguments
    ---------

    query_string: The string to search for.

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
    # similarity functions
    sim_bigg_id = func.similarity(Reaction.bigg_id, query_string)
    sim_name = func.similarity(Reaction.name, query_string)

    # get the sort column
    columns = {
        "bigg_id": func.lower(Reaction.bigg_id),
        "name": func.lower(Reaction.name),
    }

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_name)
        sort_direction = "descending"
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    # set up the query
    query = (
        session.query(Reaction.bigg_id, Model.bigg_id, Model.organism, Reaction.name)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(
            or_(
                sim_bigg_id >= bigg_id_sim_cutoff,
                and_(sim_name >= name_sim_cutoff, Reaction.name != ""),
            )
        )
    )

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    # limit the models
    if limit_models:
        query = query.filter(Model.bigg_id.in_(limit_models))

    return [
        {"bigg_id": x[0], "model_bigg_id": x[1], "organism": x[2], "name": x[3]}
        for x in query
    ]


def reaction_with_hash(hash, session):
    """Find the reaction with the given hash."""
    res = (
        session.query(Reaction.bigg_id, Reaction.name)
        .filter(Reaction.reaction_hash == hash)
        .first()
    )
    if res is None:
        raise general.NotFoundError
    return {"bigg_id": res[0], "model_bigg_id": "universal", "name": res[1]}


def search_for_universal_metabolites_count(
    query_string,
    session,
    multistrain_off,
):
    """Count the search results."""
    # similarity functions
    sim_bigg_id = func.similarity(Component.bigg_id, query_string)
    sim_name = func.similarity(Component.name, query_string)

    query = session.query(Component.bigg_id, Component.name).filter(
        or_(
            sim_bigg_id >= bigg_id_sim_cutoff,
            and_(sim_name >= name_sim_cutoff, Component.name != ""),
        )
    )

    if multistrain_off:
        query = general._add_multistrain_filter(session, query, Component)

    return query.count()


def search_for_universal_metabolites(
    query_string,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    multistrain_off=False,
):
    """Search for universal Metabolites.

    Arguments
    ---------

    query_string: The string to search for.

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name'.

    """
    # similarity functions
    sim_bigg_id = func.similarity(Component.bigg_id, query_string)
    sim_name = func.similarity(Component.name, query_string)

    # get the sort column
    columns = {
        "bigg_id": func.lower(Component.bigg_id),
        "name": func.lower(Component.name),
    }

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_name)
        sort_direction = "descending"
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    # set up the query
    query = session.query(Component.bigg_id, Component.name).filter(
        or_(
            sim_bigg_id >= bigg_id_sim_cutoff,
            and_(sim_name >= name_sim_cutoff, Component.name != ""),
        )
    )

    if multistrain_off:
        query = general._add_multistrain_filter(session, query, Component)

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def search_for_metabolites(
    query_string,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    limit_models=None,
    strict=False,
):
    """Search for model metabolites.

    Arguments
    ---------

    query_string: The string to search for.

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name',
    'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    limit_models: search for results in only this array of model BiGG IDs.

    strict: if True, then only look for exact matches to the BiGG ID, with the
    compartment.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'model_bigg_id', and
    'organism'.

    """
    # similarity functions
    sim_bigg_id = func.similarity(Component.bigg_id, query_string)
    sim_name = func.similarity(Component.name, query_string)

    # get the sort column
    columns = {
        "bigg_id": [func.lower(Component.bigg_id), func.lower(Compartment.bigg_id)],
        "name": func.lower(Component.name),
        "model_bigg_id": func.lower(Model.bigg_id),
        "organism": func.lower(Model.organism),
    }

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    if sort_column is None:
        if strict:
            # just sort by bigg ID
            sort_column_object = columns["bigg_id"]
            sort_direction = "ascending"
        else:
            # sort by most similar
            sort_column_object = func.greatest(sim_name, sim_bigg_id)
            sort_direction = "descending"
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    # set up the query
    query = (
        session.query(
            Component.bigg_id,
            Compartment.bigg_id,
            Model.bigg_id,
            Model.organism,
            Component.name,
        )
        .join(
            CompartmentalizedComponent,
            CompartmentalizedComponent.component_id == Component.id,
        )
        .join(Compartment, Compartment.id == CompartmentalizedComponent.compartment_id)
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
    )

    # whether to allow fuzzy search
    if strict:
        try:
            metabolite_bigg_id, compartment_bigg_id = parse.split_compartment(
                query_string
            )
        except Exception:
            return []
        query = query.filter(Component.bigg_id == metabolite_bigg_id).filter(
            Compartment.bigg_id == compartment_bigg_id
        )
    else:
        query = query.filter(
            or_(
                sim_bigg_id >= bigg_id_sim_cutoff,
                and_(sim_name >= name_sim_cutoff, Component.name != ""),
            )
        )

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    # just search certain models
    if limit_models:
        query = query.filter(Model.bigg_id.in_(limit_models))

    return [
        {
            "bigg_id": x[0],
            "compartment_bigg_id": x[1],
            "model_bigg_id": x[2],
            "organism": x[3],
            "name": x[4],
        }
        for x in query
    ]


def search_for_genes_count(
    query_string,
    session,
    limit_models=None,
    multistrain_off=False,
):
    """Count the search results."""
    # similarity functions
    sim_bigg_id = func.similarity(Gene.bigg_id, query_string)
    sim_name = func.similarity(Gene.name, query_string)

    # set up the query
    query = (
        session.query(
            Gene.bigg_id, Model.bigg_id, Gene.name, sim_bigg_id, Model.organism
        )
        .join(ModelGene, ModelGene.gene_id == Gene.id)
        .join(Model, Model.id == ModelGene.model_id)
        .filter(
            or_(
                sim_bigg_id >= gene_bigg_id_sim_cutoff,
                and_(sim_name >= name_sim_cutoff, Gene.name != ""),
            )
        )
    )

    if multistrain_off:
        query = general._add_multistrain_filter(session, query, Gene)

    # limit the models
    if limit_models:
        query = query.filter(Model.bigg_id.in_(limit_models))

    return query.count()


def search_for_genes(
    query_string,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    limit_models=None,
    multistrain_off=False,
):
    """Search for genes.

    Arguments
    ---------

    query_string: The string to search for.

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name',
    'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    limit_models: search for results in only this array of model BiGG IDs.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'model_bigg_id', and
    'organism'.

    """
    # similarity functions
    sim_bigg_id = func.similarity(GenomeRegion.bigg_id, query_string)
    sim_name = func.similarity(Gene.name, query_string)

    # get the sort column
    columns = {
        "bigg_id": func.lower(Gene.bigg_id),
        "name": func.lower(Gene.name),
        "model_bigg_id": func.lower(Model.bigg_id),
        "organism": func.lower(Model.organism),
    }

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_name)
        sort_direction = "descending"
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    # set up the query
    query = (
        session.query(GenomeRegion.bigg_id, Gene.name, Model.bigg_id, Model.organism)
        .join(Gene)
        .join(ModelGene)
        .join(Model)
        .filter(
            or_(
                sim_bigg_id >= gene_bigg_id_sim_cutoff,
                and_(sim_name >= name_sim_cutoff, Gene.name != ""),
            )
        )
    )

    if multistrain_off:
        query = general._add_multistrain_filter(session, query, Gene)

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    # limit the models
    if limit_models:
        query = query.filter(Model.bigg_id.in_(limit_models))

    return [
        {"bigg_id": x[0], "name": x[1], "model_bigg_id": x[2], "organism": x[3]}
        for x in query
    ]


def search_for_models_count(query_string, session, multistrain_off):
    """Count the search results."""
    # similarity functions
    sim_bigg_id = func.similarity(Model.bigg_id, query_string)
    sim_organism = func.similarity(Model.organism, query_string)

    # set up the query
    query = (
        session.query(Model.bigg_id, ModelCount, Model.organism)
        .join(ModelCount)
        .filter(
            or_(sim_bigg_id >= bigg_id_sim_cutoff, sim_organism >= organism_sim_cutoff)
        )
    )
    if multistrain_off:
        query = general._add_multistrain_filter(session, query, Model)
    return query.count()


def search_for_models(
    query_string,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    multistrain_off=False,
):
    """Search for models.

    Arguments
    ---------

    query_string: The string to search for.

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id',
    'organism', 'metabolite_count', 'reaction_count', and 'gene_count'.

    sort_direction: Either 'ascending' or 'descending'.

    limit_models: search for results in only this array of model BiGG IDs.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'organism', 'metabolite_count',
    'reaction_count', and 'gene_count'.

    """

    # models by bigg_id
    sim_bigg_id = func.similarity(Model.bigg_id, query_string)
    sim_organism = func.similarity(Model.organism, query_string)

    # get the sort column
    columns = {
        "bigg_id": func.lower(Model.bigg_id),
        "organism": func.lower(Model.organism),
        "metabolite_count": ModelCount.metabolite_count,
        "reaction_count": ModelCount.reaction_count,
        "gene_count": ModelCount.gene_count,
    }

    if sort_column is None:
        # sort by the greater similarity
        sort_column_object = func.greatest(sim_bigg_id, sim_organism)
        sort_direction = "descending"
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    # set up the query
    query = (
        session.query(
            Model.bigg_id,
            Model.organism,
            ModelCount.metabolite_count,
            ModelCount.reaction_count,
            ModelCount.gene_count,
        )
        .join(ModelCount)
        .filter(
            or_(sim_bigg_id >= bigg_id_sim_cutoff, sim_organism >= organism_sim_cutoff)
        )
    )

    if multistrain_off:
        query = general._add_multistrain_filter(session, query, Model)

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [
        {
            "bigg_id": x[0],
            "organism": x[1],
            "metabolite_count": x[2],
            "reaction_count": x[3],
            "gene_count": x[4],
        }
        for x in query
    ]


def search_ids_fast(query_string, session, limit=None):
    """Search used for autocomplete."""
    gene_q = (
        session.query(Gene.bigg_id)
        .join(ModelGene)
        .filter(Gene.bigg_id.ilike(query_string + "%"))
    )
    gene_name_q = (
        session.query(Gene.name)
        .join(ModelGene)
        .filter(Gene.name.ilike(query_string + "%"))
    )
    reaction_q = session.query(Reaction.bigg_id).filter(
        Reaction.bigg_id.ilike(query_string + "%")
    )
    reaction_name_q = session.query(Reaction.name).filter(
        Reaction.name.ilike(query_string + "%")
    )
    metabolite_q = session.query(Component.bigg_id).filter(
        Component.bigg_id.ilike(query_string + "%")
    )
    metabolite_name_q = session.query(Component.name).filter(
        Component.name.ilike(query_string + "%")
    )
    model_q = session.query(Model.bigg_id).filter(
        Model.bigg_id.ilike(query_string + "%")
    )
    organism_q = session.query(Model.organism).filter(
        Model.organism.ilike(query_string + "%")
    )
    query = gene_q.union(
        gene_name_q,
        reaction_q,
        reaction_name_q,
        metabolite_q,
        metabolite_name_q,
        model_q,
        organism_q,
    )

    if limit is not None:
        query = query.limit(limit)

    return [x[0] for x in query]


# advanced search by external database ID


def get_database_sources(session):
    # for advanced search
    result_db = (
        session.query(DataSource.bigg_id, DataSource.name)
        .filter(DataSource.name != None)
        .distinct()
        .order_by(DataSource.name)
    )
    return [(x[0], x[1]) for x in result_db]


def get_metabolites_for_database_id(session, query, database_source):
    met_db = (
        session.query(Component.bigg_id, Component.name)
        .join(Synonym, Synonym.ome_id == Component.id)
        .filter(Synonym.type == "component")
        .join(DataSource, DataSource.id == Synonym.data_source_id)
        .filter(DataSource.bigg_id == database_source)
        .filter(Synonym.synonym == query.strip())
    )
    comp_comp_db = (
        session.query(Component.bigg_id, Component.name)
        .join(CompartmentalizedComponent)
        .join(Synonym, Synonym.ome_id == CompartmentalizedComponent.id)
        .filter(Synonym.type == "compartmentalized_component")
        .join(DataSource, DataSource.id == Synonym.data_source_id)
        .filter(DataSource.bigg_id == database_source)
        .filter(Synonym.synonym == query.strip())
    )
    return [
        {"bigg_id": x[0], "model_bigg_id": "universal", "name": x[1]}
        for x in chain(met_db, comp_comp_db)
    ]


def get_reactions_for_database_id(session, query, database_source):
    result_db = (
        session.query(Reaction.bigg_id, Reaction.name)
        .join(Synonym, Synonym.ome_id == Reaction.id)
        .filter(Synonym.type == "reaction")
        .join(DataSource, DataSource.id == Synonym.data_source_id)
        .filter(DataSource.bigg_id == database_source)
        .filter(Synonym.synonym == query.strip())
    )
    return [
        {"bigg_id": x[0], "model_bigg_id": "universal", "name": x[1]} for x in result_db
    ]


def get_genes_for_database_id(session, query, database_source):
    result_db = (
        session.query(Gene.bigg_id, Model.bigg_id, Gene.name)
        .join(Synonym, Synonym.ome_id == Gene.id)
        .filter(Synonym.type == "gene")
        .join(DataSource)
        .join(ModelGene)
        .join(Model)
        .filter(DataSource.bigg_id == database_source)
        .filter(Synonym.synonym == query.strip())
    )
    return [{"bigg_id": x[0], "model_bigg_id": x[1], "name": x[2]} for x in result_db]


def sequences_for_reaction(reaction_bigg_id, session):
    print(reaction_bigg_id)
    res = (
        session.query(
            Gene.dna_sequence,
            Gene.protein_sequence,
            Gene.bigg_id,
            Genome.accession_value,
            Model.bigg_id,
        )
        .join(Chromosome, Chromosome.id == Gene.chromosome_id)
        .join(Genome, Genome.id == Chromosome.genome_id)
        .join(ModelGene, ModelGene.gene_id == Gene.id)
        .join(Model, Model.id == ModelGene.model_id)
        .join(GeneReactionMatrix, GeneReactionMatrix.model_gene_id == ModelGene.id)
        .join(ModelReaction, ModelReaction.id == GeneReactionMatrix.model_reaction_id)
        .join(Reaction, Reaction.id == ModelReaction.reaction_id)
        .filter(Reaction.bigg_id == reaction_bigg_id)
        .filter(Gene.dna_sequence != None)
    )
    return [
        {
            "dna_sequence": x[0],
            "protein_sequence": x[1],
            "gene_bigg_id": x[2],
            "genome_accession_value": x[3],
            "model_bigg_id": x[4],
        }
        for x in res.all()
    ]
