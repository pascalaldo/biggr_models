from sqlalchemy.orm import joinedload, selectinload
from bigg_models.queries import escher_map_queries, utils, id_queries

from cobradb.models import (
    Annotation,
    AnnotationLink,
    AnnotationProperty,
    ReferenceCompoundAnnotationMapping,
    ComponentAnnotationMapping,
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
    ModelCompartmentalizedComponent,
    ModelReaction,
    Model,
    Reaction,
    ReactionMatrix,
    InChI,
)

from sqlalchemy import func, select

LINKOUT_PROPERTY_KEYS = {
    "name": "Names",
    "smiles": "SMILES",
    "mass": ("Molecular Mass", "g/mol"),
    "is_obsolete": "Obsolete",
}

ANNOTATION_TYPES = {
    "seed": "ModelSEED",
    "chebi": "ChEBI",
    "rhea": "RHEA",
}


def get_universal_metabolites_count(session):
    return session.scalars(
        select(func.count(UniversalComponent.id)).filter(
            UniversalComponent.model_id == None
        )
    ).first()


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
        "bigg_id": func.lower(UniversalComponent.bigg_id),
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
    query = select(UniversalComponent.bigg_id, UniversalComponent.name).filter(
        UniversalComponent.model_id == None
    )

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    query = session.execute(query).all()
    return [{"bigg_id": x[0], "name": x[1]} for x in query]


def get_model_metabolites_count(model_bigg_id, session):
    """Count the model metabolites."""
    return session.scalars(
        select(func.count(ModelCompartmentalizedComponent.id))
        .join(ModelCompartmentalizedComponent.model)
        .filter(Model.bigg_id == model_bigg_id)
    ).first()


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
            func.lower(CompartmentalizedComponent.bigg_id),
        ],
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
        select(
            CompartmentalizedComponent.bigg_id,
            Component.name,
            Model.bigg_id,
            Model.organism,
            Compartment.bigg_id,
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
        .join(CompartmentalizedComponent.compartment)
        .filter(Model.bigg_id == model_bigg_id)
    )

    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )

    query = session.execute(query).all()
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


def process_annotation_for_template(ann: Annotation):
    d = {
        "id": ann.id,
        "bigg_id": ann.bigg_id,
        "identifier": (
            ann.bigg_id
            if ann.bigg_id.startswith("CHEBI:")
            else ann.bigg_id.split(":", maxsplit=1)[-1]
        ),
        "default_data_source_id": ann.default_data_source_id,
        "type": ANNOTATION_TYPES.get(ann.type, ann.type),
    }
    d_links = {}
    for link in ann.links:
        source_name = link.data_source.name
        d_link = {
            "value": link.identifier,
            "url": f"{link.data_source.url_prefix}{link.identifier}",
        }
        if source_name in d_links:
            d_links[source_name].append(d_link)
        else:
            d_links[source_name] = [d_link]
    d["links"] = d_links

    d_props = {}
    for prop in ann.properties:
        new_prop_key = LINKOUT_PROPERTY_KEYS.get(prop.key)
        if new_prop_key is None:
            continue
        if new_prop_key in d_props:
            d_props[new_prop_key].append(prop.value)
        else:
            d_props[new_prop_key] = [prop.value]
    d["properties"] = d_props
    return d


def get_metabolite(met_bigg_id, session):
    result_db = session.execute(
        select(UniversalComponent.bigg_id, UniversalComponent.name)
        .filter(UniversalComponent.bigg_id == met_bigg_id)
        .limit(1)
    ).first()
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

    comp_comp_db = session.execute(
        select(
            CompartmentalizedComponent.bigg_id,
            Model.bigg_id,
            Model.organism,
        )
        .join(
            UniversalCompartmentalizedComponent,
            CompartmentalizedComponent.universal_compartmentalized_component_id
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
        .filter(UniversalComponent.bigg_id == met_bigg_id)
    ).all()

    default_component_db = session.scalars(
        select(Component)
        .join(
            ComponentReferenceMapping,
            Component.id == ComponentReferenceMapping.component_id,
        )
        .join(
            UniversalComponentReferenceMapping,
            ComponentReferenceMapping.id
            == UniversalComponentReferenceMapping.mapping_id,
        )
        .join(UniversalComponentReferenceMapping.universal_component)
        .filter(UniversalComponent.bigg_id == met_bigg_id)
        .limit(1)
    ).first()
    default_component = None

    if default_component_db:
        default_component = {
            "bigg_id": default_component_db.bigg_id,
            "formula": default_component_db.formula,
            "charge": default_component_db.charge,
        }

    components_db = session.execute(
        select(Component, ComponentReferenceMapping, ReferenceCompound, InChI)
        .join(
            ComponentReferenceMapping,
            ComponentReferenceMapping.component_id == Component.id,
        )
        .join(
            ReferenceCompound,
            ReferenceCompound.id == ComponentReferenceMapping.reference_compound_id,
        )
        .outerjoin(InChI, InChI.id == ReferenceCompound.inchi_id)
        .join(Component.universal_component)
        .filter(UniversalComponent.bigg_id == met_bigg_id)
        .order_by(Component.charge)
    ).all()

    components = []
    for component, refmap, ref_db, inchi_db in components_db:
        ref = None
        ref_ann = None
        if ref_db is not None:
            ref = {
                "bigg_id": ref_db.bigg_id,
                "name": ref_db.name,
                "type": ref_db.compound_type,
                "charge": ref_db.charge,
                "formula": ref_db.formula,
                "ref_n": refmap.reference_n,
                "inchi": inchi_db,
            }
            ref_ann = session.execute(
                select(Annotation, ReferenceCompoundAnnotationMapping)
                .options(
                    selectinload(Annotation.properties),
                    selectinload(Annotation.links).joinedload(
                        AnnotationLink.data_source
                    ),
                )
                .join(Annotation.reference_compound_mappings)
                .filter(
                    ReferenceCompoundAnnotationMapping.reference_compound_id
                    == ref_db.id
                )
                .join(ReferenceCompoundAnnotationMapping.reference_compound)
            ).all()
            if ref_ann:
                ref["annotations"] = [
                    (process_annotation_for_template(ann), ann_map)
                    for ann, ann_map in ref_ann
                ]
        skip = False
        for comp in components:
            if comp["bigg_id"] == component.bigg_id:
                if ref is not None:
                    comp["reference"].append(ref)
                skip = True
                break
        if skip:
            continue
        comp_ann = session.execute(
            select(Annotation, ComponentAnnotationMapping)
            .options(
                selectinload(Annotation.properties), selectinload(Annotation.links)
            )
            .join(Annotation.component_mappings)
            .filter(ComponentAnnotationMapping.component_id == component.id)
        ).all()

        d = {
            "bigg_id": component.bigg_id,
            "name": component.name,
            "charge": component.charge,
            "formula": component.formula,
            "reference": [] if ref is None else [ref],
        }
        if comp_ann:
            d["annotations"] = [
                (process_annotation_for_template(ann), ann_map)
                for ann, ann_map in comp_ann
            ]
        if (
            default_component is not None
            and default_component["bigg_id"] == d["bigg_id"]
        ):
            d["default"] = True
            components.insert(0, d)
        else:
            components.append(d)

    for comp in components:
        all_annotations = []
        for ref in comp["reference"]:
            all_annotations.extend(ref.get("annotations", []))
        all_annotations.extend(comp.get("annotations", []))
        comp["all_annotations"] = all_annotations
    # database links and old ids
    db_link_results = id_queries._get_db_links_for_metabolite(met_bigg_id, session)
    old_id_results = id_queries._get_old_ids_for_metabolite(met_bigg_id, session)

    return {
        "bigg_id": result_db[0],
        "name": result_db[1],
        "database_links": db_link_results,
        "old_identifiers": old_id_results,
        # "compartments_in_models": [],
        "components": components,
        "default_component": default_component,
        "compartments_in_models": [
            {"bigg_id": c[0], "model_bigg_id": c[1], "organism": c[2]}
            for c in comp_comp_db
        ],
    }


def get_model_list_for_metabolite(metabolite_bigg_id, session):
    result = session.execute(
        select(Model.bigg_id, CompartmentalizedComponent.compartment_id)
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.compartmentalized_component_id
            == CompartmentalizedComponent.id,
        )
        .join(CompartmentalizedComponent.component)
        .filter(Component.bigg_id == metabolite_bigg_id)
    )
    return [{"bigg_id": x[0], "compartment_bigg_id": x[1]} for x in result]


def get_model_comp_metabolite(comp_met_id, model_bigg_id, session):
    result_db = session.execute(
        select(
            Component,
            UniversalComponent,
            CompartmentalizedComponent,
            Compartment,
            Model,
        )
        .join(Component.universal_component)
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
        .filter(CompartmentalizedComponent.bigg_id == comp_met_id)
        .filter(Model.bigg_id == model_bigg_id)
        .limit(1)
    ).first()
    if result_db is None:
        raise utils.NotFoundError(
            "Component %s not in model %s" % (comp_met_id, model_bigg_id)
        )
    component = result_db.Component
    met_bigg_id = component.bigg_id
    reference_db = session.execute(
        select(ReferenceCompound, InChI)
        .join(
            ComponentReferenceMapping,
            ReferenceCompound.id == ComponentReferenceMapping.reference_compound_id,
        )
        .outerjoin(InChI, InChI.id == ReferenceCompound.inchi_id)
        .filter(
            ComponentReferenceMapping.component_id == result_db.Component.id,
        )
    ).all()
    references = []
    for ref_db in reference_db:
        ref = {
            "bigg_id": ref_db[0].bigg_id,
            "name": ref_db[0].name,
            "type": ref_db[0].compound_type,
            "charge": ref_db[0].charge,
            "formula": ref_db[0].formula,
            "inchi": ref_db[1],
        }
        ref_ann = session.execute(
            select(Annotation, ReferenceCompoundAnnotationMapping)
            .options(
                selectinload(Annotation.properties),
                selectinload(Annotation.links).joinedload(AnnotationLink.data_source),
            )
            .join(Annotation.reference_compound_mappings)
            .filter(
                ReferenceCompoundAnnotationMapping.reference_compound_id == ref_db[0].id
            )
            .join(ReferenceCompoundAnnotationMapping.reference_compound)
        ).all()
        if ref_ann:
            ref["annotations"] = [
                (process_annotation_for_template(ann), ann_map)
                for ann, ann_map in ref_ann
            ]

        references.append(ref)

    reactions_db = session.execute(
        select(
            UniversalReaction.bigg_id, UniversalReaction.name, ModelReaction.model_id
        )
        .join(Reaction, Reaction.universal_reaction_id == UniversalReaction.id)
        .join(ReactionMatrix, ReactionMatrix.reaction_id == Reaction.id)
        .filter(
            ReactionMatrix.compartmentalized_component_id
            == result_db.CompartmentalizedComponent.id
        )
        .join(
            UniversalReactionMatrix,
            ReactionMatrix.universal_reaction_matrix_id == UniversalReactionMatrix.id,
        )
        .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
        .filter(ModelReaction.model_id == result_db.Model.id)
        .distinct()
    ).all()
    model_db = get_model_list_for_metabolite(met_bigg_id, session)
    # m_escher_maps = escher_map_queries.get_escher_maps_for_metabolite(
    #     met_bigg_id, compartment_bigg_id, model_bigg_id, session
    # )
    m_escher_maps = []
    model_result = [x for x in model_db if x["bigg_id"] != model_bigg_id]

    comp_ann = session.execute(
        select(Annotation, ComponentAnnotationMapping)
        .options(selectinload(Annotation.properties), selectinload(Annotation.links))
        .join(Annotation.component_mappings)
        .filter(ComponentAnnotationMapping.component_id == component.id)
    ).all()

    comp_ann = [
        (process_annotation_for_template(ann), ann_map) for ann, ann_map in comp_ann
    ]
    all_ann = []
    for ref in references:
        if (ref_ann := ref.get("annotations")) is not None:
            all_ann.extend(ref_ann)
    all_ann.extend(comp_ann)

    return {
        "bigg_id": result_db.CompartmentalizedComponent.bigg_id,
        "universal_id": result_db.UniversalComponent.bigg_id,
        "name": result_db.Component.name,
        "compartment_bigg_id": result_db.Compartment.bigg_id,
        "compartment_name": result_db.Compartment.name,
        "model_bigg_id": result_db.Model.bigg_id,
        "formula": result_db.Component.formula,
        "charge": result_db.Component.charge,
        "reactions": [
            {"bigg_id": r[0], "name": r[1], "model_bigg_id": r[2]} for r in reactions_db
        ],
        "escher_maps": m_escher_maps,
        "other_models_with_metabolite": model_result,
        "references": references,
        "model_specific": (result_db.Component.model_id is not None),
        "all_annotations": all_ann,
    }
