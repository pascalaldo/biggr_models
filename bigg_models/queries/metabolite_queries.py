from bigg_models.queries import escher_map_queries, utils, id_queries

from cobradb.models import (
    CompartmentalizedComponent,
    Component,
    ComponentReferenceMapping,
    ReferenceCompound,
    UniversalComponent,
    UniversalCompartmentalizedComponent,
    UniversalComponentReferenceMapping,
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
    return session.query(UniversalComponent).count()


def get_universal_metabolites(
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs
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
    query = session.query(UniversalComponent.id, UniversalComponent.name)

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def get_model_metabolites_count(model_bigg_id, session):
    """Count the model metabolites."""
    return (
        session.query(UniversalComponent)
        .join(
            UniversalCompartmentalizedComponent,
            UniversalCompartmentalizedComponent.universal_component_id
            == UniversalComponent.id,
        )
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.compartmentalized_component_id
            == UniversalCompartmentalizedComponent.id,
        )
        .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
        .filter(Model.id == model_bigg_id)
        .count()
    )


def get_model_metabolites(
    model_bigg_id,
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    **kwargs
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
        "bigg_id": [func.lower(Component.id), func.lower(Compartment.id)],
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
            Component.id,
            Component.name,
            Model.id,
            Model.organism,
            Compartment.id,
        )
        .join(
            CompartmentalizedComponent,
            CompartmentalizedComponent.component_id == Component.id,
        )
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
        .join(Compartment, Compartment.id == CompartmentalizedComponent.compartment_id)
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
        # Look for a result with a deprecated ID
        res_db = (
            session.query(DeprecatedID, UniversalComponent)
            .filter(DeprecatedID.type == "component")
            .filter(DeprecatedID.deprecated_id == met_bigg_id)
            .join(UniversalComponent, UniversalComponent.id == DeprecatedID.ome_id)
            .first()
        )
        if res_db:
            raise utils.RedirectError(res_db[1].bigg_id)
        else:
            raise utils.NotFoundError("No Component found with BiGG ID " + met_bigg_id)

    # comp_comp_db = (
    #     session.query(
    #         Compartment.id,
    #         Model.id,
    #         Model.organism,
    #         ModelCompartmentalizedComponent.formula,
    #         ModelCompartmentalizedComponent.charge,
    #     )
    #     .join(
    #         CompartmentalizedComponent,
    #         CompartmentalizedComponent.universal_id
    #         == UniversalCompartmentalizedComponent.id,
    #     )
    #     .join(
    #         ModelCompartmentalizedComponent,
    #         ModelCompartmentalizedComponent.compartmentalized_component_id
    #         == CompartmentalizedComponent.id,
    #     )
    #     .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
    #     .join(
    #         UniversalComponent,
    #         UniversalComponent.id
    #         == UniversalCompartmentalizedComponent.universal_component_id,
    #     )
    #     .filter(UniversalComponent.id == met_bigg_id)
    # )

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
        session.query(Component, ComponentReferenceMapping)
        .join(
            ComponentReferenceMapping,
            ComponentReferenceMapping.component_id == Component.id,
        )
        .filter(Component.universal_id == met_bigg_id)
        .order_by(Component.charge)
    )
    formulae = list({y.formula for y, _ in components_db if y is not None})
    charges = list({y.charge for y, _ in components_db if y is not None})

    components = []
    for component, refmap in components_db:
        skip = False
        for comp in components:
            if comp["id"] == component.id:
                comp["reference_id"].append(refmap.reference_id)
                skip = True
                break
        if skip:
            continue
        d = {
            "id": component.id,
            "name": component.name,
            "charge": component.charge,
            "reference_id": [refmap.reference_id],
        }
        if default_component is not None and default_component["id"] == d["id"]:
            d["default"] = True
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
        "compartments_in_models": [],
        "components": components,
        "default_component": default_component,
        "reference": reference,
        # "compartments_in_models": [
        #     {"bigg_id": c[0], "model_bigg_id": c[1], "organism": c[2]}
        #     for c in comp_comp_db
        # ],
    }


def get_model_list_for_metabolite(metabolite_bigg_id, session):
    result = (
        session.query(Model.id, Compartment.id)
        .join(ModelCompartmentalizedComponent)
        .join(CompartmentalizedComponent)
        .join(Compartment)
        .join(UniversalComponent)
        .filter(UniversalComponent.id == metabolite_bigg_id)
    )
    return [{"bigg_id": x[0], "compartment_bigg_id": x[1]} for x in result]


def get_model_comp_metabolite(met_bigg_id, compartment_bigg_id, model_bigg_id, session):
    result_db = (
        session.query(
            Component.id,
            Component.name,
            Compartment.id,
            Compartment.name,
            Model.id,
            ModelCompartmentalizedComponent.formula,
            ModelCompartmentalizedComponent.charge,
            CompartmentalizedComponent.id,
            Model.id,
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
        .filter(Component.id == met_bigg_id)
        .filter(Compartment.id == compartment_bigg_id)
        .filter(Model.id == model_bigg_id)
        .first()
    )
    if result_db is None:
        raise utils.NotFoundError(
            "Component %s in compartment %s not in model %s"
            % (met_bigg_id, compartment_bigg_id, model_bigg_id)
        )
    reactions_db = (
        session.query(Reaction.id, Reaction.name, Model.id)
        .join(ReactionMatrix)
        .join(ModelReaction)
        .join(Model)
        .filter(ReactionMatrix.compartmentalized_component_id == result_db[7])
        .filter(Model.id == result_db[8])
        .distinct()
    )
    model_db = get_model_list_for_metabolite(met_bigg_id, session)
    m_escher_maps = escher_map_queries.get_escher_maps_for_metabolite(
        met_bigg_id, compartment_bigg_id, model_bigg_id, session
    )
    model_result = [x for x in model_db if x["bigg_id"] != model_bigg_id]

    db_link_results = id_queries._get_db_links_for_model_comp_metabolite(
        met_bigg_id, session
    )

    old_id_results = id_queries._get_old_ids_for_model_comp_metabolite(
        met_bigg_id, compartment_bigg_id, model_bigg_id, session
    )

    return {
        "bigg_id": result_db[0],
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
    }
