from json import JSONDecodeError
import tornado
from tornado.web import HTTPError

from biggr_models.handlers.object_handlers import (
    determine_query_signature,
    REQUEST_PARAMETER_TYPES,
)
from biggr_models.queries import metabolite_queries
from biggr_models.handlers import utils

MODELS_CLASS_MAP = {
    "METABOLITE": metabolite_queries.get_any_components_by_identifiers,
}
MODELS_MAP = MODELS_CLASS_MAP

MODELS_SIGNATURE = {k: determine_query_signature(v) for k, v in MODELS_MAP.items()}


class IdentifiersHandler(utils.BaseHandler):
    def post(self):
        try:
            data = tornado.escape.json_decode(self.request.body)
        except JSONDecodeError:
            raise HTTPError(status_code=400, reason="Invalid JSON request.")
        obj_type = data.get("type")
        if not obj_type:
            raise HTTPError(
                status_code=400,
                reason="object type not valid",
            )
        obj_type = str(obj_type).upper().replace("_", "")
        if not obj_type in MODELS_SIGNATURE:
            raise HTTPError(
                status_code=400,
                reason="object type not valid",
            )

        f_sign = MODELS_SIGNATURE[obj_type]

        args = []
        for arg_name, arg_type in f_sign["args"]:
            if arg_name not in data:
                raise HTTPError(
                    status_code=400,
                    reason=f"Not a valid request, parameter {arg_name} required.",
                )
            try:
                val = REQUEST_PARAMETER_TYPES[arg_type](data[arg_name])
            except:
                raise HTTPError(
                    status_code=400,
                    reason=f"Could not convert parameter {arg_name} to type {arg_type}.",
                )
            args.append(val)
        kwargs = {}
        for kwarg_name, kwarg_type in f_sign["kwargs"]:
            if kwarg_name not in data:
                continue
            try:
                val = REQUEST_PARAMETER_TYPES[kwarg_type](data[kwarg_name])
            except:
                raise HTTPError(
                    status_code=400,
                    reason=f"Could not convert parameter {kwarg_name} to type {kwarg_type}.",
                )
            kwargs[kwarg_name] = val

        result = utils.do_safe_query(MODELS_MAP[obj_type], *args, **kwargs)
        self.return_result(result)
