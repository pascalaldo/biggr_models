from bigg_models.handlers import (
    utils,
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


def get_routes():
    routes = [
        (r"/", utils.TemplateHandler, {"template_name": "index.html"}),
        #
        # Universal
        #
        (
            r"/api/%s/(?:models/)?universal/reactions/?$" % utils.api_v,
            reaction_handlers.UniversalReactionListHandler,
        ),
        (
            r"/(?:models/)?universal/reactions/?$",
            reaction_handlers.UniversalReactionListDisplayHandler,
        ),
        #
        (
            r"/(?:api/%s/)?(?:models/)?universal/reactions/([^/]+)/?$" % utils.api_v,
            reaction_handlers.UniversalReactionHandler,
        ),
        #
        (
            r"/api/%s/(?:models/)?universal/metabolites/?$" % utils.api_v,
            metabolite_handlers.UniversalMetaboliteListHandler,
        ),
        (
            r"/(?:models/)?universal/metabolites/?$",
            metabolite_handlers.UniversalMetaboliteListDisplayHandler,
        ),
        #
        (
            r"/(?:api/%s/)?(?:models/)?universal/metabolites/([^/]+)/?$" % utils.api_v,
            metabolite_handlers.UniversalMetaboliteHandler,
        ),
        #
        (
            r"/(?:api/%s/)?compartments/?$" % utils.api_v,
            compartment_handlers.CompartmentListHandler,
        ),
        #
        (
            r"/(?:api/%s/)?compartments/([^/]+)/?$" % utils.api_v,
            compartment_handlers.CompartmentHandler,
        ),
        #
        (r"/api/%s/genomes/?$" % utils.api_v, genome_handlers.GenomeListHandler),
        (r"/genomes/?$", genome_handlers.GenomeListDisplayHandler),
        #
        (
            r"/(?:api/%s/)?genomes/([^/]+)/?$" % utils.api_v,
            genome_handlers.GenomeHandler,
        ),
        #
        # By model
        #
        (r"/api/%s/models/?$" % utils.api_v, model_handlers.ModelListHandler),
        (r"/models/?$", model_handlers.ModelsListDisplayHandler),
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
        #
        (
            r"/api/%s/models/([^/]+)/reactions/?$" % utils.api_v,
            reaction_handlers.ReactionListHandler,
        ),
        (r"/models/([^/]+)/reactions/?$", reaction_handlers.ReactionListDisplayHandler),
        #
        (
            r"/api/%s/models/([^/]+)/metabolites/?$" % utils.api_v,
            metabolite_handlers.MetaboliteListHandler,
        ),
        (
            r"/models/([^/]+)/metabolites/?$",
            metabolite_handlers.MetabolitesListDisplayHandler,
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
        (
            r"/api/%s/models/([^/]+)/genes/?$" % utils.api_v,
            gene_handlers.GeneListHandler,
        ),
        (r"/models/([^/]+)/genes/?$", gene_handlers.GeneListDisplayHandler),
        #
        # Search
        (r"/api/%s/search$" % utils.api_v, search_handlers.SearchHandler),
        (
            r"/api/%s/search_reaction_with_stoichiometry$" % utils.api_v,
            reaction_handlers.ReactionWithStoichHandler,
        ),
        (r"/search$", search_handlers.SearchDisplayHandler),
        (r"/advanced_search$", search_handlers.AdvancedSearchHandler),
        (
            r"/advanced_search_external_id_results$",
            search_handlers.AdvancedSearchExternalIDHandler,
        ),
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
            r"/static/(.*)$",
            utils.StaticFileHandlerWithEncoding,
            {"path": path.join(utils.directory, "static")},
        ),
        #
        # redirects
        (
            r"/multiecoli/?$",
            RedirectHandler,
            {"url": "http://bigg1.ucsd.edu/multiecoli"},
        ),
        (
            r"/interop-query/query-by-gene/?$", 
            db_interop_handlers.QueryByGeneHandler
        ),
        (
            r"/interop-query/query-by-strain/?$", 
            db_interop_handlers.QueryByStrainHandler
        ),
        (  
            r"/interop-query/query-by-pair/?$", 
            db_interop_handlers.QueryByPairHandler
        ),
        (
            r"/interop-query/strains/?$", 
            db_interop_handlers.StrainListHandler
        ),
        (
            r"/interop-query/genes/?$", 
            db_interop_handlers.GeneListHandler
        ),
    ]
    return routes
