from bigg_models.handlers import general
from bigg_models import queries

from cobradb.models import Compartment


# Compartments
class CompartmentListHandler(general.BaseHandler):
    template = general.env.get_template("compartments.html")

    def get(self):
        session = queries.Session()
        results = {
            "compartments": [
                {"bigg_id": x[0], "name": x[1]}
                for x in session.query(Compartment.bigg_id, Compartment.name)
            ]
        }
        session.close()
        self.return_result(results)


class CompartmentHandler(general.BaseHandler):
    template = general.env.get_template("compartment.html")

    def get(self, compartment_bigg_id):
        session = queries.Session()
        result_db = (
            session.query(Compartment)
            .filter(Compartment.bigg_id == compartment_bigg_id)
            .first()
        )
        session.close()

        result = {"bigg_id": result_db.bigg_id, "name": result_db.name}
        self.return_result(result)
