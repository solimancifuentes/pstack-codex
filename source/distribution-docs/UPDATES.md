# Releases, updates, and rollback

## Starting point

`v0.1.0` is the first supported release. It is the only release and version tag
currently available. There is no earlier public version to update from or roll
back to.

If you already use v0.1.0, keep your installation. No update, migration, or
rollback is needed. For a new installation, follow the [README](README.md).

This repository is a custom GitHub marketplace. Installation does not require
a listing in OpenAI's public Plugins Directory.

## Prepared update to port 0.2.0

The development checkout includes upstream pstack 0.15.27 and 55 skills. It adds
`create-formal-verification-skill` and revised engineering guidance. The Codex
and Dots runtime adapters, external preferences, and explicit invocation rules
remain in place. See the [update record](verification/upstream-0.15.27.md).

Port 0.2.0 is unpublished. The installation commands below still select v0.1.0.
Do not use an uncreated version tag. Actual installation, update, rollback, and
representative workflow checks are required before publishing a new port release.

## Future updates

When a new release is published:

1. Read its release notes and installation instructions.
2. Record your installed plugin version and marketplace ref.
3. Select the new published tag explicitly, then verify the installed version
   and run a representative workflow in a new chat.

The README pins `v0.1.0`. Running
`codex plugin marketplace upgrade pstack-codex` refreshes the registered ref;
it does not advance a pinned tag to a newer release. A marketplace registered
with `--ref main` follows that moving branch instead.

Use `codex plugin list --json` to inspect the installed version and marketplace.
Future release notes will give the commands needed to change the selected tag.
Use the marketplace identity reported by your installation, and keep one enabled
copy of pstack.

User preferences remain outside the package at
`~/.codex/pstack-codex/preferences.json`. Preserve that file when changing a
release. Keep credentials and project work outside the installed cache.

## Future rollback

Rollback becomes relevant after another release exists. At that point, a user
running a newer release can return to a retained, supported tag such as
`v0.1.0`, following the instructions supplied with that release.

There is no supported downgrade target before v0.1.0. Internal development
snapshots and lifecycle-test receipts are not public rollback releases.

Verify the selected package and a representative workflow after any future
rollback. Do not edit installed cache files or overwrite preferences to make a
version change succeed.

## Maintainer releases

Review changes from the original pstack repository at an exact commit, then
verify the adapted package and its actual installation. Bump the port's version,
build the shared payload, and publish its tag and ZIP after the checks pass.

For the next release, verify an update from v0.1.0 and a rollback to v0.1.0
before publication. Retain the v0.1.0 tag and release as that baseline. Keep
subsequent supported tags and publish their tested update and rollback paths.

GitHub releases and OpenAI's public Plugins Directory are separate distribution
paths. A future directory publication requires its own package review; a GitHub
release does not update a directory package.
