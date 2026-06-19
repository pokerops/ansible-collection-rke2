set allow-duplicate-variables := true

import '.devbox/virtenv/pokerops.ansible-utils.molecule/justfile'

MOLECULE_REVISION := `command git rev-parse --abbrev-ref HEAD`
MOLECULE_SCENARIO := 'components'

build-check: requirements && version-check
  ${UV} --directory . run rke2 build

update:
  ${UV} --directory . run rke2 update
