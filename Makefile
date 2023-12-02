.PHONY: help setup run-develop build-docker clean

.DEFAULT: help
help:
	@echo "make setup"
	@echo "       setup your environment"
	@echo "make run-develop"
	@echo "       run the tira server"
	@echo "make tests"
	@echo "       run all tests (automatically done in Github Actions on each commit)"
	@echo "make vite-build"
	@echo "       build and test the frontnend client code"
	@echo "make clean"
	@echo "       clean the environment"


setup: 
	@cd application && make setup

run-develop: 
	@cd application && make run-develop

tests:
	@cd application && make tests

vite-build:
	@cd application && make vite-build

clean: 
	@cd application && make clean

