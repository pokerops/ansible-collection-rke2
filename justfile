set allow-duplicate-variables := true

import '.devbox/virtenv/pokerops.ansible-utils.molecule/justfile'

MOLECULE_REVISION := `command git rev-parse --abbrev-ref HEAD`
MOLECULE_SCENARIO := 'install'

build-check: requirements && version-check
  echo ${UV} --directory . run rke2 build
  ${UV} --directory . run rke2 build

update:
  echo ${UV} --directory . run rke2 update
  ${UV} --directory . run rke2 update
