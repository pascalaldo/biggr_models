biggr_models
-----------


[BiGGr](https://biggr.org) is a website for browsing normalized, gold-standard genome-scale models and the corresponding metabolite and reaction namespace.
BiGGr is based on [BiGG](http://bigg.ucsd.edu), described in the following publication:

King ZA, Lu JS, Dräger A, Miller PC, Federowicz S, Lerman JA, Ebrahim A, Palsson BO, and Lewis NE. (2015). BiGG Models: A platform for integrating, standardizing, and sharing genome-scale models. Nucl Acids Res. doi:[10.1093/nar/gkv1049](https://doi.org/10.1093/nar/gkv1049).

This repository includes the web server and front-end for BiGGr. The database is managed by [COBRAdb](https://github.com/biosustain/cobradb), Escher maps are auto-generated with the help of [BiGGr Maps](http://github.com/biosustain/biggr_maps), and the [BiGGr Python library](http://github.com/biosustain/biggr) can be used to easily access the database and its API.

Installation
============

It is recommended to install and run BiGGr Models using [Docker](https://www.docker.com/).

To run the server using Docker, make sure Docker is installed and then follow these steps:

For development environments:
1. Download cobradb with ```git clone git@github.com:biosustain/cobradb.git```.
2. Download the code with ```git clone git@github.com:biosustain/biggr_models.git```
3. ```cd biggr_models```
4. TODO: SETTINGS, OTHER FILES
5. Run ```docker compose --profile dev up --build```.

For production environments:
1. Download the code with ```git clone git@github.com:biosustain/biggr_models.git```
2. ```cd biggr_models```
3. TODO: SETTINGS, OTHER FILES
4. Run ```docker compose --profile prod up --build```.

Note that for the biggr.org server, a CI/CD pipeline is implemented on GitHub.

License
=======

This codebase is released under the
[MIT license](https://github.com/SBRG/bigg_models/blob/master/LICENSE). The
license information for the BiGG Models website hosted at SBRG and the
associated models can be found here: http://bigg.ucsd.edu/license.
