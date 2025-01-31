from bigg_models.queries import escher_maps, general, old_ids

from cobradb.models import (
    CompartmentalizedComponent,
    Component,
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
    return session.query(Component).count()


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
        "bigg_id": func.lower(Component.bigg_id),
        "name": func.lower(Component.name),
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
    query = session.query(Component.bigg_id, Component.name)

    # order and limit
    query = general._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def get_model_metabolites_count(model_bigg_id, session):
    """Count the model metabolites."""
    return (
        session.query(Component)
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
        .filter(Model.bigg_id == model_bigg_id)
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

    # set up the query
    query = (
        session.query(
            Component.bigg_id,
            Component.name,
            Model.bigg_id,
            Model.organism,
            Compartment.bigg_id,
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
        .filter(Model.bigg_id == model_bigg_id)
    )

    # order and limit
    query = general._apply_order_limit_offset(
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
        session.query(Component.bigg_id, Component.name)
        .filter(Component.bigg_id == met_bigg_id)
        .first()
    )
    if result_db is None:
        # Look for a result with a deprecated ID
        res_db = (
            session.query(DeprecatedID, Component)
            .filter(DeprecatedID.type == "component")
            .filter(DeprecatedID.deprecated_id == met_bigg_id)
            .join(Component, Component.id == DeprecatedID.ome_id)
            .first()
        )
        if res_db:
            raise general.RedirectError(res_db[1].bigg_id)
        else:
            raise general.NotFoundError(
                "No Component found with BiGG ID " + met_bigg_id
            )

    comp_comp_db = (
        session.query(
            Compartment.bigg_id,
            Model.bigg_id,
            Model.organism,
            ModelCompartmentalizedComponent.formula,
            ModelCompartmentalizedComponent.charge,
        )
        .join(
            CompartmentalizedComponent,
            CompartmentalizedComponent.compartment_id == Compartment.id,
        )
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
        .join(Component, Component.id == CompartmentalizedComponent.component_id)
        .filter(Component.bigg_id == met_bigg_id)
    )
    formulae = list({y for y in (x[3] for x in comp_comp_db) if y is not None})
    charges = list({y for y in (x[4] for x in comp_comp_db) if y is not None})

    # database links and old ids
    db_link_results = old_ids._get_db_links_for_metabolite(met_bigg_id, session)
    old_id_results = old_ids._get_old_ids_for_metabolite(met_bigg_id, session)

    return {
        "bigg_id": result_db[0],
        "name": result_db[1],
        "formulae": formulae,
        "charges": charges,
        "database_links": db_link_results,
        "old_identifiers": old_id_results,
        "compartments_in_models": [
            {"bigg_id": c[0], "model_bigg_id": c[1], "organism": c[2]}
            for c in comp_comp_db
        ],
    }


def get_model_list_for_metabolite(metabolite_bigg_id, session):
    result = (
        session.query(Model.bigg_id, Compartment.bigg_id)
        .join(ModelCompartmentalizedComponent)
        .join(CompartmentalizedComponent)
        .join(Compartment)
        .join(Component)
        .filter(Component.bigg_id == metabolite_bigg_id)
    )
    return [{"bigg_id": x[0], "compartment_bigg_id": x[1]} for x in result]


def get_model_comp_metabolite(met_bigg_id, compartment_bigg_id, model_bigg_id, session):
    result_db = (
        session.query(
            Component.bigg_id,
            Component.name,
            Compartment.bigg_id,
            Compartment.name,
            Model.bigg_id,
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
        .filter(Component.bigg_id == met_bigg_id)
        .filter(Compartment.bigg_id == compartment_bigg_id)
        .filter(Model.bigg_id == model_bigg_id)
        .first()
    )
    if result_db is None:
        raise general.NotFoundError(
            "Component %s in compartment %s not in model %s"
            % (met_bigg_id, compartment_bigg_id, model_bigg_id)
        )
    reactions_db = (
        session.query(Reaction.bigg_id, Reaction.name, Model.bigg_id)
        .join(ReactionMatrix)
        .join(ModelReaction)
        .join(Model)
        .filter(ReactionMatrix.compartmentalized_component_id == result_db[7])
        .filter(Model.id == result_db[8])
        .distinct()
    )
    model_db = get_model_list_for_metabolite(met_bigg_id, session)
    m_escher_maps = escher_maps.get_escher_maps_for_metabolite(
        met_bigg_id, compartment_bigg_id, model_bigg_id, session
    )
    model_result = [x for x in model_db if x["bigg_id"] != model_bigg_id]

    db_link_results = old_ids._get_db_links_for_model_comp_metabolite(
        met_bigg_id, session
    )

    old_id_results = old_ids._get_old_ids_for_model_comp_metabolite(
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
