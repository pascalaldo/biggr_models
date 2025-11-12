from cobradb.models import (
    CompartmentalizedComponent,
    Component,
    EscherModule,
    Model,
    ModelCompartmentalizedComponent,
    ModelReaction,
    ModelReactionEscherMapping,
    NotFoundError,
    Reaction,
    ReactionMatrix,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, subqueryload


def get_model_reactions_for_escher_map(
    session: Session, model_bigg_id: str, map_bigg_id: str
):
    model_db = session.scalars(
        select(Model).filter(Model.bigg_id == model_bigg_id).limit(1)
    ).first()
    if model_db is None:
        raise NotFoundError("Model not found.")
    model_reactions = session.scalars(
        select(ModelReaction)
        .options(
            joinedload(ModelReaction.reaction).options(
                joinedload(Reaction.universal_reaction),
                subqueryload(Reaction.matrix).options(
                    joinedload(ReactionMatrix.universal_reaction_matrix),
                    joinedload(ReactionMatrix.compartmentalized_component).options(
                        joinedload(
                            CompartmentalizedComponent.universal_compartmentalized_component
                        ),
                        joinedload(CompartmentalizedComponent.component).joinedload(
                            Component.universal_component
                        ),
                        subqueryload(
                            CompartmentalizedComponent.model_compartmentalized_components.and_(
                                ModelCompartmentalizedComponent.model_id == model_db.id
                            )
                        ),
                    ),
                ),
            )
        )
        .join(ModelReaction.model)
        .join(ModelReaction.escher_mappings)
        .join(ModelReactionEscherMapping.escher_module)
        .filter(Model.id == model_db.id)
        .filter(EscherModule.bigg_id == map_bigg_id)
        .order_by(ModelReaction.bigg_id)
    ).all()
    return model_reactions
