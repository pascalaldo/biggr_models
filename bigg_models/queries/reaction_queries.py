from sqlalchemy.orm import aliased, selectinload, subqueryload
from bigg_models.queries import escher_map_queries, utils, id_queries
from cobradb.models import (
    Annotation,
    AnnotationLink,
    ReferenceReactionAnnotationMapping,
    Compartment,
    CompartmentalizedComponent,
    UniversalCompartmentalizedComponent,
    Component,
    ComponentReferenceMapping,
    UniversalComponent,
    Gene,
    GeneReactionMatrix,
    Model,
    ModelGene,
    ModelReaction,
    Reaction,
    ReactionAnnotationMapping,
    ReactionMatrix,
    ReferenceReaction,
    ReferenceReactionParticipant,
    ReferenceCompound,
    UniversalComponentReferenceMapping,
    UniversalReaction,
    UniversalReactionMatrix,
)
from cobradb.parse import split_id_and_copy_tag
from sqlalchemy import func, asc, select

from bigg_models.queries.memote_queries import get_memote_results_for_reaction
from bigg_models.queries.metabolite_queries import process_annotation_for_template


def get_universal_reactions_count(session):
    """Return the number of universal reactions."""
    return session.scalars(
        select(func.count(UniversalReaction.id)).filter(
            UniversalReaction.model_id == None
        )
    ).first()


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
        "bigg_id": func.lower(UniversalReaction.bigg_id),
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
    query = select(UniversalReaction.bigg_id, UniversalReaction.name).filter(
        UniversalReaction.model_id == None
    )

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    query = session.execute(query)
    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def get_model_reactions_count(model_bigg_id, session):
    """Count the model reactions."""
    return session.scalars(
        select(func.count(Reaction.id))
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.bigg_id == model_bigg_id)
    ).first()


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
        "bigg_id": func.lower(UniversalReaction.bigg_id),
        "name": func.lower(UniversalReaction.name),
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
        select(
            UniversalReaction.bigg_id,
            UniversalReaction.name,
            Model.bigg_id,
            Model.organism,
            ModelReaction.copy_number,
        )
        .join(Reaction, Reaction.universal_reaction_id == UniversalReaction.id)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.bigg_id == model_bigg_id)
    )

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    query = session.execute(query)
    return [
        {
            "bigg_id": f"{x[0]}:{x[4]}" if x[4] != 1 else x[0],
            "name": x[1],
            "model_bigg_id": x[2],
            "organism": x[3],
        }
        for x in query
    ]


def _get_metabolite_and_reference_list_for_universal_reaction(reaction_id, session):
    result_db = session.execute(
        select(
            UniversalCompartmentalizedComponent.bigg_id,
            UniversalComponent.bigg_id,
            UniversalReactionMatrix.coefficient,
            Compartment.bigg_id,
            UniversalComponent.name,
            ReferenceCompound,
            ComponentReferenceMapping,
            ReferenceReactionParticipant,
        )
        .join(UniversalCompartmentalizedComponent.universal_component)
        .join(UniversalCompartmentalizedComponent.compartment)
        .join(
            UniversalReactionMatrix,
            UniversalReactionMatrix.universal_compartmentalized_component_id
            == UniversalCompartmentalizedComponent.id,
        )
        .join(
            UniversalReaction,
            UniversalReaction.id == UniversalReactionMatrix.universal_reaction_id,
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
            ReferenceCompound.id == ComponentReferenceMapping.reference_compound_id,
            isouter=True,
        )  # TODO: Does this work when there is no reference?
        .join(
            ReferenceReaction,
            ReferenceReaction.id == UniversalReaction.reference_id,
            isouter=True,
        )
        .filter(UniversalReaction.bigg_id == reaction_id)
        .order_by(
            asc(UniversalReactionMatrix.coefficient > 0),
            asc(UniversalComponent.bigg_id),
        )
    ).all()
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
    subq = (
        select(cr_id).filter(cr.component_id == Component.id).limit(1).scalar_subquery()
    )
    result_db = session.execute(
        select(
            CompartmentalizedComponent.bigg_id,
            Component.bigg_id,
            UniversalReactionMatrix.coefficient,
            Compartment.bigg_id,
            Component.name,
            ReferenceCompound,
            ComponentReferenceMapping,
            ReferenceReactionParticipant,
            ReactionMatrix.id,
        )
        .join(CompartmentalizedComponent.compartment)
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
            UniversalReactionMatrix.id == ReactionMatrix.universal_reaction_matrix_id,
        )
        .join(
            Reaction,
            Reaction.id == ReactionMatrix.reaction_id,
        )
        .join(UniversalReaction, UniversalReaction.id == Reaction.universal_reaction_id)
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
            ReferenceCompound.id == ComponentReferenceMapping.reference_compound_id,
            isouter=True,
        )  # TODO: Does this work when there is no reference?
        .filter(Reaction.id == reaction_id)
        .order_by(
            asc(UniversalReactionMatrix.coefficient > 0),
            asc(CompartmentalizedComponent.bigg_id),
        )
    ).all()

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
    reaction_db = session.scalars(
        select(UniversalReaction)
        .filter(UniversalReaction.bigg_id == reaction_bigg_id)
        .limit(1)
    ).first()
    if not reaction_db:
        raise utils.NotFoundError("No Reaction found with BiGG ID " + reaction_bigg_id)

    result_db = session.execute(
        select(
            UniversalReaction.bigg_id,
            UniversalReaction.name,
            Model.bigg_id,
            Model.organism,
        )
        .join(Reaction, Reaction.universal_reaction_id == UniversalReaction.id)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(UniversalReaction.bigg_id == reaction_bigg_id)
        .distinct()
    ).all()

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
    all_annotations = []
    if reference_db is not None:
        ref_ann = session.execute(
            select(Annotation, ReferenceReactionAnnotationMapping)
            .options(
                selectinload(Annotation.properties),
                selectinload(Annotation.links).joinedload(AnnotationLink.data_source),
            )
            .join(Annotation.reference_reaction_mappings)
            .filter(
                ReferenceReactionAnnotationMapping.reference_reaction_id
                == reference_db.id
            )
            .join(ReferenceReactionAnnotationMapping.reference_reaction)
        ).all()
        if ref_ann:
            ref_annotations = [
                (process_annotation_for_template(ann), ann_map)
                for ann, ann_map in ref_ann
            ]
            all_annotations.extend(ref_annotations)

    reaction_ann = session.execute(
        select(Annotation, ReactionAnnotationMapping)
        .options(
            selectinload(Annotation.properties),
            selectinload(Annotation.links).joinedload(AnnotationLink.data_source),
        )
        .join(Annotation.reaction_mappings)
        .join(ReactionAnnotationMapping.reaction)
        .filter(Reaction.universal_reaction_id == reaction_db.id)
    ).all()
    if reaction_ann:
        reaction_annotations = [
            (process_annotation_for_template(ann), ann_map)
            for ann, ann_map in reaction_ann
        ]
        all_annotations.extend(reaction_annotations)

    # metabolites
    metabolite_db = _get_metabolite_and_reference_list_for_universal_reaction(
        reaction_bigg_id, session
    )

    reaction_string = utils.build_reaction_string(
        metabolite_db, -1000, 1000, False, format_met="universal_comp_comp"
    )
    return {
        "bigg_id": reaction_db.bigg_id,
        "name": reaction_db.name,
        "pseudoreaction": False,
        "all_annotations": all_annotations,
        "metabolites": metabolite_db,
        "reaction_string": reaction_string,
        "models_containing_reaction": [
            {"bigg_id": x[2], "organism": x[3]} for x in result_db
        ],
        "reference": reference_db,
    }


def get_reactions_for_model(model_bigg_id, session):
    result_db = session.execute(
        select(Reaction.bigg_id, Reaction.name, Model.organism)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(Model, Model.id == ModelReaction.model_id)
        .filter(Model.bigg_id == model_bigg_id)
    ).all()
    return [{"bigg_id": x[0], "name": x[1], "organism": x[2]} for x in result_db]


def _get_gene_list_for_model_reaction(model_reaction_id, session):
    result_db = session.execute(
        select(Gene.bigg_id, Gene.name)
        .join(Gene.model_genes)
        .join(ModelGene.reaction_matrix)
        .filter(GeneReactionMatrix.model_reaction_id == model_reaction_id)
    )
    return [{"bigg_id": x[0], "name": x[1]} for x in result_db]


def get_model_list_for_reaction(reaction_bigg_id, session):
    result = session.scalars(
        select(Model.bigg_id)
        .join(ModelReaction, ModelReaction.model_id == Model.id)
        .join(Reaction, Reaction.id == ModelReaction.reaction_id)
        .join(Reaction.universal_reaction)
        .filter(UniversalReaction.bigg_id == reaction_bigg_id)
        .distinct()
    ).all()
    return [{"bigg_id": x[0]} for x in result]


def get_reference_for_reaction(reaction_bigg_id, session):
    ur_alias = aliased(UniversalReaction)
    result = session.scalars(
        select(ReferenceReaction)
        .options(
            subqueryload(
                ReferenceReaction.universal_reactions.and_(
                    UniversalReaction.bigg_id != reaction_bigg_id,
                    UniversalReaction.model_id == None,
                )
            )
        )
        .execution_options(populate_existing=True)
        .join(ur_alias, ur_alias.reference_id == ReferenceReaction.id)
        .filter(ur_alias.bigg_id == reaction_bigg_id)
        .limit(1)
    ).first()
    return result


def get_model_reaction(model_bigg_id, biggr_id, session):
    """Get details about this reaction in the given model. Returns multiple
    results when the reaction appears in the model multiple times.

    """
    # model_reaction_db = (
    #     session.query(
    #         Reaction.id,
    #         UniversalReaction.id,
    #         UniversalReaction.name,
    #         ModelReaction.id,
    #         ModelReaction.gene_reaction_rule,
    #         ModelReaction.lower_bound,
    #         ModelReaction.upper_bound,
    #         ModelReaction.objective_coefficient,
    #         ModelReaction.copy_number,
    #         ModelReaction.subsystem,
    #     )
    #     .join(UniversalReaction, Reaction.universal_id == UniversalReaction.id)
    #     .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
    #     .filter(ModelReaction.model_id == model_bigg_id)
    #     .filter(ModelReaction.copy_number == copy_number)
    #     .filter(UniversalReaction.id == reaction_bigg_id)
    # )
    #
    reaction_bigg_id, copy_number = split_id_and_copy_tag(biggr_id)
    full_bigg_id = (
        reaction_bigg_id if copy_number == 1 else f"{reaction_bigg_id}:{copy_number}"
    )

    result_db = session.execute(
        select(
            Reaction,
            UniversalReaction,
            ModelReaction,
        )
        .join(UniversalReaction, Reaction.universal_reaction_id == UniversalReaction.id)
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .join(ModelReaction.model)
        .filter(Model.bigg_id == model_bigg_id)
        .filter(ModelReaction.copy_number == copy_number)
        .filter(UniversalReaction.bigg_id == reaction_bigg_id)
        .limit(1)
    ).first()
    if result_db is None:
        raise utils.NotFoundError(
            "Reaction %s not found in model %s" % (reaction_bigg_id, model_bigg_id)
        )

    reaction_db, universal_reaction_db, model_reaction_db = result_db

    # metabolites
    metabolite_db = _get_metabolite_and_reference_list_for_reaction(
        reaction_db.id, session
    )

    # models
    model_db = get_model_list_for_reaction(reaction_bigg_id, session)
    model_result = [x for x in model_db if x != model_bigg_id]

    # reference
    reference_db = get_reference_for_reaction(reaction_bigg_id, session)

    all_annotations = []
    if reference_db is not None:
        ref_ann = session.execute(
            select(Annotation, ReferenceReactionAnnotationMapping)
            .options(
                selectinload(Annotation.properties),
                selectinload(Annotation.links).joinedload(AnnotationLink.data_source),
            )
            .join(Annotation.reference_reaction_mappings)
            .filter(
                ReferenceReactionAnnotationMapping.reference_reaction_id
                == reference_db.id
            )
            .join(ReferenceReactionAnnotationMapping.reference_reaction)
        ).all()
        if ref_ann:
            ref_annotations = [
                (process_annotation_for_template(ann), ann_map)
                for ann, ann_map in ref_ann
            ]
            all_annotations.extend(ref_annotations)

    reaction_ann = session.execute(
        select(Annotation, ReactionAnnotationMapping)
        .options(
            selectinload(Annotation.properties),
            selectinload(Annotation.links).joinedload(AnnotationLink.data_source),
        )
        .join(Annotation.reaction_mappings)
        .filter(ReactionAnnotationMapping.reaction_id == reaction_db.id)
    ).all()
    if reaction_ann:
        reaction_annotations = [
            (process_annotation_for_template(ann), ann_map)
            for ann, ann_map in reaction_ann
        ]
        all_annotations.extend(reaction_annotations)

    other_copy_numbers = list(
        sorted(
            x[0]
            for x in session.scalars(
                select(ModelReaction.copy_number)
                .join(Reaction, Reaction.id == ModelReaction.reaction_id)
                .filter(
                    Reaction.universal_reaction_id == reaction_db.universal_reaction_id
                )
                .filter(ModelReaction.model_id == model_reaction_db.model_id)
                .filter(ModelReaction.copy_number != model_reaction_db.copy_number)
            ).all()
        )
    )

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

    gene_db = _get_gene_list_for_model_reaction(model_reaction_db.id, session)
    reaction_string = utils.build_reaction_string(
        metabolite_db,
        model_reaction_db.lower_bound,
        model_reaction_db.upper_bound,
        False,
        format_met="comp_comp",
    )
    # exported_reaction_id = (
    #     make_reaction_copy_id(reaction_bigg_id, result_db[8])
    #     if db_count > 1
    #     else reaction_bigg_id
    # )
    memote_result_db = get_memote_results_for_reaction(session, model_reaction_db.id)

    return {
        "bigg_id": reaction_bigg_id,
        "full_bigg_id": full_bigg_id,
        "model_bigg_id": model_bigg_id,
        "reaction": reaction_db,
        "all_annotations": all_annotations,
        "model_reaction": model_reaction_db,
        "universal_reaction": universal_reaction_db,
        "other_copy_numbers": other_copy_numbers,
        "reaction_string": reaction_string,
        "memote_result": memote_result_db,
        "genes": gene_db,
        "reference": reference_db,
        "other_models_with_reaction": model_result,
        "metabolites": metabolite_db,
    }


def get_reaction(reaction_bigg_id, session):
    return session.scalars(
        select(Reaction).filter(Reaction.bigg_id == reaction_bigg_id).limit(1)
    ).first()
