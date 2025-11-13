from datetime import datetime
from operator import itemgetter
import re
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    TypeVar,
    Union,
)
from cobradb.models import Base, Session, MemoteResult, MemoteTest
from sqlalchemy import Row, and_, or_
from bigg_models import __api_version__ as api_v
from bigg_models.queries import search_queries, escher_map_queries, utils as query_utils
import json
from tornado.web import (
    RequestHandler,
    StaticFileHandler,
    HTTPError,
)

from jinja2 import Environment, PackageLoader
from os import path
import mimetypes
from pprint import pprint


MODELS_CLASS_MAP = {x.__name__: x for x in Base.__subclasses__()}


class BiGGrJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if o is None:
            return None
        if isinstance(o, Row):
            return o._tuple()
        if isinstance(o, (MemoteTest, MemoteResult)):
            print(vars(o))
            print(dir(o))
            print(o._to_shallow_dict())
            return o._to_shallow_dict()
        if isinstance(o, Base):
            return o._to_shallow_dict()
        if isinstance(o, datetime):
            return {"_type": "datetime", "iso": o.isoformat()}
        # Let the base class default method raise the TypeError
        return super().default(o)


def biggr_json_object_hook(o):
    if o is None:
        return None
    if not isinstance(o, dict):
        return o
    if "_type" not in o:
        return o
    if o["_type"] == "datetime":
        if isoformat := o.get("iso"):
            return datetime.fromisoformat(isoformat)
        else:
            return None
    if o["_type"] in MODELS_CLASS_MAP:
        model_class = MODELS_CLASS_MAP[o["_type"]]
        return model_class._from_dict(o)

    return None


def format_bigg_id(bigg_id, format_type=None):
    if format_type is None:
        return bigg_id
    try:
        prefix = ""
        if bigg_id.startswith("__"):
            if "__" in bigg_id[2:]:
                model_id, bigg_id = bigg_id[2:].split("__", maxsplit=1)
                prefix = (
                    f"<span class='small opacity-75 fw-lighter'>__{model_id}__</span>"
                )
        if format_type == "comp_comp":
            comp_id, charge = bigg_id.rsplit(":", maxsplit=1)
            universal_id, compartment_id = comp_id.rsplit("_", maxsplit=1)
            return f'{prefix}<span class="fw-semibold">{universal_id}</span><span class="fw-normal opacity-75">_{compartment_id}</span><span class="fw-normal fst-italic opacity-75 small">:{charge}</span>'
        elif format_type == "comp":
            universal_id, charge = bigg_id.rsplit(":", maxsplit=1)
            return f'{prefix}<span class="fw-semibold">{universal_id}</span><span class="fw-normal fst-italic opacity-75 small">:{charge}</span>'
        elif format_type == "universal_comp_comp":
            universal_id, compartment_id = bigg_id.rsplit("_", maxsplit=1)
            return f'{prefix}<span class="fw-semibold">{universal_id}</span><span class="fw-normal opacity-75">_{compartment_id}</span>'
        elif format_type == "reaction":
            if ":" in bigg_id:
                universal_id, copy_number = bigg_id.rsplit(":", maxsplit=1)
                return f'{prefix}<span class="fw-semibold">{universal_id}</span><span class="fw-normal fst-italic opacity-75 small">:{copy_number}</span>'
            return f'{prefix}<span class="fw-semibold">{bigg_id}</span>'
        else:
            return bigg_id
    except:
        return bigg_id


def format_reference(identifier):
    namespace, ref_id = identifier.rsplit(":", maxsplit=1)
    return f'<span class="fw-normal text-body-secondary">{namespace}:</span><span class="text-body-emphasis">{ref_id}</span>'


def format_gene_reaction_rule(grr):
    s = grr.replace("(", " ( ").replace(")", " ) ")
    s = [xs for x in s.split(" ") if (xs := x.strip()) != ""]
    s = [
        (
            x
            if x in [")", "(", "or", "and", "OR", "AND"]
            else f"<span class='fw-semibold'>{x}</span>"
        )
        for x in s
    ]
    res = " "
    for x in s:
        if x == ")" or res[-1] in " (":
            res = f"{res}{x}"
        else:
            res = f"{res} {x}"

    return res.strip()


# set up jinja2 template location
env = Environment(loader=PackageLoader("bigg_models", "templates"))
env.filters["format_reference"] = lambda x: format_reference(x)
env.filters["format_id"] = format_bigg_id
env.filters["format_gene_reaction_rule"] = format_gene_reaction_rule
env.filters["int_or_float"] = lambda x: int(x) if x.is_integer() else x

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


def do_safe_query(func, *args, **kwargs):
    """Run the given function, and raise a 404 if it fails.

    Arguments
    ---------

    func: The function to run. *args and **kwargs are passed to this function.

    """
    session = Session()
    try:
        return func(session, *args, **kwargs)
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
        if isinstance(chunk, (dict, list, tuple, Base)):
            try:
                value_str = json.dumps(chunk, cls=BiGGrJSONEncoder)
            except Exception as e:
                pprint(chunk)
                print(e)
            # value_str = json.dumps(chunk)
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
                if "breadcrumbs" in result:
                    del result["breadcrumbs"]

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


def _interpret_bool(input: str) -> bool:
    return input.upper() == "TRUE"


def _interpret_asc(input: str) -> bool:
    return input.upper() == "ASC"


def col_str_search(query, col_spec: "DataColumnSpec"):
    if (search_value := col_spec.search_value.strip()) == "":
        return False, query
    return True, query.filter(col_spec.prop.contains(search_value, autoescape=True))


def col_bool_search(query, col_spec: "DataColumnSpec"):
    if (search_value := col_spec.search_value.strip()) == "":
        return False, query
    value_as_bool = search_value.upper() == "TRUE"
    return True, query.filter(col_spec.prop == value_as_bool)


REGEX_COL_NUMBER_1 = re.compile(r"^((?P<eq>[\>\<]\=?) *)?(?P<nr>\d+(\.\d+)?)$")
REGEX_COL_NUMBER_2 = re.compile(r"^(?P<nr1>\d+(\.\d+)?) *\- *(?P<nr2>\d+(\.\d+)?)$")


def col_number_search(query, col_spec):
    if (search_value := col_spec.search_value.strip()) == "":
        return False, query

    or_filters = []
    for or_part in search_value.split(","):
        and_filters = []
        for and_part in or_part.split("&"):
            part = and_part.strip()
            m = REGEX_COL_NUMBER_1.match(part)
            if m is not None:
                print("Match 1")
                print(m.groups())
                number = float(m.group("nr"))
                try:
                    comp = m.group("eq")
                except IndexError:
                    comp = None
                if comp is None:
                    and_filters.append(col_spec.prop == number)
                else:
                    if comp == ">":
                        and_filters.append(col_spec.prop > number)
                    elif comp == ">=":
                        and_filters.append(col_spec.prop >= number)
                    elif comp == "<":
                        and_filters.append(col_spec.prop < number)
                    elif comp == "<=":
                        and_filters.append(col_spec.prop <= number)
                    else:
                        print(f"Fail 1: {comp}")
                        continue
                continue
            m = REGEX_COL_NUMBER_2.match(part)
            if m is not None:
                print("Match 2")
                number1 = float(m.group("nr1"))
                number2 = float(m.group("nr2"))
                and_filters.append(col_spec.prop >= number1)
                and_filters.append(col_spec.prop <= number2)
        if len(and_filters) == 1:
            or_filters.append(and_filters[0])
        elif len(and_filters) > 1:
            or_filters.append(and_(*and_filters))

    if len(or_filters) == 0:
        return False, query
    elif len(or_filters) == 1:
        return True, query.filter(or_filters[0])
    else:
        return True, query.filter(or_(*or_filters))


class DataColumnSpec:
    def __init__(
        self,
        prop: Any,
        name: str,
        requires=None,
        global_search: bool = True,
        hyperlink: Optional[str] = None,
        search_type: str = "str",
    ):
        self.prop = prop
        self.identifier: str = str(prop).lower().replace(".", "__")
        self.name: str = name
        self.global_search = global_search
        self.requires: List[Any] = []
        if isinstance(requires, Iterable):
            self.requires.extend(requires)
        elif requires is not None:
            self.requires.append(requires)

        self.searchable: bool = True
        self.orderable: bool = True
        self.search_value: str = ""
        self.search_regex: bool = False
        self.search_type = search_type
        self.order_priority: Optional[int] = None
        self.order_asc: bool = True
        self.hyperlink = hyperlink

    def search(self, query):
        if self.search_value != "":
            print(f"{self.identifier}: '{self.search_value}' ({self.search_type})")
        if self.search_type == "str":
            return col_str_search(query, self)
        if self.search_type == "number":
            return col_number_search(query, self)
        if self.search_type == "bool":
            return col_bool_search(query, self)
        return False, query


_TT = TypeVar("_TT")
_TD = TypeVar("_TD")


class DataHandler(BaseHandler):
    template = env.get_template("data_table.html")
    title = None
    columns: List[DataColumnSpec] = []
    start: int = 0
    length: Optional[int] = None
    draw: Optional[int] = None
    name = None
    search_value: str = ""
    search_regex: bool = False
    api: bool = False
    page_data: Optional[Dict[str, Any]] = None

    def initialize(self, **kwargs):
        self.name = kwargs.get("name")

    def breadcrumbs(self) -> Any:
        return None

    def pre_filter(self, query):
        return query

    def get(self, *args, **kwargs):
        if self.api:
            return self.return_data(*args, **kwargs)
        return self.return_page(*args, **kwargs)

    def return_page(self, *args, **kwargs):
        data = dict(
            data_url=self.data_url,
            columns=self.columns,
        )

        if self.page_data:
            data = data | self.page_data

        brcrmb = self.breadcrumbs()
        if brcrmb is not None:
            data["breadcrumbs"] = brcrmb

        if self.title is not None:
            data["title"] = self.title
        self.write(self.template.render(data))
        self.finish()

    def post(self, *args, **kwargs):
        return self.return_data(*args, **kwargs)

    def return_data(self, *args, **kwargs):
        data, total, filtered = self.data_query(query_utils.get_list)
        self.write_data(data, total, filtered)

    @property
    def data_url(self):
        if self.name is None:
            raise HTTPError(status_code=500, reason="Internal error, unnamed route.")
        # Resolve named groups, this is a bit of a workaround, since
        # reverse_url does not support named groups.
        args = [
            (v, self.path_kwargs.get(k))
            for k, v in self.application.wildcard_router.named_rules[
                self.name
            ].matcher.regex.groupindex.items()
        ]
        args = [
            "" if x is None else x
            for x in map(itemgetter(1), sorted(args, key=itemgetter(0)))
        ]
        return self.reverse_url(self.name, *args)

    def _get_argument_of_type_or_default(
        self, arg_name: str, arg_type: Callable[[Any], _TT], default: _TD = None
    ) -> Union[_TT, _TD]:
        arg_val = self.get_argument(arg_name, None)
        if arg_val is None:
            return default
        try:
            arg_val = arg_type(arg_val)
        except:
            return default
        return arg_val

    def _parse_data_tables_args(self):
        self.draw = self._get_argument_of_type_or_default("draw", int, None)
        self.start = self._get_argument_of_type_or_default("start", int, 0)
        self.length = self._get_argument_of_type_or_default("length", int, None)

        self.search_value = self._get_argument_of_type_or_default(
            "search[value]", str, ""
        )
        self.search_regex = self._get_argument_of_type_or_default(
            "search[regex]", _interpret_bool, False
        )

        for col_spec in self.columns:
            col_spec.order_priority = None
            col_spec.search_value = ""
        i = 0
        while (
            col_identifier := self.get_argument(f"columns[{i}][data]", None)
        ) is not None:
            if col_identifier == "x":
                i += 1
                continue
            try:
                col_spec = next(
                    x for x in self.columns if x.identifier == col_identifier
                )
            except StopIteration:
                raise HTTPError(
                    status_code=400,
                    reason="Could not parse datatables arguments.",
                )
            col_spec.searchable = self._get_argument_of_type_or_default(
                f"columns[{i}][searchable]", _interpret_bool, col_spec.searchable
            )
            col_spec.orderable = self._get_argument_of_type_or_default(
                f"columns[{i}][orderable]", _interpret_bool, col_spec.orderable
            )
            col_spec.search_value = self._get_argument_of_type_or_default(
                f"columns[{i}][search][value]", str, col_spec.search_value
            )
            col_spec.search_regex = self._get_argument_of_type_or_default(
                f"columns[{i}][search][regex]", _interpret_bool, col_spec.search_regex
            )

            i += 1

        i = 0
        while (
            col_identifier := self.get_argument(f"order[{i}][name]", None)
        ) is not None:
            if col_identifier == "x":
                i += 1
                continue
            try:
                col_spec = next(
                    x for x in self.columns if x.identifier == col_identifier
                )
            except StopIteration:
                raise HTTPError(
                    status_code=400,
                    reason="Could not parse datatables arguments.",
                )
            col_spec.order_priority = i
            col_spec.order_asc = self._get_argument_of_type_or_default(
                f"order[{i}][dir]", _interpret_asc, col_spec.order_asc
            )

            i += 1

    def prepare(self):
        for k, v in self.path_kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
        self.api = self.path_kwargs.get("api") is not None
        if self.request.method == "POST" or self.api:
            self._parse_data_tables_args()

    def data_query(self, f, **kwargs):
        opts = dict(
            column_specs=self.columns,
            start=self.start,
            length=self.length,
            search_value=self.search_value,
            search_regex=self.search_regex,
            pre_filter=self.pre_filter,
        )
        opts = opts | kwargs
        results = do_safe_query(f, **opts)
        return results

    def write_data(self, data: Any, total_count: int, filtered_count: int):
        result = {
            "recordsTotal": total_count,
            "recordsFiltered": filtered_count,
            "data": data,
        }
        if self.draw is not None:
            result["draw"] = self.draw + 1
        self.write(result)
        self.finish()


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
