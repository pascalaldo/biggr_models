# -*- coding: utf-8 -*-

from bigg_models.version import __version__ as version, __api_version__ as api_version

from cobradb.models import (
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
    metabolite_list, lower_bound, upper_bound, universal=False, html=True
):
    post_reaction_string = ""
    pre_reaction_string = ""
    for met in metabolite_list:
        if float(met["coefficient"]) < 0:
            if float(met["coefficient"]) != -1:
                pre_reaction_string += (
                    "{}".format(abs(met["coefficient"]))
                    + " "
                    + met["bigg_id"]
                    # + "_"
                    # + met["compartment_bigg_id"]
                    + " + "
                )
            else:
                pre_reaction_string += (
                    # met["bigg_id"] + "_" + met["compartment_bigg_id"] + " + "
                    met["bigg_id"]
                    + " + "
                )
        if float(met["coefficient"]) > 0:
            if float(met["coefficient"]) != 1:
                post_reaction_string += (
                    "{}".format(abs(met["coefficient"]))
                    + " "
                    + met["bigg_id"]
                    # + "_"
                    # + met["compartment_bigg_id"]
                    + " + "
                )
            else:
                post_reaction_string += (
                    # met["bigg_id"] + "_" + met["compartment_bigg_id"] + " + "
                    met["bigg_id"]
                    + " + "
                )

    both_arrow = " &#8652; " if html else " <-> "
    left_arrow = " &#x2190; " if html else " <-- "
    right_arrow = " &#x2192; " if html else " --> "

    if len(metabolite_list) == 1 or universal is True:
        reaction_string = (
            pre_reaction_string[:-3] + both_arrow + post_reaction_string[:-3]
        )
    elif lower_bound < 0 and upper_bound <= 0:
        reaction_string = (
            pre_reaction_string[:-3] + left_arrow + post_reaction_string[:-3]
        )
    elif lower_bound >= 0 and upper_bound > 0:
        reaction_string = (
            pre_reaction_string[:-3] + right_arrow + post_reaction_string[:-3]
        )
    else:
        reaction_string = (
            pre_reaction_string[:-3] + both_arrow + post_reaction_string[:-3]
        )

    return reaction_string


# version


def database_version(session):
    return {
        "last_updated": str(session.query(DatabaseVersion).first().date_time),
        "bigg_models_version": version,
        "api_version": api_version,
    }
