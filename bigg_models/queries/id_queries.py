from collections import defaultdict
from cobradb.models import (
    DataSource,
    Compartment,
    CompartmentalizedComponent,
    Component,
    Gene,
    Model,
    ModelGene,
    ModelReaction,
    ModelCompartmentalizedComponent,
    OldIDSynonym,
    Reaction,
    Synonym,
)
from itertools import chain


def _compile_db_links(results):
    """Return links for the results that have a url_prefix."""
    links = {}
    sources = defaultdict(list)
    for data_source_bigg_id, data_source_name, url_prefix, synonym in results:
        if url_prefix is None:
            continue
        link = url_prefix + synonym
        sources[data_source_name].append({"link": link, "id": synonym})
    return dict(sources)


def _get_db_links_for_reaction(reaction_bigg_id, session):
    result_db = (
        session.query(
            DataSource.bigg_id, DataSource.name, DataSource.url_prefix, Synonym.synonym
        )
        .join(Synonym)
        .join(Reaction, Reaction.id == Synonym.ome_id)
        .filter(Synonym.type == "reaction")
        .filter(Reaction.id == reaction_bigg_id)
    )
    return _compile_db_links(result_db)


def _get_db_links_for_model_reaction(reaction_bigg_id, session):
    return _get_db_links_for_reaction(reaction_bigg_id, session)


def _get_old_ids_for_reaction(reaction_bigg_id, session):
    result_db = (
        session.query(Synonym.synonym)
        .join(OldIDSynonym)
        .join(ModelReaction, ModelReaction.id == OldIDSynonym.ome_id)
        .filter(OldIDSynonym.type == "model_reaction")
        .join(Reaction)
        .filter(Reaction.id == reaction_bigg_id)
        .distinct()
    )
    return [x[0] for x in result_db]


def _get_old_ids_for_model_reaction(model_bigg_id, reaction_bigg_id, session):
    result_db = (
        session.query(Synonym.synonym)
        .join(OldIDSynonym)
        .join(ModelReaction, ModelReaction.id == OldIDSynonym.ome_id)
        .filter(OldIDSynonym.type == "model_reaction")
        .join(Reaction)
        .join(Model)
        .filter(Reaction.id == reaction_bigg_id)
        .filter(Model.id == model_bigg_id)
        .distinct()
    )
    return [x[0] for x in result_db]


def _get_db_links_for_model_gene(gene_bigg_id, session):
    result_db = (
        session.query(
            DataSource.bigg_id, DataSource.name, DataSource.url_prefix, Synonym.synonym
        )
        .join(Synonym)
        .join(Gene, Gene.id == Synonym.ome_id)
        .filter(Synonym.type == "gene")
        .filter(Gene.bigg_id == gene_bigg_id)
    )
    return _compile_db_links(result_db)


def _get_old_ids_for_model_gene(gene_bigg_id, model_bigg_id, session):
    result_db = (
        session.query(Synonym.synonym)
        .join(OldIDSynonym)
        .join(ModelGene, ModelGene.id == OldIDSynonym.ome_id)
        .filter(OldIDSynonym.type == "model_gene")
        .join(Gene)
        .join(Model)
        .filter(Gene.bigg_id == gene_bigg_id)
        .filter(Model.id == model_bigg_id)
        .distinct()
    )
    return [x[0] for x in result_db]


def _get_db_links_for_metabolite(met_bigg_id, session):
    # result_db_1 = (
    #     session.query(
    #         DataSource.bigg_id, DataSource.name, DataSource.url_prefix, Synonym.synonym
    #     )
    #     .join(Synonym)
    #     .join(Component, Component.id == Synonym.ome_id)
    #     .filter(Synonym.type == "component")
    #     .filter(Component.id == met_bigg_id)
    # )
    # result_db_2 = (
    #     session.query(
    #         DataSource.bigg_id, DataSource.name, DataSource.url_prefix, Synonym.synonym
    #     )
    #     .join(Synonym)
    #     .join(
    #         CompartmentalizedComponent, CompartmentalizedComponent.id == Synonym.ome_id
    #     )
    #     .filter(Synonym.type == "compartmentalized_component")
    #     .join(Component, Component.id == CompartmentalizedComponent.component_id)
    #     .join(Compartment, Compartment.id == CompartmentalizedComponent.compartment_id)
    #     .filter(Component.id == met_bigg_id)
    # )
    result_db_1, result_db_2 = [], []
    return _compile_db_links(chain(result_db_1, result_db_2))


def _get_old_ids_for_metabolite(met_bigg_id, session):
    result_db = (
        session.query(Synonym.synonym)
        .join(OldIDSynonym)
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.id == OldIDSynonym.ome_id,
        )
        .filter(OldIDSynonym.type == "model_compartmentalized_component")
        .filter(Synonym.type == "component")
        .join(CompartmentalizedComponent)
        .join(Component)
        .filter(Component.id == met_bigg_id)
        .distinct()
    )
    return [x[0] for x in result_db]


def _get_db_links_for_model_comp_metabolite(met_bigg_id, session):
    return _get_db_links_for_metabolite(met_bigg_id, session)


def _get_old_ids_for_model_comp_metabolite(
    met_bigg_id, compartment_bigg_id, model_bigg_id, session
):
    result_db = (
        session.query(Synonym.synonym)
        .join(OldIDSynonym)
        .join(
            ModelCompartmentalizedComponent,
            ModelCompartmentalizedComponent.id == OldIDSynonym.ome_id,
        )
        .filter(OldIDSynonym.type == "model_compartmentalized_component")
        .filter(Synonym.type == "compartmentalized_component")
        .join(CompartmentalizedComponent)
        .join(Compartment)
        .join(Component)
        .join(Model)
        .filter(Component.id == met_bigg_id)
        .filter(Compartment.id == compartment_bigg_id)
        .filter(Model.id == model_bigg_id)
        .distinct()
    )
    return [x[0] for x in result_db]
