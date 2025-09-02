from sqlalchemy.orm import aliased
from bigg_models.queries import escher_map_queries, utils, id_queries
from cobradb.models import (
    Compartment,
    CompartmentalizedComponent,
    UniversalCompartmentalizedComponent,
    Component,
    ComponentReferenceMapping,
    UniversalComponent,
    DeprecatedID,
    Gene,
    GeneReactionMatrix,
    Model,
    ModelGene,
    ModelReaction,
    Reaction,
    ReactionMatrix,
    ReferenceReaction,
    ReferenceReactionParticipant,
    ReferenceCompound,
    UniversalComponentReferenceMapping,
    UniversalReaction,
    UniversalReactionMatrix,
)
from cobradb.util import make_reaction_copy_id
from sqlalchemy import func, asc

from bigg_models.queries.memote_queries import get_memote_results_for_reaction


# def reaction_with_hash(hash, session):
#     """Find the reaction with the given hash."""
#     res = (
#         session.query(Reaction.id, Reaction.name)
#         .filter(Reaction.reaction_hash == hash)
#         .first()
#     )
#     if res is None:
#         raise utils.NotFoundError
#     return {"bigg_id": res[0], "model_bigg_id": "universal", "name": res[1]}
#


def get_universal_reactions_count(session):
    """Return the number of universal reactions."""
    return session.query(Reaction).count()


def get_universal_reactions(
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs,
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
        "bigg_id": func.lower(UniversalReaction.id),
        "name": func.lower(UniversalReaction.name),
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
    query = session.query(UniversalReaction.id, UniversalReaction.name)

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def get_model_reactions_count(model_bigg_id, session):
    """Count the model reactions."""
    return (
        session.query(Reaction)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.id == model_bigg_id)
        .count()
    )


def get_model_reactions(
    model_bigg_id,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs,
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
        "bigg_id": func.lower(UniversalReaction.id),
        "name": func.lower(UniversalReaction.name),
        "model_bigg_id": func.lower(Model.id),
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
        session.query(
            UniversalReaction.id, UniversalReaction.name, Model.id, Model.organism
        )
        .join(Reaction, Reaction.universal_id == UniversalReaction.id)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
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


def _get_metabolite_and_reference_list_for_universal_reaction(reaction_id, session):
    result_db = (
        session.query(
            UniversalCompartmentalizedComponent.id,
            UniversalComponent.id,
            UniversalReactionMatrix.coefficient,
            UniversalCompartmentalizedComponent.compartment_id,
            UniversalComponent.name,
            ReferenceCompound,
            ComponentReferenceMapping,
            ReferenceReactionParticipant,
        )
        .join(
            UniversalComponent,
            UniversalCompartmentalizedComponent.universal_component_id
            == UniversalComponent.id,
        )
        .join(
            UniversalReactionMatrix,
            UniversalReactionMatrix.universal_compartmentalized_component_id
            == UniversalCompartmentalizedComponent.id,
        )
        .join(
            UniversalReaction,
            UniversalReaction.id == UniversalReactionMatrix.universal_id,
        )
        .join(
            ReferenceReactionParticipant,
            UniversalReactionMatrix.reference_reaction_participant_id
            == ReferenceReactionParticipant.id,
            isouter=True,
        )
        .join(
            UniversalComponentReferenceMapping,
            UniversalComponentReferenceMapping.id == UniversalComponent.id,
            isouter=True,
        )
        .join(
            ComponentReferenceMapping,
            ComponentReferenceMapping.id
            == UniversalComponentReferenceMapping.mapping_id,
            isouter=True,
        )
        .join(
            ReferenceCompound,
            ReferenceCompound.id == ComponentReferenceMapping.reference_id,
            isouter=True,
        )  # TODO: Does this work when there is no reference?
        .join(
            ReferenceReaction,
            ReferenceReaction.id == UniversalReaction.reference_id,
            isouter=True,
        )
        .filter(UniversalReaction.id == reaction_id)
        .order_by(
            asc(UniversalReactionMatrix.coefficient > 0), asc(UniversalComponent.id)
        )
        .all()
    )
    return [
        {
            "base_bigg_id": x[1],
            "bigg_id": x[0],
            "coefficient": x[2],
            "coefficient_int_or_float": int(x[2]) if x[2].is_integer() else x[2],
            "compartment_bigg_id": x[3],
            "name": x[4],
            "reference_mapping": x[6],
            "reference": x[5],
            "reference_participant": x[7],
        }
        for x in result_db
    ]


def _get_metabolite_and_reference_list_for_reaction(reaction_id, session):
    cr = aliased(ComponentReferenceMapping)
    cr_id = cr.id.label("cr_id")
    subq = session.query(cr_id).filter(cr.component_id == Component.id).limit(1)
    result_db = (
        session.query(
            CompartmentalizedComponent.id,
            Component.id,
            UniversalReactionMatrix.coefficient,
            CompartmentalizedComponent.compartment_id,
            Component.name,
            ReferenceCompound,
            ComponentReferenceMapping,
            ReferenceReactionParticipant,
            ReactionMatrix.id,
        )
        .join(
            Component,
            CompartmentalizedComponent.component_id == Component.id,
        )
        .join(
            ReactionMatrix,
            ReactionMatrix.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        .join(
            UniversalReactionMatrix,
            UniversalReactionMatrix.id == ReactionMatrix.reaction_matrix_id,
        )
        .join(
            Reaction,
            Reaction.id == ReactionMatrix.reaction_id,
        )
        .join(UniversalReaction, UniversalReaction.id == Reaction.universal_id)
        .join(
            ReferenceReaction,
            ReferenceReaction.id == UniversalReaction.reference_id,
            isouter=True,
        )
        .join(
            ReferenceReactionParticipant,
            UniversalReactionMatrix.reference_reaction_participant_id
            == ReferenceReactionParticipant.id,
            isouter=True,
        )
        # .join(
        #     ComponentReferenceMapping,
        #     ComponentReferenceMapping.component_id == Component.id,
        #     isouter=True,
        # )
        .join(
            ComponentReferenceMapping,
            ComponentReferenceMapping.id == subq,
            isouter=True,
        )
        .join(
            ReferenceCompound,
            ReferenceCompound.id == ComponentReferenceMapping.reference_id,
            isouter=True,
        )  # TODO: Does this work when there is no reference?
        .filter(Reaction.id == reaction_id)
        .order_by(
            asc(UniversalReactionMatrix.coefficient > 0),
            asc(CompartmentalizedComponent.id),
        )
        .all()
    )

    return [
        {
            "base_bigg_id": x[1],
            "bigg_id": x[0],
            "coefficient": x[2],
            "coefficient_int_or_float": int(x[2]) if x[2].is_integer() else x[2],
            "compartment_bigg_id": x[3],
            "name": x[4],
            "reference_mapping": x[6],
            "reference": x[5],
            "reference_participant": x[7],
        }
        for x in result_db
    ]


def get_reaction_and_models(reaction_bigg_id, session):
    reaction_db = (
        session.query(UniversalReaction)
        .filter(UniversalReaction.id == reaction_bigg_id)
        .first()
    )
    if not reaction_db:
        raise utils.NotFoundError("No Reaction found with BiGG ID " + reaction_bigg_id)

    result_db = (
        session.query(
            UniversalReaction.id,
            UniversalReaction.name,
            Model.id,
            Model.organism,
        )
        .join(Reaction, Reaction.universal_id == UniversalReaction.id)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(UniversalReaction.id == reaction_bigg_id)
        .distinct()
        .all()
    )

    reference_db = get_reference_for_reaction(reaction_bigg_id, session)

    # if len(result_db) == 0:
    #     # Look for a result with a deprecated ID
    #     # res_db = (
    #     #     session.query(DeprecatedID, Reaction)
    #     #     .filter(DeprecatedID.type == "reaction")
    #     #     .filter(DeprecatedID.deprecated_id == reaction_bigg_id)
    #     #     .join(Reaction, Reaction.id == DeprecatedID.ome_id)
    #     #     .first()
    #     # )
    #     res_db = None
    #     if res_db:
    #         raise utils.RedirectError(res_db[1].id)
    #     else:
    #         raise utils.NotFoundError(
    #             "No Reaction found with BiGG ID " + reaction_bigg_id
    #         )

    # db_link_results = id_queries._get_db_links_for_reaction(reaction_bigg_id, session)
    # old_id_results = id_queries._get_old_ids_for_reaction(reaction_bigg_id, session)
    #
    db_link_results = {}
    old_id_results = []
    # metabolites
    metabolite_db = _get_metabolite_and_reference_list_for_universal_reaction(
        reaction_bigg_id, session
    )

    reaction_string = utils.build_reaction_string(
        metabolite_db, -1000, 1000, False, format_met="universal_comp_comp"
    )
    return {
        "bigg_id": reaction_db.id,
        "name": reaction_db.name,
        "pseudoreaction": False,
        "database_links": db_link_results,
        "old_identifiers": old_id_results,
        "metabolites": metabolite_db,
        "reaction_string": reaction_string,
        "models_containing_reaction": [
            {"bigg_id": x[2], "organism": x[3]} for x in result_db
        ],
        "reference": reference_db,
    }


def get_reactions_for_model(model_bigg_id, session):
    result_db = (
        session.query(Reaction.id, Reaction.name, Model.organism)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.id == model_bigg_id)
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
        session.query(Model.id)
        .join(ModelReaction, ModelReaction.model_id == Model.id)
        .join(Reaction, Reaction.id == ModelReaction.reaction_id)
        .filter(Reaction.id == reaction_bigg_id)
        .distinct()
        .all()
    )
    return [{"bigg_id": x[0]} for x in result]


def get_reference_for_reaction(reaction_bigg_id, session):
    result = (
        session.query(ReferenceReaction)
        .join(UniversalReaction, UniversalReaction.reference_id == ReferenceReaction.id)
        .filter(UniversalReaction.id == reaction_bigg_id)
        .first()
    )
    return result


def get_model_reaction(model_bigg_id, reaction_bigg_id, session):
    """Get details about this reaction in the given model. Returns multiple
    results when the reaction appears in the model multiple times.

    """
    model_reaction_db = (
        session.query(
            Reaction.id,
            UniversalReaction.id,
            UniversalReaction.name,
            ModelReaction.id,
            ModelReaction.gene_reaction_rule,
            ModelReaction.lower_bound,
            ModelReaction.upper_bound,
            ModelReaction.objective_coefficient,
            ModelReaction.copy_number,
            ModelReaction.subsystem,
        )
        .join(UniversalReaction, Reaction.universal_id == UniversalReaction.id)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .filter(ModelReaction.model_id == model_bigg_id)
        .filter(UniversalReaction.id == reaction_bigg_id)
    )
    db_count = model_reaction_db.count()
    if db_count == 0:
        raise utils.NotFoundError(
            "Reaction %s not found in model %s" % (reaction_bigg_id, model_bigg_id)
        )

    reaction_id = model_reaction_db[0][0]

    # metabolites
    metabolite_db = _get_metabolite_and_reference_list_for_reaction(
        reaction_id, session
    )

    # models
    model_db = get_model_list_for_reaction(reaction_bigg_id, session)
    model_result = [x for x in model_db if x != model_bigg_id]

    # reference
    reference_db = get_reference_for_reaction(reaction_bigg_id, session)

    # database_links
    # db_link_results = id_queries._get_db_links_for_model_reaction(
    #     reaction_bigg_id, session
    # )
    #
    # # old identifiers
    # old_id_results = id_queries._get_old_ids_for_model_reaction(
    #     model_bigg_id, reaction_bigg_id, session
    # )
    #
    # # escher maps
    # r_escher_maps = escher_map_queries.get_escher_maps_for_reaction(
    #     reaction_bigg_id, model_bigg_id, session
    # )
    #
    db_link_results = {}
    old_id_results = []
    r_escher_maps = []

    result_list = []
    for result_db in model_reaction_db:
        gene_db = _get_gene_list_for_model_reaction(result_db[3], session)
        reaction_string = utils.build_reaction_string(
            metabolite_db, result_db[5], result_db[6], False, format_met="comp_comp"
        )
        exported_reaction_id = (
            make_reaction_copy_id(reaction_bigg_id, result_db[8])
            if db_count > 1
            else reaction_bigg_id
        )
        memote_result_db = get_memote_results_for_reaction(session, result_db[3])
        result_list.append(
            {
                "gene_reaction_rule": result_db[4],
                "lower_bound": result_db[5],
                "upper_bound": result_db[6],
                "objective_coefficient": result_db[7],
                "genes": gene_db,
                "copy_number": result_db[8],
                "subsystem": result_db[9],
                "exported_reaction_id": exported_reaction_id,
                "reaction_string": reaction_string,
                "memote_result": memote_result_db,
            }
        )

    return {
        "count": len(result_list),
        "bigg_id": reaction_bigg_id,
        "universal_bigg_id": model_reaction_db[0][1],
        "name": model_reaction_db[0][1],
        "pseudoreaction": False,
        "model_bigg_id": model_bigg_id,
        "metabolites": metabolite_db,
        "database_links": db_link_results,
        "old_identifiers": old_id_results,
        "other_models_with_reaction": model_result,
        "escher_maps": r_escher_maps,
        "results": result_list,
        "reference": reference_db,
    }


def get_reaction(reaction_bigg_id, session):
    return session.query(Reaction).filter(Reaction.id == reaction_bigg_id).first()
