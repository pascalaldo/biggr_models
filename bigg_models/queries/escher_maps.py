from bigg_models.queries import general
from cobradb.models import (
    EscherMap,
    EscherMapMatrix,
    Compartment,
    CompartmentalizedComponent,
    Component,
    Model,
    ModelCompartmentalizedComponent,
    ModelReaction,
    Reaction,
)


# Escher maps
def get_escher_maps_for_model(model_id, session):
    result_db = session.query(EscherMap).filter(EscherMap.model_id == model_id)
    return [{"map_name": x.map_name, "element_id": None} for x in result_db]


def get_escher_maps_for_reaction(reaction_bigg_id, model_bigg_id, session):
    result_db = (
        session.query(EscherMap.map_name, EscherMapMatrix.escher_map_element_id)
        .join(EscherMapMatrix, EscherMapMatrix.escher_map_id == EscherMap.id)
        .join(ModelReaction, ModelReaction.id == EscherMapMatrix.ome_id)
        .filter(EscherMapMatrix.type == "model_reaction")
        .join(Model, Model.id == ModelReaction.model_id)
        .join(Reaction, Reaction.id == ModelReaction.reaction_id)
        .filter(Reaction.bigg_id == reaction_bigg_id)
        .filter(Model.bigg_id == model_bigg_id)
        .order_by(EscherMap.priority.desc())
    )
    return [{"map_name": x[0], "element_id": x[1]} for x in result_db]


def get_escher_maps_for_metabolite(
    metabolite_bigg_id, compartment_bigg_id, model_bigg_id, session
):
    result_db = (
        session.query(EscherMap.map_name, EscherMapMatrix.escher_map_element_id)
        .join(EscherMapMatrix, EscherMapMatrix.escher_map_id == EscherMap.id)
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.id == EscherMapMatrix.ome_id,
        )
        .filter(EscherMapMatrix.type == "model_compartmentalized_component")
        .join(Model, Model.id == ModelCompartmentalizedComponent.model_id)
        .join(
            CompartmentalizedComponent,
            CompartmentalizedComponent.id
            == ModelCompartmentalizedComponent.compartmentalized_component_id,
        )
        .join(Component, Component.id == CompartmentalizedComponent.component_id)
        .join(Compartment, Compartment.id == CompartmentalizedComponent.compartment_id)
        .filter(Component.bigg_id == metabolite_bigg_id)
        .filter(Compartment.bigg_id == compartment_bigg_id)
        .filter(Model.bigg_id == model_bigg_id)
        .order_by(EscherMap.priority.desc())
    )
    return [{"map_name": x[0], "element_id": x[1]} for x in result_db]


def json_for_map(map_name, session):
    result_db = (
        session.query(EscherMap.map_data).filter(EscherMap.map_name == map_name).first()
    )
    if result_db is None:
        raise general.NotFoundError("Could not find Escher map %s" % map_name)

    return result_db[0].decode("utf8")
