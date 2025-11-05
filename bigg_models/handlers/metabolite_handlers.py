from typing import Optional
from cobradb.models import (
    Compartment,
    CompartmentalizedComponent,
    Component,
    Model,
    ModelCompartmentalizedComponent,
    UniversalComponent,
)
from bigg_models.handlers import utils
from bigg_models.queries import metabolite_queries, utils as query_utils

import re


class UniversalMetaboliteListViewHandler(utils.DataHandler):
    title = "Universal Metabolites"
    columns = [
        utils.DataColumnSpec(
            UniversalComponent.bigg_id,
            "BiGG ID",
            hyperlink="/universal/metabolites/${row['universalcomponent__bigg_id']}",
        ),
        utils.DataColumnSpec(UniversalComponent.name, "Name"),
    ]

    def pre_filter(self, query):
        return query.filter(UniversalComponent.collection_id == None)

    def breadcrumbs(self):
        return [
            ("Home", "/"),
            ("Universal", None),
            ("Metabolites", "/universal/metabolites/"),
        ]


class UniversalMetaboliteHandler(utils.BaseHandler):
    template = utils.env.get_template("universal_metabolite.html")

    def get(self, met_bigg_id):
        try:
            result = utils.safe_query(metabolite_queries.get_metabolite, met_bigg_id)
        except query_utils.RedirectError as e:
            self.redirect(re.sub(self.request.path, "%s$" % met_bigg_id, e.args[0]))
        else:
            result["breadcrumbs"] = [
                ("Home", "/"),
                ("Universal", None),
                ("Metabolites", f"/universal/metabolites/"),
                (met_bigg_id, f"/universal/metabolites/{met_bigg_id}"),
            ]
            self.return_result(result)


class MetaboliteListViewHandler(utils.DataHandler):
    title = "Metabolites"
    model_bigg_id: Optional[str] = None
    columns = [
        utils.DataColumnSpec(
            ModelCompartmentalizedComponent.bigg_id,
            "BiGG ID",
            hyperlink="/models/${row['model__bigg_id']}/metabolites/${row['modelcompartmentalizedcomponent__bigg_id']}",
        ),
        utils.DataColumnSpec(
            Component.name,
            "Name",
            requires=[
                ModelCompartmentalizedComponent.compartmentalized_component,
                CompartmentalizedComponent.component,
            ],
        ),
        utils.DataColumnSpec(
            Compartment.bigg_id,
            "Compartment",
            requires=[
                ModelCompartmentalizedComponent.compartmentalized_component,
                CompartmentalizedComponent.compartment,
            ],
        ),
        utils.DataColumnSpec(
            Model.bigg_id, "Model", requires=ModelCompartmentalizedComponent.model
        ),
        utils.DataColumnSpec(
            (Component.collection_id != None),
            "Collection-specific",
            requires=[
                ModelCompartmentalizedComponent.compartmentalized_component,
                CompartmentalizedComponent.component,
            ],
            search_type="bool",
        ),
    ]

    def pre_filter(self, query):
        return query.filter(Model.bigg_id == self.model_bigg_id)

    def breadcrumbs(self):
        return [
            ("Home", "/"),
            ("Models", "/models/"),
            (self.model_bigg_id, f"/models/{self.model_bigg_id}"),
            ("Metabolites", f"/models/{self.model_bigg_id}/metabolites/"),
        ]


class MetaboliteHandler(utils.BaseHandler):
    template = utils.env.get_template("metabolite.html")

    def get(self, model_bigg_id, comp_met_id):
        results = utils.safe_query(
            metabolite_queries.get_model_comp_metabolite,
            comp_met_id,
            model_bigg_id,
        )
        results["breadcrumbs"] = [
            ("Home", "/"),
            ("Models", "/models/"),
            (model_bigg_id, f"/models/{model_bigg_id}/"),
            ("Metabolites", f"/models/{model_bigg_id}/metabolites/"),
            (
                utils.format_bigg_id(comp_met_id, "comp_comp"),
                f"/models/{model_bigg_id}/metabolites/{comp_met_id}",
            ),
        ]
        self.return_result(results)
