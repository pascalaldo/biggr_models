#!/bin/bash

mkdir -p /static/models/
mkdir -p /static/multistrain/
mkdir -p /static/namespace/

BIGG_MODELS_DIR=`python -c "import bigg_models; print(bigg_models.__file__)" | xargs dirname`
ln -s /static/models $BIGG_MODELS_DIR/static/models
ln -s /static/multistrain $BIGG_MODELS_DIR/static/multistrain
ln -s /static/namespace $BIGG_MODELS_DIR/static/namespace

bin/run

sass $BIGG_MODELS_DIR/scss/custom.scss $BIGG_MODELS_DIR/static/css/custom.css

cp node_modules/bootstrap/dist/js/bootstrap.bundle.min.js bigg_models/static/js/

if [ $? -eq 0 ]; then
	python -m bigg_models.server --port=8910 --processes=1 --debug=True
fi

