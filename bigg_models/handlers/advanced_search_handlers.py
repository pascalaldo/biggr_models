from cobradb.models import (
    Annotation,
    AnnotationLink,
    AnnotationProperty,
    Component,
    ComponentAnnotationMapping,
    ComponentIDMapping,
    ComponentReferenceMapping,
    DataSource,
    Model,
    ModelCollection,
    Reaction,
    ReactionAnnotationMapping,
    ReferenceCompound,
    ReferenceReaction,
    ReferenceReactionAnnotationMapping,
    UniversalCompartmentalizedComponent,
    UniversalComponent,
    UniversalReaction,
)
from sqlalchemy import distinct, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import aggregate_strings, array_agg
from bigg_models.handlers import utils
from bigg_models.queries import utils as query_utils

ALLOWED_SEARCH_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-()[]/:.,"
)

# agg_strings = lambda x: aggregate_strings(x, ", ")
# agg_strings = lambda x: array_agg(distinct(x))
agg_strings = lambda x: aggregate_strings(distinct(x), ", ")
process_string_array = lambda x: ", ".join(x)


def get_data_source_id(session: Session, bigg_id: str):
    return session.scalars(
        select(DataSource.id).filter(DataSource.bigg_id == bigg_id).limit(1)
    ).first()


DATA_SOURCE_IDS = {
    "RHEA": utils.do_safe_query(get_data_source_id, "rhea"),
    "seed.compound": utils.do_safe_query(get_data_source_id, "seed.compound"),
    "seed.reaction": utils.do_safe_query(get_data_source_id, "seed.reaction"),
    "kegg.compound": utils.do_safe_query(get_data_source_id, "kegg.compound"),
    "kegg.reaction": utils.do_safe_query(get_data_source_id, "kegg.reaction"),
    "metacyc.compound": utils.do_safe_query(get_data_source_id, "metacyc.compound"),
    "metacyc.reaction": utils.do_safe_query(get_data_source_id, "metacyc.reaction"),
    "metanetx.chemical": utils.do_safe_query(get_data_source_id, "metanetx.chemical"),
    "metanetx.reaction": utils.do_safe_query(get_data_source_id, "metanetx.reaction"),
}


class UniversalMetaboliteSearchHandler(utils.DataHandler):
    title = "Universal Metabolites"
    search_query: str = ""
    column_specs = [
        utils.DataColumnSpec(
            UniversalComponent.bigg_id,
            "BiGG ID",
            hyperlink="/universal/metabolites/${row['universalcomponent__bigg_id']}",
        ),
        utils.DataColumnSpec(
            Component.name,
            "Names",
            agg_func=agg_strings,
            # process=process_string_array,
            requires=[UniversalComponent.components],
        ),
        utils.DataColumnSpec(
            ComponentIDMapping.old_bigg_id,
            "Old BiGG IDs",
            agg_func=agg_strings,
            requires=[UniversalComponent.old_bigg_ids],
        ),
        utils.DataColumnSpec(
            AnnotationProperty.value_str,
            "Synonyms",
            agg_func=agg_strings,
            # process=process_string_array,
            requires=[
                UniversalComponent.components,
                Component.annotation_mappings,
                ComponentAnnotationMapping.annotation,
                Annotation.properties.and_(AnnotationProperty.key == "name"),
            ],
        ),
    ]

    def pre_filter(self, query):
        return query.filter(UniversalComponent.collection_id == None)

    def post_filter(self, query):
        return query.group_by(UniversalComponent.bigg_id)

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class MetaboliteReferenceSearchHandler(utils.DataHandler):
    title = "Metabolites via Reference"
    search_query: str = ""
    column_specs = [
        utils.DataColumnSpec(
            Component.bigg_id,
            "BiGG ID",
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            Component.name,
            "Name",
            agg_func=agg_strings,
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            UniversalComponent.bigg_id,
            "Universal BiGG ID",
            agg_func=agg_strings,
            requires=[Component.universal_component],
            hyperlink="/universal/metabolites/${row['universalcomponent__bigg_id']}",
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            ReferenceCompound.bigg_id,
            "Reference Compound",
            agg_func=agg_strings,
            requires=[
                Component.reference_mappings,
                ComponentReferenceMapping.reference_compound,
            ],
            search_query_exact_match=True,
        ),
    ]

    def pre_filter(self, query):
        return query.filter(Component.collection_id == None)

    def post_filter(self, query):
        return query.group_by(Component.bigg_id)

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class MetaboliteAnnotationSearchHandler(utils.DataHandler):
    title = "Metabolites via Annotation"
    search_query: str = ""
    data_source: str = ""
    column_specs = [
        utils.DataColumnSpec(
            Component.bigg_id,
            "BiGG ID",
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            Component.name,
            "Name",
            agg_func=agg_strings,
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            UniversalComponent.bigg_id,
            "Universal BiGG ID",
            agg_func=agg_strings,
            requires=[Component.universal_component],
            hyperlink="/universal/metabolites/${row['universalcomponent__bigg_id']}",
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            AnnotationLink.identifier,
            "Annotation",
            agg_func=agg_strings,
            requires=[
                Component.annotation_mappings,
                ComponentAnnotationMapping.annotation,
                Annotation.links,
            ],
            search_query_exact_match=True,
        ),
    ]

    def pre_filter(self, query):
        return query.filter(Component.collection_id == None).filter(
            AnnotationLink.data_source_id == DATA_SOURCE_IDS[self.data_source]
        )

    def post_filter(self, query):
        return query.group_by(Component.bigg_id)

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class UniversalReactionSearchHandler(utils.DataHandler):
    title = "Universal Reactions"
    search_query: str = ""
    column_specs = [
        utils.DataColumnSpec(
            UniversalReaction.bigg_id,
            "BiGG ID",
            hyperlink="/universal/reactions/${row['universalreaction__bigg_id']}",
        ),
        utils.DataColumnSpec(
            UniversalReaction.name,
            "Name",
        ),
        utils.DataColumnSpec(
            AnnotationProperty.value_str,
            "Synonyms",
            agg_func=agg_strings,
            # process=process_string_array,
            requires=[
                UniversalReaction.reactions,
                Reaction.annotation_mappings,
                ReactionAnnotationMapping.annotation,
                Annotation.properties.and_(AnnotationProperty.key == "name"),
            ],
        ),
    ]

    def pre_filter(self, query):
        return query.filter(UniversalReaction.collection_id == None)

    def post_filter(self, query):
        return query.group_by(UniversalReaction.bigg_id, UniversalReaction.name)

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class UniversalReactionReferenceSearchHandler(utils.DataHandler):
    title = "Reactions via Reference"
    search_query: str = ""
    column_specs = [
        utils.DataColumnSpec(
            UniversalReaction.bigg_id,
            "BiGG ID",
            hyperlink="/universal/reactions/${row['universalreaction__bigg_id']}",
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            UniversalReaction.name,
            "Name",
            agg_func=agg_strings,
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            ReferenceReaction.bigg_id,
            "Reference",
            agg_func=agg_strings,
            requires=[UniversalReaction.reference],
            search_query_exact_match=True,
        ),
        utils.DataColumnSpec(
            ("RHEA:" + AnnotationLink.identifier),
            "Alternative Reference IDs",
            agg_func=agg_strings,
            requires=[
                UniversalReaction.reference,
                ReferenceReaction.annotation_mappings,
                ReferenceReactionAnnotationMapping.annotation,
                Annotation.links,
            ],
            search_query_exact_match=True,
            search_query_remove_namespace=True,
        ),
    ]

    def pre_filter(self, query):
        return query.filter(UniversalReaction.collection_id == None)

    def post_filter(self, query):
        return query.group_by(UniversalReaction.bigg_id)

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class UniversalReactionAnnotationSearchHandler(utils.DataHandler):
    title = "Reactions via Annotation"
    search_query: str = ""
    data_source: str = ""
    column_specs = [
        utils.DataColumnSpec(
            UniversalReaction.bigg_id,
            "BiGG ID",
            hyperlink="/universal/reactions/${row['universalreaction__bigg_id']}",
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            UniversalReaction.name,
            "Name",
            agg_func=agg_strings,
            apply_search_query=False,
        ),
        utils.DataColumnSpec(
            AnnotationLink.identifier,
            "Annotation",
            agg_func=agg_strings,
            requires=[
                UniversalReaction.reactions,
                Reaction.annotation_mappings,
                ReactionAnnotationMapping.annotation,
                Annotation.links,
            ],
            search_query_exact_match=True,
        ),
    ]

    def pre_filter(self, query):
        return query.filter(UniversalReaction.collection_id == None).filter(
            AnnotationLink.data_source_id == DATA_SOURCE_IDS[self.data_source]
        )

    def post_filter(self, query):
        return query.group_by(UniversalReaction.bigg_id)

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class ModelSearchHandler(utils.DataHandler):
    title = "Models"
    search_query: str = ""
    column_specs = [
        utils.DataColumnSpec(
            Model.bigg_id,
            "BiGG ID",
            hyperlink="/models/${row['model__bigg_id']}",
        ),
        utils.DataColumnSpec(
            Model.organism,
            "Organism",
        ),
        utils.DataColumnSpec(
            ModelCollection.bigg_id,
            "Collection",
            requires=[Model.collection],
        ),
        utils.DataColumnSpec(
            ModelCollection.description,
            "Collection Description",
            requires=[Model.collection],
        ),
    ]

    def post_filter(self, query):
        query = query.group_by(
            Model.bigg_id,
            Model.organism,
            ModelCollection.bigg_id,
            ModelCollection.description,
        )
        return query

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class SearchResultsHandler(utils.BaseHandler):
    template = utils.env.get_template("search_results.html")

    def clean_search_query(self, search_query):
        return "".join(x for x in search_query.strip() if x in ALLOWED_SEARCH_ALPHABET)

    def build_special_tab_page(self, search_query):
        if ":" in search_query:
            namespace, identifier = search_query.split(":", maxsplit=1)
        else:
            if search_query.startswith("cpd"):
                namespace = "seed.compound"
                identifier = search_query
            elif search_query.startswith("rxn"):
                namespace = "seed.reaction"
                identifier = search_query

            elif search_query.startswith("MNX"):
                namespace = "metanetx"
                identifier = search_query
            else:
                namespace = "BIGG"
                identifier = search_query
        namespace = namespace.upper()

        if namespace == "SEED":
            if identifier.startswith("cpd"):
                namespace = "SEED.COMPOUND"
            else:
                namespace = "SEED.REACTION"

        if namespace == "KEGG":
            if identifier.startswith("C"):
                namespace = "KEGG.COMPOUND"
            else:
                namespace = "KEGG.REACTION"

        if namespace == "METANETX":
            if identifier.startswith("MNXM"):
                namespace = "METANETX.CHEMICAL"
            else:
                namespace = "METANETX.REACTION"

        if namespace == "METACYC":
            if identifier.startswith("RXN-") or identifier.endswith("-RXN"):
                namespace = "METACYC.REACTION"
            else:
                namespace = "METACYC.COMPOUND"

        if namespace == "CHEBI":
            return {
                "id": "special_page",
                "title": "Reference",
                "data_url": f"/api/v3/search/metabolites_ref/{namespace}:{identifier}",
                "row_icon": "molecule_S",
                "columns": MetaboliteReferenceSearchHandler.column_specs,
                "message": "Interpreted search query as a reference metabolite entry.",
            }
        elif namespace == "RHEA":
            return {
                "id": "special_page",
                "title": "Reference",
                "data_url": f"/api/v3/search/reactions_ref/{namespace}:{identifier}",
                "row_icon": "reaction_S",
                "columns": UniversalReactionReferenceSearchHandler.column_specs,
                "message": "Interpreted search query as a reference reaction entry.",
            }
        elif namespace == "SEED.COMPOUND":
            return {
                "id": "special_page",
                "title": "SEED",
                "data_url": f"/api/v3/search/metabolites_ann/seed.compound/{identifier}",
                "row_icon": "molecule_S",
                "columns": MetaboliteAnnotationSearchHandler.column_specs,
                "message": "Interpreted search query as a ModelSEED metabolite entry.",
            }
        elif namespace == "SEED.REACTION":
            return {
                "id": "special_page",
                "title": "SEED",
                "data_url": f"/api/v3/search/reactions_ann/seed.reaction/{identifier}",
                "row_icon": "reaction_S",
                "columns": UniversalReactionAnnotationSearchHandler.column_specs,
                "message": "Interpreted search query as a ModelSEED reaction entry.",
            }

        elif namespace == "KEGG.COMPOUND":
            return {
                "id": "special_page",
                "title": "KEGG",
                "data_url": f"/api/v3/search/metabolites_ann/kegg.compound/{identifier}",
                "row_icon": "molecule_S",
                "columns": MetaboliteAnnotationSearchHandler.column_specs,
                "message": "Interpreted search query as a KEGG metabolite entry.",
            }
        elif namespace == "KEGG.REACTION":
            return {
                "id": "special_page",
                "title": "KEGG",
                "data_url": f"/api/v3/search/reactions_ann/kegg.reaction/{identifier}",
                "row_icon": "reaction_S",
                "columns": UniversalReactionAnnotationSearchHandler.column_specs,
                "message": "Interpreted search query as a KEGG reaction entry.",
            }

        elif namespace == "METANETX.CHEMICAL":
            return {
                "id": "special_page",
                "title": "MetaNetX",
                "data_url": f"/api/v3/search/metabolites_ann/metanetx.chemical/{identifier}",
                "row_icon": "molecule_S",
                "columns": MetaboliteAnnotationSearchHandler.column_specs,
                "message": "Interpreted search query as a MetaNetX metabolite entry.",
            }
        elif namespace == "METANETX.REACTION":
            return {
                "id": "special_page",
                "title": "MetaNetX",
                "data_url": f"/api/v3/search/reactions_ann/metanetx.reaction/{identifier}",
                "row_icon": "reaction_S",
                "columns": UniversalReactionAnnotationSearchHandler.column_specs,
                "message": "Interpreted search query as a MetaNetX reaction entry.",
            }

        elif namespace == "METACYC.COMPOUND":
            return {
                "id": "special_page",
                "title": "MetaCyc",
                "data_url": f"/api/v3/search/metabolites_ann/metacyc.compound/{identifier}",
                "row_icon": "molecule_S",
                "columns": MetaboliteAnnotationSearchHandler.column_specs,
                "message": "Interpreted search query as a MetaCyc metabolite entry.",
            }
        elif namespace == "METACYC.REACTION":
            return {
                "id": "special_page",
                "title": "MetaCyc",
                "data_url": f"/api/v3/search/reactions_ann/metacyc.reaction/{identifier}",
                "row_icon": "reaction_S",
                "columns": UniversalReactionAnnotationSearchHandler.column_specs,
                "message": "Interpreted search query as a MetaCyc reaction entry.",
            }

        return None

    def get(self, search_query):
        if not search_query.strip():
            search_query = self.get_argument("search_query", "")
        search_query = self.clean_search_query(search_query)

        special_page = self.build_special_tab_page(search_query)
        special_page = [special_page] if special_page is not None else []
        data = {
            "search_query": search_query,
            "result_types": special_page
            + [
                {
                    "id": "model",
                    "title": "Models",
                    "data_url": utils.get_reverse_url(
                        self,
                        "search_models",
                        {"api": "/api/v3", "search_query": search_query},
                    ),
                    "columns": ModelSearchHandler.column_specs,
                    "row_icon": "model_S",
                },
                {
                    "id": "universal_component",
                    "title": "Metabolites",
                    "data_url": utils.get_reverse_url(
                        self,
                        "search_metabolites",
                        {"api": "/api/v3", "search_query": search_query},
                    ),
                    "columns": UniversalMetaboliteSearchHandler.column_specs,
                    "row_icon": "molecule_S",
                },
                {
                    "id": "universal_reaction",
                    "title": "Reactions",
                    "data_url": utils.get_reverse_url(
                        self,
                        "search_reactions",
                        {"api": "/api/v3", "search_query": search_query},
                    ),
                    "columns": UniversalReactionSearchHandler.column_specs,
                    "row_icon": "reaction_S",
                },
            ],
            "breadcrumbs": [("Home", "/"), ("Search", None), (search_query, None)],
        }
        self.return_result(data)
