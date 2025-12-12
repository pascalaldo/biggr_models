from biggr_models.handlers import compartment_handlers
from sqlalchemy import select
from sqlalchemy.orm import Session
from cobradb.models import Compartment

from biggr_models.queries import utils


def get_compartment(session: Session, bigg_id: str):
    compartment_db = session.scalars(
        select(Compartment).filter(Compartment.bigg_id == bigg_id).limit(1)
    ).first()
    if compartment_db is None:
        raise utils.NotFoundError("No compartment found with BiGG ID " + bigg_id)

    models_with_compartment_url = f"/compartments/{compartment_db.bigg_id}/models"
    models_with_compartment_columns = (
        compartment_handlers.ModelsWithCompartmentListViewHandler.column_specs
    )

    result = {
        "compartment": compartment_db,
        "models_with_compartment_url": models_with_compartment_url,
        "models_with_compartment_columns": models_with_compartment_columns,
    }
    return result
