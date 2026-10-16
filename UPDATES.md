# Update and rollback

User overrides remain outside the package. Record the current plugin version
and marketplace ref before updating. Keep worktree changes and credentials
outside the installed cache.

## Git marketplace

```sh
codex plugin marketplace upgrade pstack-codex
codex plugin add pstack-codex@pstack-codex --json
codex plugin list --available --json
```

Marketplace upgrade refreshes the catalog. Confirm the installed version and
path from the plugin result; a catalog refresh alone does not prove installed
bytes changed. If the client retains a stale package, remove and add this plugin
through native commands, then verify the resulting version. Keep your external
profile file. Never edit installed cache files as an update method.

To select an exact release or return to a prior tag:

```sh
codex plugin marketplace remove pstack-codex
codex plugin marketplace add solimancifuentes/pstack-codex --ref v0.2.2
codex plugin remove pstack-codex@pstack-codex --json
codex plugin add pstack-codex@pstack-codex --json
```

Replace `v0.2.2` with the intended existing tag. Marketplace removal changes the
source registration; plugin removal changes installed registration and cache.
Use the exact marketplace name to avoid changing unrelated plugins. Restart or
refresh Desktop and start a new chat. Check native skill discovery and run a
representative workflow after the selected version is installed.

## Existing personal managed installation

An earlier local installation may use `pstack-codex@personal` and the separate
`pstack-codex` manager. Its owned registration, source releases, migration
backups, and preferences are distinct from the public marketplace. Do not enable
two copies of this plugin for ordinary use.

That manager supports `status`, `verify`, `install --release ... --dry-run`,
`install --release ... --yes`, and `rollback --to RELEASE_ID --dry-run/--yes`.
Its `rollback --to before-install --yes` restores recorded standalone originals.
New ordinary installs do not consolidate standalone skills; the optional
`--migrate-standalone` flag requires the audited originals during the first
managed install. Interrupted operations use `recover --dry-run`, then
`recover --yes` after reviewing the operation.

Shared v0.2+ releases preserve arbitrary live profile overrides. Legacy v0.1
releases embedded their build profile. A legacy rollback with incompatible
current overrides stops without overwriting the profile. Review that conflict
or select a shared release; do not replace preferences merely to force rollback.

## Maintainer upstream workflow

Fetch only the original repository, record its exact commit, review every
changed adapter context, and run source integrity, package, runtime, and native
installation checks. A changed source hash is a review gate, not a value to
replace blindly. Bump the port's SemVer, build one shared payload, export its
marketplace and plugin-only ZIP, and publish a tagged release after verification.

Public-directory skill changes require a new package upload and the applicable
review/publication process. GitHub releases do not silently update a published
directory package. Keep previous tags for rollback and document tested coverage.
