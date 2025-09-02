from bigg_models.queries import utils

from cobradb.util import ref_tuple_to_str
from cobradb import settings
from cobradb.models import (
    MemoteTest,
    MemoteResult,
)

from sqlalchemy import func
from os import path


def get_general_results_for_model(session, model_bigg_id):
    result_db = (
        session.query(MemoteTest, MemoteResult)
        .join(MemoteResult, MemoteResult.test_id == MemoteTest.id)
        .filter(
            (MemoteResult.model_id == model_bigg_id)
            & (MemoteResult.model_reaction_id == None)
            & (MemoteResult.model_component_id == None)
            & (MemoteResult.model_gene_id == None)
            & (MemoteResult.result != None)
        )
        .all()
    )

    if result_db is not None:
        result_db = {r[0].id: r for r in result_db}

    return result_db
