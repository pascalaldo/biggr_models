from sqlalchemy.orm import aliased
from bigg_models.queries import utils

from cobradb.util import ref_tuple_to_str
from cobradb import settings
from cobradb.models import (
    MemoteTest,
    MemoteResult,
)

from sqlalchemy import func
from os import path

REACTION_TESTS = ["test_blocked_reactions", "test_reaction_mass_balance"]


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


def get_memote_results_for_reaction(session, model_reaction_id):
    reaction_result_alias = aliased(MemoteResult)
    general_result_alias = aliased(MemoteResult)

    result_db = (
        session.query(reaction_result_alias, general_result_alias, MemoteTest)
        .join(
            general_result_alias,
            (general_result_alias.test_id == reaction_result_alias.test_id)
            & (general_result_alias.model_id == reaction_result_alias.model_id)
            & (general_result_alias.model_reaction_id == None)
            & (general_result_alias.model_component_id == None)
            & (general_result_alias.model_gene_id == None),
        )
        .join(MemoteTest, MemoteTest.id == reaction_result_alias.test_id)
        .filter(
            (reaction_result_alias.model_reaction_id == model_reaction_id)
            & (reaction_result_alias.test_id.in_(REACTION_TESTS))
        )
        .all()
    )
    return result_db
