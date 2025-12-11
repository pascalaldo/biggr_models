#!/bin/bash

# mkdir -p /static/models/
# mkdir -p /static/namespace/
#
# ln -s /static/models bigg_models/static/models
ln -s /models bigg_models/static/models

cd /cobradb
python setup.py install

cd /server

bin/run

npm install bootstrap@5.3.7

sass --quiet --update --watch bigg_models/scss/custom.scss bigg_models/static/css/custom.css &

cp node_modules/bootstrap/dist/js/bootstrap.bundle.min.js bigg_models/static/js/

if [ $? -eq 0 ]; then
	python -m bigg_models.server --port=8910 --debug=True
fi

