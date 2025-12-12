#!/bin/bash

# mkdir -p /static/models/
# mkdir -p /static/namespace/
#
# ln -s /static/models biggr_models/static/models
ln -s /models biggr_models/static/models

cd /cobradb
python setup.py install

cd /server

bin/run

npm install bootstrap@5.3.7

sass --quiet --update --watch biggr_models/scss/custom.scss biggr_models/static/css/custom.css &

cp node_modules/bootstrap/dist/js/bootstrap.bundle.min.js biggr_models/static/js/

if [ $? -eq 0 ]; then
	python -m biggr_models.server --port=8910 --debug=True
fi

