.PHONY: all ${MAKECMDGOALS}

MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))

MOLECULE_SCENARIO ?= components
MOLECULE_REVISION ?= $$(git rev-parse --abbrev-ref HEAD)
DEBIAN_RELEASE ?= bookworm
UBUNTU_RELEASE ?= noble
EL_RELEASE ?= 9
DEBIAN_SHASUMS = https://cloud.debian.org/images/cloud/${DEBIAN_RELEASE}/latest/SHA512SUMS
DEBIAN_KVM_FILENAME = $$(curl -s ${DEBIAN_SHASUMS} | grep "generic-amd64.qcow2" | awk '{print $$2}')
DEBIAN_KVM_IMAGE = https://cloud.debian.org/images/cloud/${DEBIAN_RELEASE}/latest/${DEBIAN_KVM_FILENAME}
UBUNTU_KVM_IMAGE = https://cloud-images.ubuntu.com/${UBUNTU_RELEASE}/current/${UBUNTU_RELEASE}-server-cloudimg-amd64.img
ALMA_KVM_IMAGE = https://repo.almalinux.org/almalinux/${EL_RELEASE}/cloud/x86_64/images/AlmaLinux-${EL_RELEASE}-GenericCloud-latest.x86_64.qcow2
ROCKY_KVM_IMAGE = https://dl.rockylinux.org/pub/rocky/${EL_RELEASE}/images/x86_64/Rocky-${EL_RELEASE}-GenericCloud-Base.latest.x86_64.qcow2
MOLECULE_KVM_IMAGE := $(UBUNTU_KVM_IMAGE)
GALAXY_API_KEY ?=
GITHUB_REPOSITORY ?= $$(git config --get remote.origin.url | cut -d':' -f 2 | cut -d. -f 1)
GITHUB_ORG = $$(echo ${GITHUB_REPOSITORY} | cut -d'/' -f 1)
GITHUB_REPO = $$(echo ${GITHUB_REPOSITORY} | cut -d'/' -f 2)
REQUIREMENTS = requirements.yml
ROLE_DIR = roles
ROLE_FILE = roles.yml
COLLECTION_NAMESPACE = $$(yq -r '.namespace' < galaxy.yml)
COLLECTION_NAME = $$(yq -r '.name' < galaxy.yml)
COLLECTION_VERSION = $$(yq -r '.version' < galaxy.yml)

LOGIN_ARGS ?=

all: install version lint test

ubuntu:
	MOLECULE_KVM_IMAGE=${UBUNTU_KVM_IMAGE} \
	MOLECULE_OUTPUT_DIR=${MOECULE_OUTPUT_DIR} \
	MOLECULE_SCENARIO=${MOLECULE_SCENARIO} \
		make dependency create prepare

noble ubuntu2404:
	make ubuntu UBUNTU_RELEASE=noble MOLECULE_SCENARIO=${MOLECULE_SCENARIO}

jammy ubuntu2204:
	make ubuntu UBUNTU_RELEASE=jammy MOLECULE_SCENARIO=${MOLECULE_SCENARIO}

focal ubuntu2004:
	make ubuntu UBUNTU_RELEASE=focal MOLECULE_SCENARIO=${MOLECULE_SCENARIO}

debian:
	make dependency create prepare \
		MOLECULE_KVM_IMAGE=${DEBIAN_KVM_IMAGE} \
		MOLECULE_OUTPUT_DIR=${MOECULE_OUTPUT_DIR} \
		MOLECULE_SCENARIO=${MOLECULE_SCENARIO}

bookworm debian12:
	make debian MOLECULE_SCENARIO=${MOLECULE_SCENARIO} DEBIAN_RELEASE=bookworm

alma:
	make dependency create prepare \
		MOLECULE_KVM_IMAGE=${ALMA_KVM_IMAGE} \
		MOLECULE_OUTPUT_DIR=${MOECULE_OUTPUT_DIR} \
		MOLECULE_SCENARIO=${MOLECULE_SCENARIO}

alma9:
	make alma EL_RELEASE=9 MOLECULE_SCENARIO=${MOLECULE_SCENARIO}

rocky:
	make dependency create prepare \
		MOLECULE_KVM_IMAGE=${ROCKY_KVM_IMAGE} \
		MOLECULE_OUTPUT_DIR=${MOECULE_OUTPUT_DIR} \
		MOLECULE_SCENARIO=${MOLECULE_SCENARIO}

rocky9:
	make rocky EL_RELEASE=9 MOLECULE_SCENARIO=${MOLECULE_SCENARIO}

test: lint
	ANSIBLE_COLLECTIONS_PATH=$(MAKEFILE_DIR) \
	MOLECULE_OUTPUT_DIR=${MOECULE_OUTPUT_DIR} \
	MOLECULE_REVISION=${MOLECULE_REVISION} \
	MOLECULE_KVM_IMAGE=${MOLECULE_KVM_IMAGE} \
		uv run dotenv molecule test -s ${MOLECULE_SCENARIO}

install:
	@uv sync

lint: install
	uv run yamllint . -c .yamllint
	ANSIBLE_COLLECTIONS_PATH=$(MAKEFILE_DIR) \
	uv run ansible-lint -p playbooks/ --exclude ".ansible/*"

requirements: install
	@python --version
	@uv run ansible-galaxy role install \
		--force --no-deps \
		--roles-path ${ROLE_DIR} \
		--role-file ${ROLE_FILE}
	ANSIBLE_COLLECTIONS_PATH=$(MAKEFILE_DIR) \
	uv run ansible-galaxy collection install \
		--force-with-deps .
	@find ./ -name "*.ymle*" -delete

build: requirements
	@uv run rke2 build
	@git status --porcelain | wc -l | grep -q '^0$$' || (echo "Uncommitted build detected, please run build stage and commit changes" && exit 1)

update:
	@uv run rke2 update

ifeq (login,$(firstword $(MAKECMDGOALS)))
    LOGIN_ARGS := $(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))
    $(eval $(subst $(space),,$(wordlist 2,$(words $(MAKECMDGOALS)),$(MAKECMDGOALS))):;@:)
endif

dependency create prepare converge idempotence side-effect verify destroy cleanup reset list login:
	rm -rf ansible_collections/ 
	ANSIBLE_COLLECTIONS_PATH=$(MAKEFILE_DIR) \
	MOLECULE_REVISION=${MOLECULE_REVISION} \
	MOLECULE_KVM_IMAGE=${MOLECULE_KVM_IMAGE} \
	MOLECULE_OUTPUT_DIR=${MOECULE_OUTPUT_DIR} \
	uv run dotenv molecule $@ -s ${MOLECULE_SCENARIO} ${LOGIN_ARGS}

clean: destroy reset
	@uv env remove $$(which python) >/dev/null 2>&1 || exit 0

publish: build
	uv run ansible-galaxy collection publish --api-key ${GALAXY_API_KEY} \
		"${COLLECTION_NAMESPACE}-${COLLECTION_NAME}-${COLLECTION_VERSION}.tar.gz"

local:
	uv run ansible-galaxy collection install --force .

version:
	@uv run molecule --version

debug: version
	@uv export --dev --without-hashes || exit 0

