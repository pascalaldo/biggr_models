from typing import List, NewType, Optional, Type, Union
from bigg_models.version import __version__ as version, __api_version__ as api_version
import bigg_models.handlers.utils as handler_utils

from cobradb.models import (
    Base,
    Component,
    CompartmentalizedComponent,
    DatabaseVersion,
    Gene,
    Model,
    ModelCompartmentalizedComponent,
    ModelGene,
    ModelReaction,
    Reaction,
    Publication,
    PublicationModel,
)

from sqlalchemy import desc, asc, and_, not_
from os.path import abspath, dirname, join

root_directory = abspath(join(dirname(__file__), ".."))

IDType = NewType("IDType", Union[str, int])
StrList = NewType("StrList", List[str])
OptStr = NewType("OptStr", Optional[str])


class NotFoundError(Exception):
    pass


class RedirectError(Exception):
    pass


def _shorten_name(name, l=100):
    if name is None:
        return None
    if len(name) > l:
        return name[:l] + "..."
    else:
        return name


def _apply_order_limit_offset(
    query, sort_column_object=None, sort_direction="ascending", page=None, size=None
):
    """Get model metabolites.

    Arguments
    ---------

    query: A sqlalchemy query

    sort_column_object: An object or list of objects to order by, or None to not
    order.

    sort_direction: Either 'ascending' or 'descending'. Ignored if
    sort_column_object is None.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    Returns
    -------

    An updated query.

    """
    # sort
    if sort_column_object is not None:
        if sort_direction == "descending":
            direction_fn = desc
        elif sort_direction == "ascending":
            direction_fn = asc
        else:
            raise ValueError("Bad sort direction %s" % sort_direction)

        if type(sort_column_object) is list:
            query = query.order_by(*[direction_fn(x) for x in sort_column_object])
        else:
            query = query.order_by(direction_fn(sort_column_object))

    # limit and offset
    if page is not None and size is not None:
        page = int(page)
        size = int(size)
        offset = page * size
        query = query.limit(size).offset(offset)

    return query


def _add_pub_filter(query):
    return (
        query.join(PublicationModel, PublicationModel.model_id == Model.id)
        .join(Publication, Publication.id == PublicationModel.publication_id)
        .filter(
            not_(
                and_(
                    Publication.reference_id.in_(["24277855", "27667363"]),
                    Publication.reference_type == "pmid",
                )
            )
        )
    )


def _add_multistrain_filter(session, query, from_class):
    if from_class is Reaction:
        return query.filter(
            Reaction.id.in_(
                _add_pub_filter(
                    session.query(Reaction.id)
                    .join(ModelReaction, ModelReaction.reaction_id == Reaction.id)
                    .join(Model, Model.id == ModelReaction.model_id)
                )
            )
        )
    elif from_class is Component:
        return query.filter(
            Component.id.in_(
                _add_pub_filter(
                    session.query(Component.id)
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
                )
            )
        )
    elif from_class is Model or from_class is Gene:
        return _add_pub_filter(query)
    else:
        raise Exception


def get_gene_list_for_model(model_bigg_id, session):
    result = (
        session.query(Gene.bigg_id, Gene.name, Model.organism, Model.bigg_id)
        .join(ModelGene, ModelGene.gene_id == Gene.id)
        .join(Model, Model.id == ModelGene.model_id)
        .filter(Model.bigg_id == model_bigg_id)
    )
    return [
        {"bigg_id": x[0], "name": x[1], "organism": x[2], "model_bigg_id": x[3]}
        for x in result
    ]


# -----------
# Utilities
# -----------


def build_reaction_string(
    metabolite_list,
    lower_bound,
    upper_bound,
    universal=False,
    html=True,
    format_met=None,
):
    reaction_string_parts = [[], []]
    for met in metabolite_list:
        part_i = int(float(met["coefficient"]) > 0)
        formatted_bigg_id = handler_utils.format_bigg_id(
            met["bigg_id"], format_type=format_met
        )
        if abs(float(met["coefficient"])) != 1:
            coeff = float(abs(met["coefficient"]))
            if coeff.is_integer():
                coeff = int(coeff)
            reaction_string_parts[part_i].append(
                f"<span class='fw-bold'>{coeff}</span> {formatted_bigg_id}"
            )
        else:
            reaction_string_parts[part_i].append(formatted_bigg_id)

    both_arrow = " &#8652; " if html else " <-> "
    left_arrow = " &#x2190; " if html else " <-- "
    right_arrow = " &#x2192; " if html else " --> "

    if len(metabolite_list) == 1 or universal is True:
        arrow = both_arrow
    elif lower_bound < 0 and upper_bound <= 0:
        arrow = left_arrow
    elif lower_bound >= 0 and upper_bound > 0:
        arrow = right_arrow
    else:
        arrow = both_arrow
    reaction_string = arrow.join(" + ".join(x) for x in reaction_string_parts)
    return reaction_string


# version


def database_version(session):
    return {
        "last_updated": str(session.query(DatabaseVersion).first().date_time),
        "bigg_models_version": version,
        "api_version": api_version,
    }


def convert_id_to_query_filter(bigg_id: IDType, obj_cls: Type[Base]):
    if isinstance(bigg_id, int):
        return obj_cls.id == bigg_id
    if isinstance(bigg_id, str):
        return obj_cls.bigg_id == bigg_id
    raise ValueError()
