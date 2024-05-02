<h1 align="center"><p><img src="http://assets.tira.io/tira-icons/tira-logo-32px-white.png" style="vertical-align:bottom"> TIRA Integrated Research Architecture </p>
</h1>

This repository contains the source code for all components of the [TIRA](https://www.tira.io) shared task platform.

Components:

- [Backend](application) (test coverage: ![test coverage backend](application/test/test-coverage/coverage.svg))
- [Frontend](application/src/tira/frontend-vuetify) (test coverage: ![Coverage of the frontend](application/src/tira/frontend-vuetify/coverage/badge-lines.svg))
- [Python Client](python-client) (test coverage: ![Coverage of the python client](python-client/tests/test-coverage/coverage.svg))


## Resources
* [Wiki](https://tira-io.github.io/tira/): Getting started with TIRA as a developer/administrator
* [User Docs](https://www.tira.io/t/getting-started/1364): Getting started with TIRA as a user
* [Papers](https://webis.de/publications.html?q=tira): List of publications
* [Contribution Guide](CONTRIBUTING.md): How to contribute to the TIRA project


## Setup Your Development Environment

We use [devcontainers](https://code.visualstudio.com/docs/devcontainers/containers) for development. To start your environment, either use Github Codespaces (click on "Code" -> "Codespaces" in Github to open one) as easiest way to get started, or [devpod](https://github.com/loft-sh/devpod) as open source alternative (directly pointing to our Kubernetes or your local docker installation).

Run `make` to get an overview of all commands that will setup a self-contained tira application in your dev environment.

1. Setup the database and compile the vuetify frontend
   ```bash
   ~$ make setup
   ```

2. Start the local environment, point your browser to the specified URL
   ```bash
   ~$ make run-develop
   ```

3. Optionally: To work on real data, initialize your development database from a database dump via
   ```bash
   ~$ make import-data-from-dump
   ```
   or to work with mock data run:
    ```bash
   ~$ cd application
   ~$ make import-mock-data
   ```


## Paper

If you use TIRA in your own research, please cite our paper

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
