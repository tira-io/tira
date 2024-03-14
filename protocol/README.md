# TIRA Protocol

THis repository contains the tira protocol source files and build tools. If you change the protocol, please recompile them and commit them to the tira application and tira host repositories. 

## Build

Use the makefile to build the protocol files. 

All in one command:

```bash
sudo make build
```

Or use the individual targets, depending on your needs:

```bash
sudo make setup  # install protoc, the protobuf compiler from the distribution
make venv  # setup python to compile the python targets
make build-python
```