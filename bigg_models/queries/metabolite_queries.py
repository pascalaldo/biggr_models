from bigg_models.queries import escher_map_queries, utils, id_queries

from cobradb.models import (
    CompartmentalizedComponent,
    Component,
    ComponentReferenceMapping,
    ReferenceCompound,
    UniversalComponent,
    UniversalCompartmentalizedComponent,
    UniversalComponentReferenceMapping,
    UniversalReaction,
    UniversalReactionMatrix,
    Compartment,
    DeprecatedID,
    ModelCompartmentalizedComponent,
    ModelReaction,
    Model,
    Reaction,
    ReactionMatrix,
)

from sqlalchemy import func


def get_universal_metabolites_count(session):
    return (
        session.query(UniversalComponent)
        .filter(UniversalComponent.model_specific == False)
        .count()
    )


def get_universal_metabolites(
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs,
):
    """Get universal metabolites.

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
        "bigg_id": func.lower(UniversalComponent.id),
        "name": func.lower(UniversalComponent.name),
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
    query = session.query(UniversalComponent.id, UniversalComponent.name).filter(
        UniversalComponent.model_specific == False
    )

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def get_model_metabolites_count(model_bigg_id, session):
    """Count the model metabolites."""
    return (
        session.query(ModelCompartmentalizedComponent)
        .filter(ModelCompartmentalizedComponent.model_id == model_bigg_id)
        .count()
    )


def get_model_metabolites(
    model_bigg_id,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs,
):
    """Get model metabolites.

    Arguments
    ---------

    model_bigg_id: The bigg id of the model to retrieve metabolites.

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id',
    'name', 'model_bigg_id', and 'organism'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'name', 'compartment_bigg_id',
    'model_bigg_id', and 'organism'.

    """
    # get the sort column
    columns = {
        "bigg_id": [
            func.lower(CompartmentalizedComponent.id),
        ],
        "name": func.lower(Component.name),
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
            CompartmentalizedComponent.id,
            Component.name,
            Model.id,
            Model.organism,
            CompartmentalizedComponent.compartment_id,
        )
        .join(
            Component,
            CompartmentalizedComponent.component_id == Component.id,
        )
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
        .filter(Model.id == model_bigg_id)
    )

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [
        {
            "bigg_id": x[0],
            "name": x[1],
            "model_bigg_id": x[2],
            "organism": x[3],
            "compartment_bigg_id": x[4],
        }
        for x in query
    ]


def get_metabolite(met_bigg_id, session):
    result_db = (
        session.query(UniversalComponent.id, UniversalComponent.name)
        .filter(UniversalComponent.id == met_bigg_id)
        .first()
    )
    if result_db is None:
        raise utils.NotFoundError("No Component found with BiGG ID " + met_bigg_id)
        # Look for a result with a deprecated ID
        # res_db = (
        #     session.query(DeprecatedID, UniversalComponent)
        #     .filter(DeprecatedID.type == "component")
        #     .filter(DeprecatedID.deprecated_id == met_bigg_id)
        #     .join(UniversalComponent, UniversalComponent.id == DeprecatedID.ome_id)
        #     .first()
        # )
        # if res_db:
        #     raise utils.RedirectError(res_db[1].bigg_id)
        # else:
        #     raise utils.NotFoundError("No Component found with BiGG ID " + met_bigg_id)

    comp_comp_db = (
        session.query(
            CompartmentalizedComponent.id,
            Model.id,
            Model.organism,
        )
        .join(
            UniversalCompartmentalizedComponent,
            CompartmentalizedComponent.universal_id
            == UniversalCompartmentalizedComponent.id,
        )
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
        .join(
            UniversalComponent,
            UniversalComponent.id
            == UniversalCompartmentalizedComponent.universal_component_id,
        )
        .filter(UniversalComponent.id == met_bigg_id)
    )

    default_component_db = (
        session.query(UniversalComponentReferenceMapping, Component, ReferenceCompound)
        .join(
            ComponentReferenceMapping,
            ComponentReferenceMapping.id
            == UniversalComponentReferenceMapping.mapping_id,
        )
        .join(Component, Component.id == ComponentReferenceMapping.component_id)
        .join(
            ReferenceCompound,
            ReferenceCompound.id == ComponentReferenceMapping.reference_id,
        )
        .filter(UniversalComponentReferenceMapping.id == met_bigg_id)
        .first()
    )
    print(f"Default component: {default_component_db}")
    print(default_component_db[0].id)
    default_component = None
    reference = None

    if default_component_db:
        _, default_component_db, reference_db = default_component_db
        default_component = {
            "id": default_component_db.id,
            "formula": default_component_db.formula,
            "charge": default_component_db.charge,
        }
        reference = {
            "id": reference_db.id,
            "name": reference_db.name,
            "type": reference_db.compound_type,
            "charge": reference_db.charge,
            "formula": reference_db.formula,
        }

    components_db = (
        session.query(Component, ComponentReferenceMapping, ReferenceCompound)
        .join(
            ComponentReferenceMapping,
            ComponentReferenceMapping.component_id == Component.id,
        )
        .join(
            ReferenceCompound,
            ReferenceCompound.id == ComponentReferenceMapping.reference_id,
        )
        .filter(Component.universal_id == met_bigg_id)
        .order_by(Component.charge)
    )
    formulae = list({y.formula for y, _, _ in components_db if y is not None})
    charges = list({y.charge for y, _, _ in components_db if y is not None})

    components = []
    for component, refmap, ref_db in components_db:
        ref = None
        if ref_db is not None:
            ref = {
                "id": ref_db.id,
                "name": ref_db.name,
                "type": ref_db.compound_type,
                "charge": ref_db.charge,
                "formula": ref_db.formula,
                "ref_n": refmap.reference_n,
            }
        skip = False
        for comp in components:
            if comp["id"] == component.id:
                if ref is not None:
                    comp["reference"].append(ref)
                skip = True
                break
        if skip:
            continue
        d = {
            "id": component.id,
            "name": component.name,
            "charge": component.charge,
            "formula": component.formula,
            "reference": [] if ref is None else [ref],
        }
        if default_component is not None and default_component["id"] == d["id"]:
            d["default"] = True
            components.insert(0, d)
        else:
            components.append(d)

    # database links and old ids
    db_link_results = id_queries._get_db_links_for_metabolite(met_bigg_id, session)
    old_id_results = id_queries._get_old_ids_for_metabolite(met_bigg_id, session)

    return {
        "bigg_id": result_db[0],
        "name": result_db[1],
        "formulae": formulae,
        "charges": charges,
        "database_links": db_link_results,
        "old_identifiers": old_id_results,
        # "compartments_in_models": [],
        "components": components,
        "default_component": default_component,
        "reference": reference,
        "compartments_in_models": [
            {"bigg_id": c[0], "model_bigg_id": c[1], "organism": c[2]}
            for c in comp_comp_db
        ],
    }


def get_model_list_for_metabolite(metabolite_bigg_id, session):
    result = (
        session.query(Model.id, CompartmentalizedComponent.compartment_id)
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        .filter(CompartmentalizedComponent.component_id == metabolite_bigg_id)
    )
    return [{"bigg_id": x[0], "compartment_bigg_id": x[1]} for x in result]


def get_model_comp_metabolite(comp_met_id, model_bigg_id, session):
    result_db = (
        session.query(
            Component.id,
            Component.name,
            Compartment.id,
            Compartment.name,
            Model.id,
            Component.formula,
            Component.charge,
            CompartmentalizedComponent.id,
            Model.id,
            Component.model_specific,
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
        .filter(CompartmentalizedComponent.id == comp_met_id)
        .filter(Model.id == model_bigg_id)
        .first()
    )
    if result_db is None:
        raise utils.NotFoundError(
            "Component %s not in model %s" % (comp_met_id, model_bigg_id)
        )
    met_bigg_id = result_db[0]
    reference_db = (
        session.query(ReferenceCompound)
        .join(
            ComponentReferenceMapping,
            ReferenceCompound.id == ComponentReferenceMapping.reference_id,
        )
        .filter(
            ComponentReferenceMapping.component_id == str(result_db[0]),
        )
        .first()
    )
    if reference_db is None:
        reference = None
    else:
        reference = {
            "id": reference_db.id,
            "name": reference_db.name,
            "type": reference_db.compound_type,
            "charge": reference_db.charge,
            "formula": reference_db.formula,
        }

    reactions_db = (
        session.query(
            UniversalReaction.id, UniversalReaction.name, ModelReaction.model_id
        )
        .join(Reaction, Reaction.universal_id == UniversalReaction.id)
        .join(ReactionMatrix, ReactionMatrix.reaction_id == Reaction.id)
        .filter(ReactionMatrix.compartmentalized_component_id == result_db[7])
        .join(
            UniversalReactionMatrix,
            ReactionMatrix.reaction_matrix_id == UniversalReactionMatrix.id,
        )
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .filter(ModelReaction.model_id == result_db[8])
        .distinct()
    )
    model_db = get_model_list_for_metabolite(met_bigg_id, session)
    # m_escher_maps = escher_map_queries.get_escher_maps_for_metabolite(
    #     met_bigg_id, compartment_bigg_id, model_bigg_id, session
    # )
    m_escher_maps = []
    model_result = [x for x in model_db if x["bigg_id"] != model_bigg_id]

    db_link_results = []
    old_id_results = []
    # db_link_results = id_queries._get_db_links_for_model_comp_metabolite(
    #     met_bigg_id, session
    # )
    #
    # old_id_results = id_queries._get_old_ids_for_model_comp_metabolite(
    #     met_bigg_id, compartment_bigg_id, model_bigg_id, session
    # )

    return {
        "bigg_id": result_db[7],
        "name": result_db[1],
        "compartment_bigg_id": result_db[2],
        "compartment_name": result_db[3],
        "model_bigg_id": result_db[4],
        "formula": result_db[5],
        "charge": result_db[6],
        "database_links": db_link_results,
        "old_identifiers": old_id_results,
        "reactions": [
            {"bigg_id": r[0], "name": r[1], "model_bigg_id": r[2]} for r in reactions_db
        ],
        "escher_maps": m_escher_maps,
        "other_models_with_metabolite": model_result,
        "reference": reference,
        "model_specific": result_db[9],
    }
