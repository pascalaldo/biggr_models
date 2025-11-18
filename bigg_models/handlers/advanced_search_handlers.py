from cobradb.models import (
    Annotation,
    AnnotationProperty,
    Component,
    ComponentAnnotationMapping,
    Reaction,
    ReactionAnnotationMapping,
    UniversalComponent,
    UniversalReaction,
)
from sqlalchemy import distinct, or_
from sqlalchemy.sql.functions import aggregate_strings, array_agg
from bigg_models.handlers import utils
from bigg_models.queries import utils as query_utils

ALLOWED_SEARCH_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-()[]/:"

# agg_strings = lambda x: aggregate_strings(x, ", ")

agg_strings = lambda x: array_agg(distinct(x))
process_string_array = lambda x: ", ".join(x)

SEARCH_COLSPECS = {
    "UNIVERSAL_COMPONENT": [
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
    ],
    "UNIVERSAL_REACTION": [
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
    ],
}


class UniversalMetaboliteSearchHandler(utils.DataHandler):
    title = "Universal Metabolites"
    search_query: str = ""
    columns = SEARCH_COLSPECS["UNIVERSAL_COMPONENT"]

    def pre_filter(self, query):
        return query.filter(UniversalComponent.collection_id == None)

    def post_filter(self, query):
        return query.group_by(UniversalComponent.bigg_id)

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class UniversalReactionSearchHandler(utils.DataHandler):
    title = "Universal Reactions"
    search_query: str = ""
    columns = SEARCH_COLSPECS["UNIVERSAL_REACTION"]

    def pre_filter(self, query):
        return query.filter(UniversalReaction.collection_id == None)

    def post_filter(self, query):
        return query.group_by(UniversalReaction.bigg_id, UniversalReaction.name)

    def return_data(self, search_query, *args, **kwargs):
        data, total, filtered = self.data_query(
            query_utils.get_search_list, search_query=search_query
        )
        self.write_data(data, total, filtered)


class SearchResultsHandler(utils.BaseHandler):
    template = utils.env.get_template("search_results.html")

    def clean_search_query(self, search_query):
        return "".join(x for x in search_query.strip() if x in ALLOWED_SEARCH_ALPHABET)

    def get(self, search_query):
        if not search_query.strip():
            search_query = self.get_argument("search_query", "")
        search_query = self.clean_search_query(search_query)
        data = {
            "search_query": search_query,
            "result_types": [
                {
                    "id": "universal_component",
                    "title": "Metabolites",
                    "data_url": utils.get_reverse_url(
                        self,
                        "search_metabolites",
                        {"api": "/api/v3", "search_query": search_query},
                    ),
                    "columns": SEARCH_COLSPECS["UNIVERSAL_COMPONENT"],
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
                    "columns": SEARCH_COLSPECS["UNIVERSAL_REACTION"],
                    "row_icon": "reaction_S",
                },
            ],
            "breadcrumbs": [("Home", "/"), ("Search", None), (search_query, None)],
        }
        self.return_result(data)
