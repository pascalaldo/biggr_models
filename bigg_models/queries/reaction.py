from bigg_models.queries import escher_maps, general, old_ids
from cobradb.models import (
    Compartment,
    CompartmentalizedComponent,
    Component,
    DeprecatedID,
    Gene,
    GeneReactionMatrix,
    Model,
    ModelGene,
    ModelReaction,
    Reaction,
    ReactionMatrix,
)
from cobradb.util import make_reaction_copy_id
from sqlalchemy import desc, asc, func, or_, and_, not_

# -------------------------------------------------------------------------------
# Reactions
# -------------------------------------------------------------------------------


def get_universal_reactions_count(session):
    """Return the number of universal reactions."""
    return session.query(Reaction).count()


def get_universal_reactions(
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs
):
    """Get universal reactions.

    Arguments
    ---------

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id', 'name'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name'.

    """
    # get the sort column
    columns = {
        "bigg_id": func.lower(Reaction.bigg_id),
        "name": func.lower(Reaction.name),
    }

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    # set up the query
    query = session.query(Reaction.bigg_id, Reaction.name)

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def get_model_reactions_count(model_bigg_id, session):
    """Count the model reactions."""
    return (
        session.query(Reaction)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.bigg_id == model_bigg_id)
        .count()
    )


def get_model_reactions(
    model_bigg_id,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs
):
    """Get model reactions.

    Arguments
    ---------

    model_bigg_id: The bigg id of the model to retrieve reactions.

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
        "bigg_id": func.lower(Reaction.bigg_id),
        "name": func.lower(Reaction.name),
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
    # set up the query
    query = (
        session.query(Reaction.bigg_id, Reaction.name, Model.bigg_id, Model.organism)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.bigg_id == model_bigg_id)
    )

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [
        {"bigg_id": x[0], "name": x[1], "model_bigg_id": x[2], "organism": x[3]}
        for x in query
    ]


def _get_metabolite_list_for_reaction(reaction_id, session):
    result_db = (
        session.query(
            Component.bigg_id,
            ReactionMatrix.stoichiometry,
            Compartment.bigg_id,
            Component.name,
        )
        # Metabolite -> ReactionMatrix
        .join(
            CompartmentalizedComponent,
            CompartmentalizedComponent.component_id == Component.id,
        )
        .join(
            ReactionMatrix,
            ReactionMatrix.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        # -> Reaction> Model
        .join(Reaction, Reaction.id == ReactionMatrix.reaction_id)
        # -> Compartment
        .join(Compartment, Compartment.id == CompartmentalizedComponent.compartment_id)
        # filter
        .filter(Reaction.bigg_id == reaction_id)
        .all()
    )
    return [
        {
            "bigg_id": x[0],
            "stoichiometry": x[1],
            "compartment_bigg_id": x[2],
            "name": x[3],
        }
        for x in result_db
    ]


def get_reaction_and_models(reaction_bigg_id, session):
    result_db = (
        session.query(
            Reaction.bigg_id,
            Reaction.name,
            Reaction.pseudoreaction,
            Model.bigg_id,
            Model.organism,
        )
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Reaction.bigg_id == reaction_bigg_id)
        .distinct()
        .all()
    )
    if len(result_db) == 0:
        # Look for a result with a deprecated ID
        res_db = (
            session.query(DeprecatedID, Reaction)
            .filter(DeprecatedID.type == "reaction")
            .filter(DeprecatedID.deprecated_id == reaction_bigg_id)
            .join(Reaction, Reaction.id == DeprecatedID.ome_id)
            .first()
        )
        if res_db:
            raise general.RedirectError(res_db[1].bigg_id)
        else:
            raise general.NotFoundError(
                "No Reaction found with BiGG ID " + reaction_bigg_id
            )

    db_link_results = general._get_db_links_for_reaction(reaction_bigg_id, session)
    old_id_results = general._get_old_ids_for_reaction(reaction_bigg_id, session)

    # metabolites
    metabolite_db = _get_metabolite_list_for_reaction(reaction_bigg_id, session)

    reaction_string = general.build_reaction_string(metabolite_db, -1000, 1000, False)
    return {
        "bigg_id": result_db[0][0],
        "name": result_db[0][1],
        "pseudoreaction": result_db[0][2],
        "database_links": db_link_results,
        "old_identifiers": old_id_results,
        "metabolites": metabolite_db,
        "reaction_string": reaction_string,
        "models_containing_reaction": [
            {"bigg_id": x[3], "organism": x[4]} for x in result_db
        ],
    }


def get_reactions_for_model(model_bigg_id, session):
    result_db = (
        session.query(Reaction.bigg_id, Reaction.name, Model.organism)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.bigg_id == model_bigg_id)
        .all()
    )
    return [{"bigg_id": x[0], "name": x[1], "organism": x[2]} for x in result_db]


def _get_gene_list_for_model_reaction(model_reaction_id, session):
    result_db = (
        session.query(Gene.bigg_id, Gene.name)
        .join(ModelGene)
        .join(GeneReactionMatrix)
        .filter(GeneReactionMatrix.model_reaction_id == model_reaction_id)
    )
    return [{"bigg_id": x[0], "name": x[1]} for x in result_db]


def get_model_list_for_reaction(reaction_bigg_id, session):
    result = (
        session.query(Model.bigg_id)
        .join(ModelReaction, ModelReaction.model_id == Model.id)
        .join(Reaction, Reaction.id == ModelReaction.reaction_id)
        .filter(Reaction.bigg_id == reaction_bigg_id)
        .distinct()
        .all()
    )
    return [{"bigg_id": x[0]} for x in result]


def get_model_reaction(model_bigg_id, reaction_bigg_id, session):
    """Get details about this reaction in the given model. Returns multiple
    results when the reaction appears in the model multiple times.

    """
    model_reaction_db = (
        session.query(
            Reaction.bigg_id,
            Reaction.name,
            ModelReaction.id,
            ModelReaction.gene_reaction_rule,
            ModelReaction.lower_bound,
            ModelReaction.upper_bound,
            ModelReaction.objective_coefficient,
            Reaction.pseudoreaction,
            ModelReaction.copy_number,
            ModelReaction.subsystem,
        )
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.bigg_id == model_bigg_id)
        .filter(Reaction.bigg_id == reaction_bigg_id)
    )
    db_count = model_reaction_db.count()
    if db_count == 0:
        raise general.NotFoundError(
            "Reaction %s not found in model %s" % (reaction_bigg_id, model_bigg_id)
        )

    # metabolites
    metabolite_db = _get_metabolite_list_for_reaction(reaction_bigg_id, session)

    # models
    model_db = get_model_list_for_reaction(reaction_bigg_id, session)
    model_result = [x for x in model_db if x != model_bigg_id]

    # database_links
    db_link_results = general._get_db_links_for_model_reaction(
        reaction_bigg_id, session
    )

    # old identifiers
    old_id_results = old_ids._get_old_ids_for_model_reaction(
        model_bigg_id, reaction_bigg_id, session
    )

    # escher maps
    r_escher_maps = escher_maps.get_escher_maps_for_reaction(
        reaction_bigg_id, model_bigg_id, session
    )

    result_list = []
    for result_db in model_reaction_db:
        gene_db = _get_gene_list_for_model_reaction(result_db[2], session)
        reaction_string = general.build_reaction_string(
            metabolite_db, result_db[4], result_db[5], False
        )
        exported_reaction_id = (
            make_reaction_copy_id(reaction_bigg_id, result_db[8])
            if db_count > 1
            else reaction_bigg_id
        )
        result_list.append(
            {
                "gene_reaction_rule": result_db[3],
                "lower_bound": result_db[4],
                "upper_bound": result_db[5],
                "objective_coefficient": result_db[6],
                "genes": gene_db,
                "copy_number": result_db[8],
                "subsystem": result_db[9],
                "exported_reaction_id": exported_reaction_id,
                "reaction_string": reaction_string,
            }
        )

    return {
        "count": len(result_list),
        "bigg_id": reaction_bigg_id,
        "name": model_reaction_db[0][1],
        "pseudoreaction": model_reaction_db[0][7],
        "model_bigg_id": model_bigg_id,
        "metabolites": metabolite_db,
        "database_links": db_link_results,
        "old_identifiers": old_id_results,
        "other_models_with_reaction": model_result,
        "escher_maps": r_escher_maps,
        "results": result_list,
    }


def get_reaction(reaction_bigg_id, session):
    return session.query(Reaction).filter(Reaction.bigg_id == reaction_bigg_id).first()
