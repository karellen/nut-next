# COPR nut-next Repository

This is a COPR repository for the Network UPS Tools (NUT) trunk builds.

The packages are built in the [karellen/nut-next](https://copr.fedorainfracloud.org/coprs/karellen/nut-next/)
COPR project from the [NUT](https://github.com/networkupstools/nut) `master` branch.

## Installation

```
dnf copr enable karellen/nut-next
dnf install nut-next nut-next-client --allowerasing
```

Each `nut-next` package conflicts with and provides the corresponding distribution `nut` package (`nut`,
`nut-client`, `nut-cgi`, `nut-xml`, `nut-devel` and, on Fedora only, `nut-monitor`), so it replaces it. On EL the
dependencies come from EPEL, which must be enabled.

## How It Works

* The `nut` directory is a git submodule tracking upstream `master`.
* Every 6 hours the [update workflow](.github/workflows/update.yml) checks upstream for new commits. When there are
  any it bumps the submodule, regenerates `VERSION_DEFAULT` (the upstream `tools/gitlog2version.sh` output, so that
  the build knows the git revision without a git checkout), and runs `tito tag` followed by `git push --follow-tags`.
* COPR rebuilds the package from the pushed tag, producing the SRPM with tito.
* The package version is NUT's own development version, `<last release>.<commits since that release>`,
  e.g. `2.8.5.1602`.

## Relationship to Fedora

The packaging is the Fedora [nut](https://src.fedoraproject.org/rpms/nut) dist-git packaging, adapted to build from
the upstream trunk. This repository shares its git history with the Fedora dist-git repository and is periodically
synchronized with it by merging the Fedora branch.

Differences from Fedora:

* Fedora's backport patches and patches that upstream has since absorbed are not carried; the remaining patches
  (`rmpidf`, `rhinoname`) are rebased onto the trunk.
* The build runs upstream `autogen.sh` and builds the man pages, which a git checkout does not ship pre-generated.
* The same spec also builds for EL8, EL9 and EL10 with EPEL. There the NUT-Monitor GUI (`nut-next-monitor`) is not
  built, as EL does not provide `python3-pyqt6`; EL8 also lacks the I2C drivers (no `libi2c-devel`); and the `nut`
  user is created in `%pre`, because rpm on EL does not create sysusers.d users before installing files.
