.PHONY: help frontend clean


.DEFAULT: help
help:
	@echo "make tests"
	@echo "       run all tests (automatically done in Github Actions on each commit)"
	@echo "make vite-build"
	@echo "       build and test the frontnend client code"
	@echo "make clean"
	@echo "       clean the environment"

frontend:
	make vite-build

vite-build:
	@cd ../frontend \
	&& yarn build

vite-build-light:
	@cd ../frontend \
	&& yarn build-light

vite-build-docker:
	docker run -v ${PWD}:/app --platform linux/amd64 --rm -ti -w /app/src/tira/frontend-vuetify --entrypoint yarn webis/tira-application:basis-0.0.95 build

vite-build-light-docker:
	docker run -v ${PWD}:/app --platform linux/amd64 --rm -ti -w /app/src/tira/frontend-vuetify --entrypoint yarn webis/tira-application:basis-0.0.95 build-light
