from bigg_models.queries import *
from bigg_models.queries import (
    _shorten_name,
    _get_old_ids_for_model_gene,
    _get_old_ids_for_model_reaction,
    _get_old_ids_for_model_comp_metabolite,
    _get_gene_list_for_model_reaction,
    _get_metabolite_list_for_reaction,
)
from bigg_models.version import __version__ as version, __api_version__ as api_version

from cobradb.models import *

import pytest
from pytest import raises
import time
import json
from itertools import chain


@pytest.fixture(scope="function")
def session(request):
    """Make a session"""

    def teardown():
        Session.close_all()

    request.addfinalizer(teardown)

    return Session()


# util
def test__shorten_name():
    assert _shorten_name(None) is None
    assert _shorten_name("abc", 2) == "ab..."


# Reactions
def test_get_reaction_and_models(session):
    result = get_reaction_and_models("ADA", session)
    assert result["bigg_id"] == "ADA"
    assert result["name"] == "Adenosine deaminase"
    assert result["pseudoreaction"] is False
    assert {
        "bigg_id": "iAPECO1_1312",
        "organism": "Escherichia coli APEC O1",
    } in result["models_containing_reaction"]
    assert set(result["old_identifiers"]) == {"ADA", "ADNDA", "ADNDA_c"}
    assert "old_id" not in result["database_links"]
    with raises(Exception):
        result = get_reaction_and_models("not_a_reaction", session)


def test_get_reactions_for_model(session):
    result = get_reactions_for_model("iAPECO1_1312", session)
    assert len(result) > 5
    assert "ADA" in [x["bigg_id"] for x in result]


def test__get_old_ids_for_model_reaction(session):
    res = _get_old_ids_for_model_reaction("iAPECO1_1312", "ADA", session)
    assert res == ["ADA"]


def test_get_model_reaction(session):
    result = get_model_reaction("iAPECO1_1312", "ADA", session)
    assert result["bigg_id"] == "ADA"
    assert result["name"] == "Adenosine deaminase"
    assert result["results"][0]["gene_reaction_rule"] == "APECO1_RS08710"
    assert "APECO1_RS08710" in [x["bigg_id"] for x in result["results"][0]["genes"]]
    assert "nh4" in [x["bigg_id"] for x in result["metabolites"]]
    assert "Ammonium" in [x["name"] for x in result["metabolites"]]
    assert "c" in [x["compartment_bigg_id"] for x in result["metabolites"]]
    assert 1.0 in [x["stoichiometry"] for x in result["metabolites"]]
    assert "other_models_with_reaction" in result
    assert "iAPECO1_1312" not in result["other_models_with_reaction"]
    assert "upper_bound" in result["results"][0]
    assert "lower_bound" in result["results"][0]
    assert "objective_coefficient" in result["results"][0]
    assert result["old_identifiers"] == ["ADA"]
    assert "old_id" not in result["database_links"]


# def test_get_model_reaction_multiple_copies(session):
#     # this reaction should have two copies
#     res = get_model_reaction('RECON1', 'FACOAL204', session)
#     assert len(res['results']) == 2
#     this_copy = res['results'][0]['copy_number']
#     if this_copy == 1:
#         r1 = res['results'][0]
#         r2 = res['results'][1]
#     else:
#         r1 = res['results'][1]
#         r2 = res['results'][0]

#     assert r1['gene_reaction_rule'] == '(2180_AT1)'
#     assert [x['bigg_id'] for x in r1['genes']] == ['2180_AT1']
#     assert r1['exported_reaction_id'] == 'FACOAL204_copy1'

#     assert r2['gene_reaction_rule'] == '(22305_AT1) or (2181_AT2) or (2181_AT1) or (2180_AT1) or (22305_AT2) or (2182_AT1) or (2182_AT2)'
#     assert {x['bigg_id'] for x in r2['genes']} == {'22305_AT1', '2181_AT2', '2181_AT1', '2180_AT1', '22305_AT2', '2182_AT1', '2182_AT2'}
#     # no names for these genes
#     assert (x for x in r2['genes'] if x ['bigg_id'] == '22305_AT1').next()['name'] is None
#     assert (x for x in r2['genes'] if x ['bigg_id'] == '22305_AT2').next()['name'] is None

#     # copy 2
#     assert r2['exported_reaction_id'] == 'FACOAL204_copy2'


# Models
def test_get_models(session):
    result = get_models(session)
    assert "iAPECO1_1312" in [r["bigg_id"] for r in result]
    assert "Escherichia coli APEC O1" in [r["organism"] for r in result]
    assert type(result[0]["metabolite_count"]) is int
    assert type(result[0]["reaction_count"]) is int
    assert type(result[0]["gene_count"]) is int


def test_get_model_and_counts(session):
    result = get_model_and_counts("iAPECO1_1312", session)
    assert result["model_bigg_id"] == "iAPECO1_1312"
    assert result["organism"] == "Escherichia coli APEC O1"
    assert type(result["metabolite_count"]) is int
    assert type(result["reaction_count"]) is int
    assert type(result["gene_count"]) is int


def test_get_model_list(session):
    result = get_model_list(session)
    assert "iAPECO1_1312" in result


# -------------
# Metabolites
# -------------


def test_get_metabolite_list_for_reaction(session):
    result = _get_metabolite_list_for_reaction("GAPD", session)
    assert "g3p" in [r["bigg_id"] for r in result]
    assert isinstance(result[0]["stoichiometry"], float)
    assert "c" in [r["compartment_bigg_id"] for r in result]


def test_get_metabolite(session):
    result = get_metabolite("akg", session)
    assert result["bigg_id"] == "akg"
    assert result["name"] == "2-Oxoglutarate"
    assert result["formulae"] == ["C5H4O5"]
    assert "c" in [c["bigg_id"] for c in result["compartments_in_models"]]
    assert "iAPECO1_1312" in [
        c["model_bigg_id"] for c in result["compartments_in_models"]
    ]
    assert "Escherichia coli APEC O1" in [
        c["organism"] for c in result["compartments_in_models"]
    ]
    assert {
        "link": "http://identifiers.org/kegg.compound/C00026",
        "id": "C00026",
    } in result["database_links"]["KEGG Compound"]
    assert set(result["old_identifiers"]) == {"akg"}
    assert "old_id" not in result["database_links"]


def test__get_old_ids_for_model_comp_metabolite(session):
    res = _get_old_ids_for_model_comp_metabolite("akg", "c", "iAPECO1_1312", session)
    assert res == ["akg_c"]


def test_get_model_comp_metabolite(session):
    result = get_model_comp_metabolite("akg", "c", "iAPECO1_1312", session)
    assert result["bigg_id"] == "akg"
    assert result["name"] == "2-Oxoglutarate"
    assert result["compartment_bigg_id"] == "c"
    assert result["formula"] == "C5H4O5"
    assert result["charge"] == -2
    reaction_bigg_ids = [r["bigg_id"] for r in result["reactions"]]
    assert "AKGDH" in reaction_bigg_ids
    assert "EX_akg_e" not in reaction_bigg_ids
    assert "iAPECO1_1312" not in [
        r["bigg_id"] for r in result["other_models_with_metabolite"]
    ]
    assert result["old_identifiers"] == ["akg_c"]
    assert "old_id" not in result["database_links"]
    # make sure models are being filtered
    result = get_model_comp_metabolite("h", "c", "iAPECO1_1312", session)
    assert all([r["model_bigg_id"] == "iAPECO1_1312" for r in result["reactions"]])


def test_get_model_metabolites(session):
    results = get_model_metabolites("iAPECO1_1312", session)
    assert "akg" in [x["bigg_id"] for x in results]
    assert "c" in [x["compartment_bigg_id"] for x in results]


# genes
def test_get_gene_list_for_model(session):
    results = get_gene_list_for_model("iAPECO1_1312", session)
    assert "APECO1_RS08710" in [x["bigg_id"] for x in results]


def test__get_gene_list_for_model_reaction(session):
    mr_db = (
        session.query(ModelReaction)
        .join(Model)
        .join(Reaction)
        .filter(Model.bigg_id == "iAF1260")
        .filter(Reaction.bigg_id == "ATPM")
        .filter(Reaction.pseudoreaction == True)
        .first()
    )
    results = _get_gene_list_for_model_reaction(mr_db.id, session)
    assert len(results) == 0

    mr_db = (
        session.query(ModelReaction)
        .join(Model)
        .join(Reaction)
        .filter(Model.bigg_id == "iAF1260")
        .filter(Reaction.bigg_id == "NTP1")
        .filter(Reaction.pseudoreaction == False)
        .first()
    )
    results = _get_gene_list_for_model_reaction(mr_db.id, session)
    assert len(results) == 2


def test__get_old_ids_for_model_gene(session):
    res = _get_old_ids_for_model_gene("APECO1_RS08710", "iAPECO1_1312", session)
    assert res == ["APECO1_706"]
    res = _get_old_ids_for_model_gene("TM0846", "iLJ478", session)
    assert set(res) == {"TM0846", "TM_0846"}


def test_get_model_gene(session):
    result = get_model_gene("ECO103_2936", "iECO103_1326", session)
    assert result["bigg_id"] == "ECO103_2936"
    assert result["old_identifiers"] == ["ECO103_2936"]
    none_links = [
        x
        for x in result["database_links"].items()
        if any([ext["link"] is None for ext in x[1]])
    ]
    assert len(none_links) == 0
    # No protein sequence
    assert result["dna_sequence"] is not None
    assert result["protein_sequence"] is None


def test_get_model_gene_2(session):
    result = get_model_gene("b1779", "iJO1366", session)
    # Yes protein sequence
    assert result["dna_sequence"] is not None
    assert result["protein_sequence"] is not None


# database sources
def test_get_database_sources(session):
    assert ("kegg.compound", "KEGG Compound") in get_database_sources(session)


# Escher maps
def test_escher_maps_for_reaction(session):
    maps = get_escher_maps_for_reaction("GAPD", "iMM904", session)
    assert "iMM904.Central carbon metabolism" in [x["map_name"] for x in maps]
    assert "669341" in maps[0]["element_id"]


def test_escher_maps_for_metabolite(session):
    maps = get_escher_maps_for_metabolite("atp", "c", "iMM904", session)
    assert "iMM904.Central carbon metabolism" == maps[0]["map_name"]
    assert "672110" in maps[0]["element_id"]


def test_json_for_map():
    session = Session()
    map_json = json_for_map("iMM904.Central carbon metabolism", session)
    assert isinstance(map_json, str)
    assert json.loads(map_json)[0]["homepage"] == "https://escher.github.io"
    session.close()


# search


def test_search_for_universal_reactions(session):
    results = search_for_universal_reactions("GAPD", session)
    assert results[0]["bigg_id"] == "GAPD"


def test_search_for_reactions(session):
    time1 = time.time()
    results = search_for_reactions("GAPD", session)
    time2 = time.time()
    print("search_for_reactions took %0.3f ms" % ((time2 - time1) * 1000.0))

    assert results[0]["bigg_id"] == "GAPD"
    assert "iAPECO1_1312" in [x["model_bigg_id"] for x in results]
    results = search_for_reactions("GAPD-", session)
    assert results[0]["bigg_id"] == "GAPD"
    # test name search
    results = search_for_reactions("Glyceraldehyde-3-phosphate dehydrogenase", session)
    assert "GAPD" in [x["bigg_id"] for x in results]


def test_search_for_universal_metabolites(session):
    results = search_for_universal_metabolites("g3p", session)
    assert results[0]["bigg_id"] == "g3p"


def test_search_for_metabolites(session):
    results = search_for_metabolites("g3pd", session)
    assert "g3p" in [x["bigg_id"] for x in results]
    assert "iAPECO1_1312" in [x["model_bigg_id"] for x in results]
    # strict
    results = search_for_metabolites("g3p_c", session, strict=True)
    assert "g3p" in [x["bigg_id"] for x in results]
    assert "c" in [x["compartment_bigg_id"] for x in results]
    # catch bug where there are a MILLION results:
    assert len(results) <= len(get_model_list(session))
    results = search_for_metabolites("g3p", session, strict=True)
    assert results == []


def test_search_for_genes(session):
    results = search_for_genes("APECO1_RS08710", session)
    assert results[0]["bigg_id"] == "APECO1_RS08710"
    assert results[0]["model_bigg_id"] == "iAPECO1_1312"
    results = search_for_genes(
        "APECO1_RS08710", session, limit_models=["iAPECO1_1312", "iJO1366"]
    )
    assert results[0]["bigg_id"] == "APECO1_RS08710"
    results = search_for_genes("APECO1_RS08710", session, limit_models=["iJO1366"])
    assert len(results) == 0
    results = search_for_genes("APECO1_RS08710_6", session)
    assert len(results) == 0
    # test query == ''
    results = search_for_genes("", session)
    assert len(results) == 0


def test_search_for_models(session):
    results = search_for_models("iAPECO1_1312", session)
    assert results[0]["bigg_id"] == "iAPECO1_1312"
    assert "metabolite_count" in results[0]
    assert "organism" in results[0]
    results = search_for_models("iAPECO1_1312-", session)
    assert results[0]["bigg_id"] == "iAPECO1_1312"
    # by organism
    results = search_for_models("Escherichia coli", session)
    assert "iAPECO1_1312" in [x["bigg_id"] for x in results]


def test_search_ids_fast(session):
    time1 = time.time()
    results = search_ids_fast("ga", session)
    time2 = time.time()
    print("l = 2, search_ids_fast took %0.3f ms" % ((time2 - time1) * 1000.0))

    time1 = time.time()
    results = search_ids_fast("gap", session)
    time2 = time.time()
    print("l = 3, search_ids_fast took %0.3f ms" % ((time2 - time1) * 1000.0))

    time1 = time.time()
    results = search_ids_fast("gapd", session)
    time2 = time.time()
    print("l = 4, search_ids_fast took %0.3f ms" % ((time2 - time1) * 1000.0))
    assert "GAPD" in results

    # organism
    results = search_ids_fast("Escherichia coli", session)
    assert "Escherichia coli APEC O1" in results


# advanced search by external database ID

# get_metabolites_for_database_id

# get_reactions_for_database_id


def test_get_genes_for_database_id(session):
    assert {
        "bigg_id": "b0241",
        "model_bigg_id": "iJO1366",
        "name": "phoE",
    } in get_genes_for_database_id(session, "b0241", "old_bigg_id")


# version


def test_database_version(session):
    res = database_version(session)
    assert "201" in res["last_updated"]
    assert res["bigg_models_version"] == version
    assert res["api_version"] == api_version
