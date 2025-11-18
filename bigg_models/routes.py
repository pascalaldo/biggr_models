from typing import Any, Dict, Optional, Type
from tornado.routing import URLSpec
from tornado.web import RequestHandler
from bigg_models.handlers import (
    advanced_search_handlers,
    identifiers_handlers,
    escher_handlers,
    utils,
    object_handlers,
    reaction_handlers,
    compartment_handlers,
    gene_handlers,
    genome_handlers,
    metabolite_handlers,
    model_handlers,
    search_handlers,
    db_interop_handlers,
)
from os import path
from tornado.web import RedirectHandler


def url(
    pattern: str,
    handler: Type[RequestHandler],
    kwargs: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
) -> URLSpec:
    if name is None:
        return URLSpec(pattern, handler, kwargs)
    if kwargs is None:
        opts = {"name": name}
    else:
        opts = kwargs
        opts["name"] = name
    return URLSpec(pattern, handler, opts, name=name)


def get_routes():
    api_regex = r"(?P<api>/api/%s)?" % utils.api_v
    routes = [
        (r"/", utils.TemplateHandler, {"template_name": "index.html"}),
        (
            r"/api/%s/objects/?$" % utils.api_v,
            object_handlers.ObjectHandler,
        ),
        (
            r"/api/%s/identifiers/?$" % utils.api_v,
            identifiers_handlers.IdentifiersHandler,
        ),
        url(
            api_regex + r"/universal/reactions/?$",
            reaction_handlers.UniversalReactionListViewHandler,
            name="reactions",
        ),
        #
        (
            r"/(?:api/%s/)?(?:models/)?universal/reactions/([^/]+)/?$" % utils.api_v,
            reaction_handlers.UniversalReactionHandler,
        ),
        url(
            api_regex + r"/universal/metabolites/?$",
            metabolite_handlers.UniversalMetaboliteListViewHandler,
            name="metabolites",
        ),
        #
        (
            r"/(?:api/%s/)?(?:models/)?universal/metabolites/([^/]+)/?$" % utils.api_v,
            metabolite_handlers.UniversalMetaboliteHandler,
        ),
        #
        url(
            api_regex + r"/compartments/?$",
            compartment_handlers.CompartmentListViewHandler,
            name="compartments",
        ),
        #
        (
            r"/(?:api/%s/)?compartments/([^/]+)/?$" % utils.api_v,
            compartment_handlers.CompartmentHandler,
        ),
        #
        url(
            api_regex + r"/genomes/?$",
            genome_handlers.GenomeListViewHandler,
            name="genomes",
        ),
        #
        (
            r"/(?:api/%s/)?genomes/([^/]+)/?$" % utils.api_v,
            genome_handlers.GenomeHandler,
        ),
        url(
            r"/collections/?$",
            model_handlers.ModelCollectionsTreeViewHandler,
        ),
        url(
            api_regex + r"/collections/(?P<collection_bigg_id>[^/]+)/?$",
            model_handlers.ModelCollectionHandler,
            name="model_collection",
        ),
        #
        # By model
        #
        url(
            api_regex + r"/models/?$",
            model_handlers.ModelsListViewHandler,
            name="models",
        ),
        #
        (r"/(?:api/%s/)?models/([^/]+)/?$" % utils.api_v, model_handlers.ModelHandler),
        #
        (
            r"/(?:api/%s/)?models/([^/]+)/download/?$" % utils.api_v,
            model_handlers.ModelDownloadHandler,
        ),
        #
        (
            r"/(?:api/%s/)?models/([^/]+)/reactions/([^/]+)/?$" % utils.api_v,
            reaction_handlers.ReactionHandler,
        ),
        url(
            api_regex + r"/models/(?P<model_bigg_id>[^/]+)/reactions/?$",
            reaction_handlers.ReactionListViewHandler,
            name="model_reactions",
        ),
        url(
            api_regex + r"/models/(?P<model_bigg_id>[^/]+)/metabolites/?$",
            metabolite_handlers.MetaboliteListViewHandler,
            name="model_metabolites",
        ),
        url(
            api_regex + r"/models/(?P<model_bigg_id>[^/]+)/genes/?$",
            gene_handlers.GeneListViewHandler,
            name="model_genes",
        ),
        url(
            api_regex
            + r"/models/(?P<model_bigg_id>[^/]+)/escher/(?P<map_bigg_id>[^/]+)/?$",
            escher_handlers.EscherHandler,
            name="escher_maps",
        ),
        #
        (
            r"/(?:api/%s/)?models/([^/]+)/metabolites/([^/]+)/?$" % utils.api_v,
            metabolite_handlers.MetaboliteHandler,
        ),
        #
        (
            r"/(?:api/%s/)?models/([^/]+)/genes/([^/]+)/?$" % utils.api_v,
            gene_handlers.GeneHandler,
        ),
        #
        # Search
        (
            r"/search/(?P<search_query>.*)$",
            advanced_search_handlers.SearchResultsHandler,
        ),
        url(
            api_regex + r"/search/metabolites/(?P<search_query>.*)$",
            advanced_search_handlers.UniversalMetaboliteSearchHandler,
            name="search_metabolites",
        ),
        url(
            api_regex + r"/search/reactions/(?P<search_query>.*)$",
            advanced_search_handlers.UniversalReactionSearchHandler,
            name="search_reactions",
        ),
        (r"/api/%s/search$" % utils.api_v, search_handlers.SearchHandler),
        (
            r"/api/%s/search_reaction_with_stoichiometry$" % utils.api_v,
            reaction_handlers.ReactionWithStoichHandler,
        ),
        (r"/search$", search_handlers.SearchDisplayHandler),
        (r"/advanced_search$", search_handlers.AdvancedSearchHandler),
        # (
        #     r"/advanced_search_external_id_results$",
        #     search_handlers.AdvancedSearchExternalIDHandler,
        # ),
        (r"/advanced_search_results$", search_handlers.AdvancedSearchResultsHandler),
        (r"/advanced_search_sequences$", search_handlers.AdvancedSearchSequences),
        (r"/autocomplete$", utils.AutocompleteHandler),
        #
        # Maps
        (r"/escher_map_json/([^/]+)$", utils.EscherMapJSONHandler),
        #
        # Pages
        (r"/web_api$", RedirectHandler, {"url": "/data_access"}),
        (r"/data_access$", utils.WebAPIHandler),
        (
            r"/license$",
            utils.TemplateHandler,
            {"template_name": "about_license_page.html"},
        ),
        (
            r"/about$",
            utils.TemplateHandler,
            {"template_name": "about_license_page.html"},
        ),
        (r"/updates$", utils.TemplateHandler, {"template_name": "updates.html"}),
        #
        # Version
        (r"/api/%s/database_version$" % utils.api_v, utils.APIVersionHandler),
        #
        # Static/Download
        (
            r"/(favicon.ico)$",
            utils.StaticFileHandlerWithEncoding,
            {"path": path.join(utils.directory, "static", "assets", "favicon")},
        ),
        (
            r"/static/(.*)$",
            utils.StaticFileHandlerWithEncoding,
            {"path": path.join(utils.directory, "static")},
        ),
        (r"/interop-query/query-by-gene/?$", db_interop_handlers.QueryByGeneHandler),
        (
            r"/interop-query/query-by-strain/?$",
            db_interop_handlers.QueryByStrainHandler,
        ),
        (r"/interop-query/query-by-pair/?$", db_interop_handlers.QueryByPairHandler),
        (r"/interop-query/strains/?$", db_interop_handlers.StrainListHandler),
        (r"/interop-query/genes/?$", db_interop_handlers.GeneListHandler),
    ]
    return routes
