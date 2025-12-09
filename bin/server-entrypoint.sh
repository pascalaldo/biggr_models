#!/bin/bash

# mkdir -p /static/models/
# mkdir -p /static/multistrain/
# mkdir -p /static/namespace/

BIGG_MODELS_DIR=`python -c "import bigg_models; print(bigg_models.__file__)" | xargs dirname`
# ln -s /static/models $BIGG_MODELS_DIR/static/models
ln -s /models $BIGG_MODELS_DIR/static/models
# ln -s /static/multistrain $BIGG_MODELS_DIR/static/multistrain
# ln -s /static/namespace $BIGG_MODELS_DIR/static/namespace

bin/run

if [ $? -eq 0 ]; then
	for i in $(seq 1 5);
	do
		python -m bigg_models.server --port=8910 --process_i=$i &
	done
	python -m bigg_models.server --port=8910 --process_i=6
fi

