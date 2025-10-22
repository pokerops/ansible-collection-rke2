include .devbox/virtenv/pokerops.ansible-utils.molecule/Makefile

deploy:
	uv run ansible-galaxy collection install \
		--force-with-deps .

build: requirements
	@uv run rke2 build
	@git status --porcelain | wc -l | grep -q '^0$$' || (echo "Uncommitted build detected, please run build stage and commit changes" && exit 1)

update:
	@uv run rke2 update

local:
	uv run ansible-galaxy collection install --force .
