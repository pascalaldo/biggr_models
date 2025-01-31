from bigg_models.handlers import (
    general,
    reaction,
    compartment,
    gene,
    genome,
    metabolite,
    model,
    search,
)
from os import path
from tornado.web import RedirectHandler


def get_routes():
    routes = [
        (r"/", general.TemplateHandler, {"template_name": "index.html"}),
        #
        # Universal
        #
        (
            r"/api/%s/(?:models/)?universal/reactions/?$" % general.api_v,
            reaction.UniversalReactionListHandler,
        ),
        (
            r"/(?:models/)?universal/reactions/?$",
            reaction.UniversalReactionListDisplayHandler,
        ),
        #
        (
            r"/(?:api/%s/)?(?:models/)?universal/reactions/([^/]+)/?$" % general.api_v,
            reaction.UniversalReactionHandler,
        ),
        #
        (
            r"/api/%s/(?:models/)?universal/metabolites/?$" % general.api_v,
            metabolite.UniversalMetaboliteListHandler,
        ),
        (
            r"/(?:models/)?universal/metabolites/?$",
            metabolite.UniversalMetaboliteListDisplayHandler,
        ),
        #
        (
            r"/(?:api/%s/)?(?:models/)?universal/metabolites/([^/]+)/?$"
            % general.api_v,
            metabolite.UniversalMetaboliteHandler,
        ),
        #
        (
            r"/(?:api/%s/)?compartments/?$" % general.api_v,
            compartment.CompartmentListHandler,
        ),
        #
        (
            r"/(?:api/%s/)?compartments/([^/]+)/?$" % general.api_v,
            compartment.CompartmentHandler,
        ),
        #
        (r"/api/%s/genomes/?$" % general.api_v, genome.GenomeListHandler),
        (r"/genomes/?$", genome.GenomeListDisplayHandler),
        #
        (r"/(?:api/%s/)?genomes/([^/]+)/?$" % general.api_v, genome.GenomeHandler),
        #
        # By model
        #
        (r"/api/%s/models/?$" % general.api_v, model.ModelListHandler),
        (r"/models/?$", model.ModelsListDisplayHandler),
        #
        (r"/(?:api/%s/)?models/([^/]+)/?$" % general.api_v, model.ModelHandler),
        #
        (
            r"/(?:api/%s/)?models/([^/]+)/download/?$" % general.api_v,
            model.ModelDownloadHandler,
        ),
        #
        (
            r"/(?:api/%s/)?models/([^/]+)/reactions/([^/]+)/?$" % general.api_v,
            reaction.ReactionHandler,
        ),
        #
        (
            r"/api/%s/models/([^/]+)/reactions/?$" % general.api_v,
            reaction.ReactionListHandler,
        ),
        (r"/models/([^/]+)/reactions/?$", reaction.ReactionListDisplayHandler),
        #
        (
            r"/api/%s/models/([^/]+)/metabolites/?$" % general.api_v,
            metabolite.MetaboliteListHandler,
        ),
        (r"/models/([^/]+)/metabolites/?$", metabolite.MetabolitesListDisplayHandler),
        #
        (
            r"/(?:api/%s/)?models/([^/]+)/metabolites/([^/]+)/?$" % general.api_v,
            metabolite.MetaboliteHandler,
        ),
        #
        (
            r"/(?:api/%s/)?models/([^/]+)/genes/([^/]+)/?$" % general.api_v,
            gene.GeneHandler,
        ),
        #
        (r"/api/%s/models/([^/]+)/genes/?$" % general.api_v, gene.GeneListHandler),
        (r"/models/([^/]+)/genes/?$", gene.GeneListDisplayHandler),
        #
        # Search
        (r"/api/%s/search$" % general.api_v, search.SearchHandler),
        (
            r"/api/%s/search_reaction_with_stoichiometry$" % general.api_v,
            reaction.ReactionWithStoichHandler,
        ),
        (r"/search$", search.SearchDisplayHandler),
        (r"/advanced_search$", search.AdvancedSearchHandler),
        (
            r"/advanced_search_external_id_results$",
            search.AdvancedSearchExternalIDHandler,
        ),
        (r"/advanced_search_results$", search.AdvancedSearchResultsHandler),
        (r"/advanced_search_sequences$", search.AdvancedSearchSequences),
        (r"/autocomplete$", general.AutocompleteHandler),
        #
        # Maps
        (r"/escher_map_json/([^/]+)$", general.EscherMapJSONHandler),
        #
        # Pages
        (r"/web_api$", RedirectHandler, {"url": "/data_access"}),
        (r"/data_access$", general.WebAPIHandler),
        (
            r"/license$",
            general.TemplateHandler,
            {"template_name": "about_license_page.html"},
        ),
        (
            r"/about$",
            general.TemplateHandler,
            {"template_name": "about_license_page.html"},
        ),
        (r"/updates$", general.TemplateHandler, {"template_name": "updates.html"}),
        #
        # Version
        (r"/api/%s/database_version$" % general.api_v, general.APIVersionHandler),
        #
        # Static/Download
        (
            r"/static/(.*)$",
            general.StaticFileHandlerWithEncoding,
            {"path": path.join(general.directory, "static")},
        ),
        #
        # redirects
        (
            r"/multiecoli/?$",
            RedirectHandler,
            {"url": "http://bigg1.ucsd.edu/multiecoli"},
        ),
    ]
    return routes
