#!/bin/bash -ex

version=$1
changes=$(git log $(git describe --tags --abbrev=0)..HEAD --no-merges --format="- %s")

echo "__version__ = '${version}'" > zyppkeys/version.py
osc vc -m "Version ${version}\n${changes}" zyppkeys.changes
vi zyppkeys.changes
git commit zyppkeys/version.py zyppkeys.changes -m "Version ${version}"
git tag "v${version}"
read -p "Push now? "
git push
git push --tags
gh release create "v${version}"  --generate-notes

read -p "Update RPM? "
cd ~/devel/obs/zypp:plugins/zypper-keys-plugin
osc up
sed -i -e "s/^\(Version: *\)[^ ]*$/\1${version}/" zypper-keys.spec
osc vc -m "Version ${version}\n${changes}"
vi zypper-keys.changes
osc rm zyppkeys-*.tar.gz
osc service dr
osc add zyppkeys-*.tar.gz
osc st
osc diff|bat

read -p "Submit RPM? "
osc ci
#osc sr
