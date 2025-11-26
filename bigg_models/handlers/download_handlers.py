from json import JSONDecodeError
from typing import List, Optional
from bigg_models.queries import download_queries
import tornado
from bigg_models.handlers import utils
from tornado.web import HTTPError


class ReactionsDownloadHandler(utils.BaseHandler):
    def get(self):
        reactions = utils.do_safe_query(download_queries.get_reactions)

        self.return_result(reactions)


class MetabolitesDownloadHandler(utils.BaseHandler):
    def get(self):
        metabolites = utils.do_safe_query(download_queries.get_metabolites)

        self.return_result(metabolites)
