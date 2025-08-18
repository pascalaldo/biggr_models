#!/bin/bash

mkdir -p /static/models/
mkdir -p /static/multistrain/
mkdir -p /static/namespace/

ln -s /static/models bigg_models/static/models
ln -s /static/multistrain bigg_models/static/multistrain
ln -s /static/namespace bigg_models/static/namespace

bin/run

npm install bootstrap@5.3.7

sass --quiet --update --watch bigg_models/scss/custom.scss bigg_models/static/css/custom.css &

cp node_modules/bootstrap/dist/js/bootstrap.bundle.min.js bigg_models/static/js/

if [ $? -eq 0 ]; then
	python -m bigg_models.server --port=8910 --processes=1 --debug=True
fi

