export

MOLECULE_REVISION ?= $(shell git rev-parse --abbrev-ref HEAD)
MOLECULE_SCENARIO ?= install

include ${MAKEFILE}

build-check: build
	@${UV_RUN} rke2 build
	@git status --porcelain | wc -l | grep -q '^0$$' || (echo "Uncommitted changes detected, please run build-check and commit changes" && exit 1)

update:
	@${UV_RUN} rke2 update
