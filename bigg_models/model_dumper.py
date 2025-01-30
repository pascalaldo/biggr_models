# -*- coding: utf-8 -*-

from bigg_models.server import static_model_dir as static_dir

from cobradb.models import *
from cobradb.model_dumping import dump_model
from cobradb import settings

from os.path import join, isdir, abspath, dirname, isfile
from os import makedirs, system
from subprocess import call
import time
import shutil
import cobra

# DEBUG means test with one model
DEBUG = False


def get_model_polisher():
    """Return the path to ModelPolisher."""
    path = settings.model_polisher
    if not isfile(path):
        raise Exception("Could not find ModelPolisher: %s" % path)
    if not isfile(settings.java):
        raise Exception("Could not find java executable: %s" % settings.java)
    return path


def make_all_static_models():
    """Write static models for all models in the database."""
    # delete static model dir
    # try:
    #     shutil.rmtree(static_dir)
    # except OSError:
    #     pass
    #
    # # make the directories
    # try:
    #     makedirs(static_dir)
    # except OSError:
    #     pass

    failed_models = []
    model_polisher_path = get_model_polisher()
    session = Session()
    bigg_ids = [i[0] for i in session.query(Model.bigg_id)]
    for bigg_id in bigg_ids:
        if DEBUG and bigg_id != "e_coli_core":
            continue
        # keep track of which models failed
        print(
            "------------------------------------------------------------\n"
            "Dumping model %s" % bigg_id
        )
        if not write_static_model(bigg_id, model_polisher_path):
            failed_models.append(bigg_id)
    session.close()
    if len(failed_models) > 0:
        return "Failed for models " + " ".join(failed_models)


def write_static_model(bigg_id, model_polisher_path):
    """Write out static files for a model with the given BiGG ID.

    This will output compressed and uncompressed SBML L3 + FBCv2, JSON,
    and MAT files.

    """
    success = True
    print("Dumping model")
    t = time.time()
    model = dump_model(bigg_id)
    print("Dumping finished in %.2f seconds" % (time.time() - t))
    sbml_filepath = join(static_dir, bigg_id + ".xml")
    try:
        print("Writing SBML")
        t = time.time()
        cobra.io.write_sbml_model(model, sbml_filepath)
        print("Writing SBML finished in %.2f seconds" % (time.time() - t))
    except Exception as e:
        success = False
        print('failed to export sbml model "%s": %s' % (bigg_id, e.message))
    else:
        print("Compressing")
        t = time.time()
        system("gzip --keep --force --best " + sbml_filepath)
        print("Compressing finished in %.2f seconds" % (time.time() - t))
        # else:
        #     success = False

    print("Writing MAT")
    t = time.time()
    mat_filepath = join(static_dir, bigg_id + ".mat")
    cobra.io.save_matlab_model(model, mat_filepath)
    system("gzip --keep --force --best " + mat_filepath)
    print("Writing MAT finished in %.2f seconds" % (time.time() - t))

    print("Writing JSON")
    t = time.time()
    json_filepath = join(static_dir, bigg_id + ".json")
    cobra.io.save_json_model(model, json_filepath)
    system("gzip --keep --force --best " + json_filepath)
    print("Writing JSON finished in %.2f seconds" % (time.time() - t))

    return success
