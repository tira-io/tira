<h1 align="center"><p><img src="http://assets.tira.io/tira-icons/tira-logo-32px-white.png" style="vertical-align:bottom"> TIRA Integrated Research Architecture </p>
</h1>

This repository contains the source code for all components of the [TIRA](https://www.tira.io) shared task platform.

Components:

- [Backend](application) (test coverage: ![test coverage backend](application/test/test-coverage/coverage.svg))
- [Frontend](application/src/tira/frontend-vuetify) (test coverage: ![Coverage of the frontend](application/src/tira/frontend-vuetify/coverage/badge-lines.svg))
- [Python Client](python-client) (test coverage: ![Coverage of the python client](python-client/tests/test-coverage/coverage.svg))


## Setup Your Local Development Environment

We use [dev containers](https://code.visualstudio.com/docs/devcontainers/containers) to simplify development. Please install Docker and an IDE with support for dev containers on your machine (we usually use VS Code).

First, please clone the repository:
```
git clone git@github.com:tira-io/tira.git
```

Please open the directory `application` in VS Code, and confirm to use the provided dev container.

If you want to work on production data, please ensure that you can login to ssh.webis.de, and then do the following:

```
make import-data-from-dump
```

To start TIRA locally, please run:

```
make run-develop
```

Then, you can point your browser to the specified URL.

## Resources
* [Wiki](../../wiki): Getting started with TIRA as a developer/administrator
* [User Docs](https://www.tira.io/t/getting-started/1364): Getting started with TIRA as a user
* [Papers](https://webis.de/publications.html?q=tira): List of publications
* [Contribution Guide](CONTRIBUTING.md): How to contribute to the TIRA project

## Create New Zip of the Database Dump

Go the the password database `webis.uni-weimar.de:code-admin/passwords` -> Generic -> tira-development-database-dump

```
cd /mnt/ceph/storage/data-in-production/tira/development-database-dumps/
zip --encrypt django-db-dump-<DATE>.zip /mnt/ceph/tira/state/db-backup/django-db-dump-<DATE>.json
ln -s django-db-dump-<DATE>.zip django-db-dump.zip
```

## Paper

If you use TIRA in your own research, please be sure to cite our paper

```
@InProceedings{froebe:2023b,
  address =                  {Berlin Heidelberg New York},
  author =                   {Maik Fr{\"o}be and Matti Wiegmann and Nikolay Kolyada and Bastian Grahm and Theresa Elstner and Frank Loebe and Matthias Hagen and Benno Stein and Martin Potthast},
  booktitle =                {Advances in Information Retrieval. 45th European Conference on {IR} Research ({ECIR} 2023)},
  month =                    apr,
  publisher =                {Springer},
  series =                   {Lecture Notes in Computer Science},
  site =                     {Dublin, Irland},
  title =                    {{Continuous Integration for Reproducible Shared Tasks with TIRA.io}},
  todo =                     {doi, month, pages, code},
  year =                     2023
}
```
## License

[MIT License](LICENSE)
