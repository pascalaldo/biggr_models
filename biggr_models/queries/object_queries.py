from collections.abc import Iterable
from typing import Any, Type
from cobradb.models import (
    Annotation,
    AnnotationLink,
    Base,
    Chromosome,
    Compartment,
    CompartmentalizedComponent,
    Component,
    Genome,
    InChI,
    MemoteResult,
    MemoteTest,
    Model,
    ModelCollection,
    Publication,
    Reaction,
    ReactionMatrix,
    ReferenceCompound,
    ReferenceReaction,
    ReferenceReactionParticipant,
    ReferenceReactivePart,
    ReferenceReactivePartMatrix,
    Taxon,
    TaxonomicRank,
    UniversalComponent,
    UniversalReaction,
)
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, subqueryload

from biggr_models.queries import utils

OBJECT_DEFAULT_LOAD = {
    Model: (
        joinedload(Model.genome),
        joinedload(Model.model_count),
        joinedload(Model.collection),
        subqueryload(Model.publication_models),
    ),
    ModelCollection: (),
    Reaction: (
        joinedload(Reaction.collection),
        subqueryload(Reaction.matrix).joinedload(
            ReactionMatrix.compartmentalized_component
        ),
    ),
    UniversalReaction: (joinedload(UniversalReaction.reference),),
    ReferenceReaction: (
        subqueryload(ReferenceReaction.reaction_participants).joinedload(
            ReferenceReactionParticipant.compound
        )
    ),
    Component: (),
    UniversalComponent: (
        joinedload(UniversalComponent.reference_mapping),
        joinedload(UniversalComponent.collection),
        subqueryload(UniversalComponent.components),
    ),
    CompartmentalizedComponent: (joinedload(CompartmentalizedComponent.compartment),),
    ReferenceCompound: (
        joinedload(ReferenceCompound.inchi),
        subqueryload(ReferenceCompound.reactive_part_matrix).joinedload(
            ReferenceReactivePartMatrix.reactive_part
        ),
    ),
    ReferenceReactivePart: (
        joinedload(ReferenceReactivePart.inchi),
        subqueryload(ReferenceReactivePart.matrix).joinedload(
            ReferenceReactivePartMatrix.compound
        ),
    ),
    Genome: (subqueryload(Genome.chromosomes),),
    Chromosome: (joinedload(Chromosome.genome)),
    Compartment: (),
    Publication: (subqueryload(Publication.publication_models),),
    InChI: (),
    MemoteTest: (),
    MemoteResult: (
        joinedload(MemoteResult.test),
        joinedload(MemoteResult.model),
        joinedload(MemoteResult.model_reaction),
        joinedload(MemoteResult.model_compartmentalized_component),
        joinedload(MemoteResult.model_gene),
    ),
    Annotation: (
        subqueryload(Annotation.links).joinedload(AnnotationLink.data_source),
    ),
    Taxon: (joinedload(Taxon.rank),),
    TaxonomicRank: (),
}


def get_object(
    obj_type: Type[Base],
    session: Session,
    id: utils.IDType,
):
    id_sel = utils.convert_id_to_query_filter(id, obj_type)
    obj_db = session.scalars(
        select(obj_type).options(*OBJECT_DEFAULT_LOAD[obj_type]).filter(id_sel).limit(1)
    ).first()

    if obj_db is None:
        raise utils.NotFoundError(f"No Object found with BiGG ID {id}")

    return {"id": id, "object": obj_db}


def get_object_property(
    parent_obj_type: Type[Base],
    obj_type: Type[Base],
    property: Any,
    session: Session,
    id: int,
):
    id_sel = utils.convert_id_to_query_filter(id, parent_obj_type)
    obj_db = session.scalars(
        select(parent_obj_type)
        .options(subqueryload(property).options(*OBJECT_DEFAULT_LOAD.get(obj_type, ())))
        .filter(id_sel)
        .limit(1)
    ).first()

    if obj_db is None:
        raise utils.NotFoundError(f"No Object found with BiGG ID {id}")

    results = getattr(obj_db, property.key)

    if isinstance(results, Iterable):
        results = list(results)

    return {"id": id, "objects": results}
