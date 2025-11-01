from bigg_models.handlers import utils

from cobradb.models import Compartment


class CompartmentListViewHandler(utils.DataHandler):
    title = "Compartments"
    columns = [
        utils.DataColumnSpec(
            Compartment.bigg_id,
            "BiGG ID",
            hyperlink="/compartments/${row['compartment__bigg_id']}",
        ),
        utils.DataColumnSpec(
            Compartment.name,
            "Name",
            hyperlink="/compartments/${row['compartment__bigg_id']}",
        ),
    ]

    def breadcrumbs(self):
        return [("Home", "/"), ("Compartments", "/compartments/")]


class CompartmentHandler(utils.BaseHandler):
    template = utils.env.get_template("compartment.html")

    def get(self, compartment_bigg_id):
        session = utils.Session()
        result_db = (
            session.query(Compartment)
            .filter(Compartment.bigg_id == compartment_bigg_id)
            .first()
        )
        session.close()

        result = {"bigg_id": result_db.bigg_id, "name": result_db.name}
        self.return_result(result)
