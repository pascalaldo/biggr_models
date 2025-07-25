from bigg_models.queries import utils, escher_map_queries

from cobradb.util import ref_tuple_to_str
from cobradb import settings
from cobradb.models import (
    DatabaseVersion,
    Genome,
    Model,
    ModelCount,
    Publication,
    PublicationModel,
)

from sqlalchemy import func
from os import path


def get_models_count(session, multistrain_off, **kwargs):
    """Return the number of models in the database."""
    query = session.query(Model)
    if multistrain_off:
        query = utils._add_multistrain_filter(session, query, Model)
    return query.count()


def get_models(
    session,
    page=None,
    size=None,
    sort_column=None,
    sort_direction="ascending",
    multistrain_off=False,
):
    """Get models and number of components.

    Arguments
    ---------

    session: An ome session object.

    page: The page, or None for all pages.

    size: The page length, or None for all pages.

    sort_column: The name of the column to sort. Must be one of 'bigg_id',
    'organism', 'metabolite_count', 'reaction_count', and 'gene_count'.

    sort_direction: Either 'ascending' or 'descending'.

    Returns
    -------

    A list of objects with keys 'bigg_id', 'organism', 'metabolite_count',
    'reaction_count', and 'gene_count'.

    """
    # get the sort column
    columns = {
        "bigg_id": func.lower(Model.id),
        "organism": func.lower(Model.organism),
        "metabolite_count": ModelCount.metabolite_count,
        "reaction_count": ModelCount.reaction_count,
        "gene_count": ModelCount.gene_count,
    }

    if sort_column is None:
        sort_column_object = None
    else:
        try:
            sort_column_object = columns[sort_column]
        except KeyError:
            print("Bad sort_column name: %s" % sort_column)
            sort_column_object = next(iter(columns.values()))

    # set up the query
    query = session.query(
        Model.id,
        Model.organism,
        ModelCount.metabolite_count,
        ModelCount.reaction_count,
        ModelCount.gene_count,
    ).join(ModelCount, ModelCount.model_id == Model.id)
    print(str(query))
    if multistrain_off:
        query = utils._add_multistrain_filter(session, query, Model)
    print(str(query))
    # order and limit
    query = utils._apply_order_limit_offset(
        query, sort_column_object, sort_direction, page, size
    )
    print(str(query))

    return [
        {
            "bigg_id": x[0],
            "organism": x[1],
            "metabolite_count": x[2],
            "reaction_count": x[3],
            "gene_count": x[4],
        }
        for x in query
    ]


def get_model_and_counts(
    model_bigg_id, session, static_model_dir=None, static_multistrain_dir=None
):
    model_db = (
        session.query(
            Model,
            ModelCount,
            Genome,
            Publication.reference_type,
            Publication.reference_id,
        )
        .join(ModelCount, ModelCount.model_id == Model.id)
        .outerjoin(Genome, Genome.id == Model.genome_id)
        .outerjoin(PublicationModel, PublicationModel.model_id == Model.id)
        .outerjoin(Publication, Publication.id == PublicationModel.publication_id)
        .filter(Model.id == model_bigg_id)
        .first()
    )
    if model_db is None:
        raise utils.NotFoundError("No Model found with BiGG ID " + model_bigg_id)

    # genome ref
    if model_db[2] is None:
        genome_ref_string = genome_name = None
    else:
        genome_name = model_db[2].accession_value
        genome_ref_string = ref_tuple_to_str(model_db[2].accession_type, genome_name)
    m_escher_maps = escher_map_queries.get_escher_maps_for_model(
        model_db[0].id, session
    )
    result = {
        "model_bigg_id": model_db[0].id,
        "published_filename": model_db[0].published_filename,
        "organism": getattr(model_db[2], "organism", None),
        "genome_name": genome_name,
        "genome_ref_string": genome_ref_string,
        "metabolite_count": model_db[1].metabolite_count,
        "reaction_count": model_db[1].reaction_count,
        "gene_count": model_db[1].gene_count,
        "reference_type": model_db[3],
        "reference_id": model_db[4],
        "escher_maps": m_escher_maps,
        "last_updated": session.query(DatabaseVersion)
        .first()
        .date_time.strftime("%b %d, %Y"),
    }
    if static_model_dir:
        # get filesizes
        for ext in ("xml", "xml_gz", "mat", "mat_gz", "json", "json_gz", "multistrain"):
            if ext == "multistrain":
                if not static_multistrain_dir:
                    continue
                fpath = path.join(
                    static_multistrain_dir, model_bigg_id + "_multistrain.zip"
                )
            else:
                fpath = path.join(
                    static_model_dir, model_bigg_id + "." + ext.replace("_", ".")
                )
            byte_size = path.getsize(fpath) if path.isfile(fpath) else 0
            if byte_size > 1048576:
                result[ext + "_size"] = "%.1f MB" % (byte_size / 1048576.0)
            elif byte_size > 1024:
                result[ext + "_size"] = "%.1f kB" % (byte_size / 1024.0)
            elif byte_size > 0:
                result[ext + "_size"] = "%d B" % (byte_size)
    return result


def get_model_list(session):
    """Return a list of all models, for advanced search."""
    model_list = session.query(Model.id).order_by(Model.id)
    list = [x[0] for x in model_list]
    list.sort()
    return list


def get_model_json_string(model_bigg_id):
    """Get the model JSON for download."""
    fpath = path.join(settings.model_dump_directory, model_bigg_id + ".json")
    try:
        with open(fpath, "r") as f:
            data = f.read()
    except IOError as e:
        raise utils.NotFoundError(e.message)
    return data
