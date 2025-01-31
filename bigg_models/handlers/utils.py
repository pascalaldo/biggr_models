from cobradb.models import Session
from bigg_models import __api_version__ as api_v
from bigg_models.queries import search_queries, escher_map_queries, utils as query_utils
import simplejson as json
from tornado.web import (
    RequestHandler,
    StaticFileHandler,
    HTTPError,
)

from jinja2 import Environment, PackageLoader
from os import path
import mimetypes

# set up jinja2 template location
env = Environment(loader=PackageLoader("bigg_models", "templates"))

# root directory
directory = path.abspath(path.join(path.dirname(__file__), ".."))
static_model_dir = path.join(directory, "static", "models")
static_multistrain_dir = path.join(directory, "static", "multistrain")

# host
api_host = "bigg.ucsd.edu"


def _possibly_compartmentalized_met_id(obj):
    if "compartment_bigg_id" not in obj:
        return obj["bigg_id"]
    else:
        return "{bigg_id}_{compartment_bigg_id}".format(**obj)


def _parse_col_arg(s):
    try:
        return s.split(",")
    except AttributeError:
        return None


def _get_col_name(
    query_arguments, columns, default_column=None, default_direction="ascending"
):
    for k, v in query_arguments.items():
        split = [x.strip("[]") for x in k.split("[")]
        if len(split) != 2:
            continue
        if split[0] == "col":
            sort_direction = "ascending" if v[0] == b"0" else "descending"
            sort_col_index = int(split[1])
            return columns[sort_col_index], sort_direction
    return default_column, default_direction


def safe_query(func, *args, **kwargs):
    """Run the given function, and raise a 404 if it fails.

    Arguments
    ---------

    func: The function to run. *args and **kwargs are passed to this function.

    """
    session = Session()
    kwargs["session"] = session
    try:
        return func(*args, **kwargs)
    except query_utils.NotFoundError as e:
        raise HTTPError(status_code=404, reason=e.args[0])
    except ValueError as e:
        raise HTTPError(status_code=400, reason=e.args[0])
    finally:
        session.close()


class BaseHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")

    def write(self, chunk):
        # note that serving a json list is a security risk
        # This is meant to be serving public-read only data only.
        if isinstance(chunk, (dict, list, tuple)):
            value_str = json.dumps(chunk)
            RequestHandler.write(self, value_str)
            self.set_header("Content-type", "application/json; charset=utf-8")
        else:
            RequestHandler.write(self, chunk)

    def return_result(self, result=None):
        """Returns result as either rendered HTML or JSON

        This is suitable for cases where the template takes exactly the same
        result as the JSON api. This function will serve JSON if the request
        URI starts with JSON, otherwise it will render the objects template
        with the data

        """
        if self.request.uri.startswith("/api"):
            if result:
                self.write(result)
                self.finish()
            else:
                # For redirects
                pass
        else:
            if result:
                self.write(self.template.render(result))
                self.finish()
            else:
                self.write(self.template.render())
                self.finish()

    def get(self):
        self.return_result()


class TemplateHandler(BaseHandler):
    def initialize(self, template_name):
        self.template = env.get_template(template_name)


class PageableHandler(BaseHandler):
    """HTTP requests can pass in arguments for page, size, columns, and the
    sort_column.

    TODO test this class.

    """

    def _get_pager_args(self, default_sort_column=None, sort_direction="ascending"):
        query_kwargs = {
            "page": self.get_argument("page", None),
            "size": self.get_argument("size", None),
            "multistrain_off": self.get_argument("multistrain", None) == "off",
            "sort_column": default_sort_column,
            "sort_direction": sort_direction,
        }

        # determine the columns
        column_str = self.get_argument("columns", None)
        columns = column_str.split(",") if column_str else []

        # determine which column we are sorting by
        # These are parameters formatted as col[i] = 0 (or 1 for descending)
        for param_name, param_value in self.request.query_arguments.items():
            if not (param_name.startswith("col[") and param_name.endswith("]")):
                continue
            try:
                # get the number in col[?]
                col_index = int(param_name[4:-1])
                sort_direction = "ascending" if param_value[0] == b"0" else "descending"
            except ValueError as e:
                raise HTTPError(
                    status_code=400,
                    reason="could not parse %s=%s" % (param_name, param_value),
                )
            # convert these integers into meaningful sort params
            try:
                query_kwargs["sort_column"] = columns[col_index]
            except IndexError:
                raise HTTPError(
                    status_code=400,
                    reason="column #%d not found in columns" % col_index,
                )
            else:
                query_kwargs["sort_direction"] = sort_direction

        return query_kwargs


class AutocompleteHandler(BaseHandler):
    def get(self):
        query_string = self.get_argument("query")
        result_array = safe_query(
            search_queries.search_ids_fast, query_string, limit=15
        )
        self.write(result_array)
        self.finish()


class EscherMapJSONHandler(BaseHandler):
    def get(self, map_name):
        map_json = safe_query(escher_map_queries.json_for_map, map_name)

        self.write(map_json)
        # need to do this because map_json is a string
        self.set_header("Content-type", "application/json; charset=utf-8")
        self.finish()


class WebAPIHandler(BaseHandler):
    template = env.get_template("data_access.html")

    def get(self):
        self.write(self.template.render(api_v=api_v, api_host=api_host))
        self.finish()


class APIVersionHandler(BaseHandler):
    def get(self):
        result = safe_query(query_utils.database_version)
        self.return_result(result)


# static files
class StaticFileHandlerWithEncoding(StaticFileHandler):
    # This is only to opportunisticly use a pre-compressed file
    # (equivalent to gzip_static in nginx).
    def get_absolute_path(self, root, file_path):
        p = path.abspath(path.join(root, file_path))
        # if the client accepts gzip
        if "gzip" in self.request.headers.get("Accept-Encoding", ""):
            if path.isfile(p + ".gz"):
                self.set_header("Content-Encoding", "gzip")
                return p + ".gz"
        return p

    def get_content_type(self):
        """Same as the default, except that we add a utf8 encoding for XML and JSON files."""
        mime_type, encoding = mimetypes.guess_type(self.path)

        # from https://github.com/tornadoweb/tornado/pull/1468
        # per RFC 6713, use the appropriate type for a gzip compressed file
        if encoding == "gzip":
            return "application/gzip"
        # As of 2015-07-21 there is no bzip2 encoding defined at
        # http://www.iana.org/assignments/media-types/media-types.xhtml
        # So for that (and any other encoding), use octet-stream.
        elif encoding is not None:
            return "application/octet-stream"

        # assume utf-8 for xml and json
        elif mime_type == "application/xml":
            return "application/xml; charset=utf-8"
        elif mime_type == "application/json":
            return "application/json; charset=utf-8"

        # from https://github.com/tornadoweb/tornado/pull/1468
        elif mime_type is not None:
            return mime_type
        # if mime_type not detected, use application/octet-stream
        else:
            return "application/octet-stream"
