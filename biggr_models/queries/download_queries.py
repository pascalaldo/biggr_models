from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, subqueryload
from cobradb.models import (
    Component,
    ComponentReferenceMapping,
    Reaction,
    ReactionMatrix,
    UniversalComponent,
    UniversalReaction,
    UniversalReactionMatrix,
)


def extract_reaction_participants(matrix):
    participants = []
    for m in matrix:
        bigg_id = m.compartmentalized_component.bigg_id
        coefficient = m.universal_reaction_matrix.coefficient
        participants.append((coefficient, bigg_id))
    return participants


def extract_universal_reaction_participants(matrix):
    participants = []
    for m in matrix:
        bigg_id = m.universal_compartmentalized_component.bigg_id
        coefficient = m.coefficient
        participants.append((coefficient, bigg_id))
    return participants


def get_reactions(session: Session):
    query = select(Reaction)
    query = query.options(
        joinedload(Reaction.universal_reaction).options(
            joinedload(UniversalReaction.reference),
            subqueryload(UniversalReaction.matrix).joinedload(
                UniversalReactionMatrix.universal_compartmentalized_component
            ),
        ),
        subqueryload(Reaction.matrix).options(
            joinedload(ReactionMatrix.compartmentalized_component),
            joinedload(ReactionMatrix.universal_reaction_matrix),
        ),
    )
    query = query.filter(Reaction.collection_id == None)
    results = session.scalars(query).all()

    reactions = []
    for reaction_db in results:
        d = {
            "bigg_id": reaction_db.bigg_id,
            "copy_number": reaction_db.copy_number,
            "participants": extract_reaction_participants(reaction_db.matrix),
            "universalreaction__bigg_id": reaction_db.universal_reaction.bigg_id,
            "universalreaction__name": reaction_db.universal_reaction.name,
            "universalreaction__participants": extract_universal_reaction_participants(
                reaction_db.universal_reaction.matrix
            ),
            "universalreaction__is_exchange": reaction_db.universal_reaction.is_exchange,
            "universalreaction__is_pseudo": reaction_db.universal_reaction.is_pseudo,
            "universalreaction__is_transport": reaction_db.universal_reaction.is_transport,
        }
        if (reference_db := reaction_db.universal_reaction.reference) is not None:
            d["referencereaction__bigg_id"] = reference_db.bigg_id
        reactions.append(d)
    return reactions


def get_metabolites(session: Session):
    query = select(Component)
    query = query.options(
        joinedload(Component.universal_component).options(
            subqueryload(UniversalComponent.default_component),
            subqueryload(UniversalComponent.old_bigg_ids),
        ),
        subqueryload(Component.reference_mappings).joinedload(
            ComponentReferenceMapping.reference_compound
        ),
        subqueryload(Component.compartmentalized_components),
    )
    query = query.filter(Component.collection_id == None)
    results = session.scalars(query).all()

    metabolites = []
    for component_db in results:
        d = {
            "bigg_id": component_db.bigg_id,
            "name": component_db.name,
            "formula": component_db.formula,
            "charge": component_db.charge,
            "universalcomponent__bigg_id": component_db.universal_component.bigg_id,
            "universalcomponent__name": component_db.universal_component.name,
            "universalcomponent__default_component": component_db.universal_component.default_component.bigg_id,
            "universalcomponent__old_bigg_ids": [
                x.old_bigg_id for x in component_db.universal_component.old_bigg_ids
            ],
            "compartmentalized_components": [
                x.bigg_id for x in component_db.compartmentalized_components
            ],
            "references": [
                x.reference_compound.bigg_id for x in component_db.reference_mappings
            ],
        }
        metabolites.append(d)
    return metabolites
