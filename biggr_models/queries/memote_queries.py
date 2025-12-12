from sqlalchemy.orm import aliased

from cobradb.models import (
    MemoteTest,
    MemoteResult,
)

from sqlalchemy import select

REACTION_TESTS = [
    "test_blocked_reactions",
    "test_reaction_mass_balance",
    "test_reaction_charge_balance",
    "test_ngam_presence",
    "test_find_reversible_oxygen_reactions",
]
METABOLITE_TESTS = [
    "test_find_disconnected",
    "test_find_orphans",
    "test_find_deadends",
    "test_metabolites_charge_presence",
    "test_metabolites_formula_presence",
    "test_unconserved_metabolites",
]
GENE_TESTS = []


def get_general_results_for_model(session, model_id):
    result_db = session.execute(
        select(MemoteTest, MemoteResult)
        .join(MemoteResult, MemoteResult.test_id == MemoteTest.id)
        .filter(
            (MemoteResult.model_id == model_id)
            & (MemoteResult.model_reaction_id == None)
            & (MemoteResult.model_compartmentalized_component_id == None)
            & (MemoteResult.model_gene_id == None)
            & (MemoteResult.result != None)
        )
    ).all()

    if result_db is not None:
        result_db = {r[0].bigg_id: tuple(r) for r in result_db}

    return result_db


def get_memote_results_for_reaction(session, model_reaction_id):
    reaction_result_alias = aliased(MemoteResult)
    general_result_alias = aliased(MemoteResult)

    result_db = session.execute(
        select(reaction_result_alias, general_result_alias, MemoteTest)
        .join(
            general_result_alias,
            (general_result_alias.test_id == reaction_result_alias.test_id)
            & (general_result_alias.model_id == reaction_result_alias.model_id)
            & (general_result_alias.model_reaction_id == None)
            & (general_result_alias.model_compartmentalized_component_id == None)
            & (general_result_alias.model_gene_id == None),
        )
        .join(MemoteTest, MemoteTest.id == reaction_result_alias.test_id)
        .filter(
            (reaction_result_alias.model_reaction_id == model_reaction_id)
            & (MemoteTest.bigg_id.in_(REACTION_TESTS))
        )
    ).all()
    return [tuple(r) for r in result_db]


def get_memote_results_for_metabolite(session, model_compartmentalized_component_id):
    metabolite_result_alias = aliased(MemoteResult)
    general_result_alias = aliased(MemoteResult)

    result_db = session.execute(
        select(metabolite_result_alias, general_result_alias, MemoteTest)
        .join(
            general_result_alias,
            (general_result_alias.test_id == metabolite_result_alias.test_id)
            & (general_result_alias.model_id == metabolite_result_alias.model_id)
            & (general_result_alias.model_reaction_id == None)
            & (general_result_alias.model_compartmentalized_component_id == None)
            & (general_result_alias.model_gene_id == None),
        )
        .join(MemoteTest, MemoteTest.id == metabolite_result_alias.test_id)
        .filter(
            (
                metabolite_result_alias.model_compartmentalized_component_id
                == model_compartmentalized_component_id
            )
            & (MemoteTest.bigg_id.in_(METABOLITE_TESTS))
        )
    ).all()
    return [tuple(r) for r in result_db]


def get_memote_results_for_gene(session, model_gene_id):
    gene_result_alias = aliased(MemoteResult)
    general_result_alias = aliased(MemoteResult)

    result_db = session.execute(
        select(gene_result_alias, general_result_alias, MemoteTest)
        .join(
            general_result_alias,
            (general_result_alias.test_id == gene_result_alias.test_id)
            & (general_result_alias.model_id == gene_result_alias.model_id)
            & (general_result_alias.model_reaction_id == None)
            & (general_result_alias.model_compartmentalized_component_id == None)
            & (general_result_alias.model_gene_id == None),
        )
        .join(MemoteTest, MemoteTest.id == gene_result_alias.test_id)
        .filter(
            (gene_result_alias.model_gene_id == model_gene_id)
            & (MemoteTest.bigg_id.in_(GENE_TESTS))
        )
    ).all()
    return [tuple(r) for r in result_db]
