# Copyright (c) 2008-2009 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
"""
Code for tagging Spacewalk/Satellite packages.
"""

import re
import shutil

try:
    from shlex import quote
except ImportError:
    from pipes import quote

from tito.common import (error_out,
                         get_latest_tagged_version,
                         get_spec_version_and_release,
                         increase_version,
                         reset_release,
                         increase_zstream,
                         info_out)
from tito.tagger.main import VersionTagger
from subprocess import check_output, check_call
import os

VERSION_RE = re.compile(r"^\d+(\.\d+)+$")


class NutVersionTagger(VersionTagger):

    def get_submodule_version(self):
        # NUT's own version helper: <last release>.<commits since that release>,
        # e.g. 2.8.5.1602; trunk is pinned to HEAD so the result only depends on
        # the submodule commit, not on which local/remote branches exist.
        env = dict(os.environ, NUT_VERSION_QUERY="VER50", NUT_VERSION_GIT_TRUNK="HEAD")
        version = check_output(["tools/gitlog2version.sh"], text=True, cwd="nut", env=env).strip()

        if not VERSION_RE.match(version):
            error_out(f"Unexpected NUT version {version!r} from nut/tools/gitlog2version.sh!")

        return version

    def _bump_version(self, release=False, zstream=False):
        """
        Bump up the package version in the spec file.

        Set release to True to bump the package release instead.

        Checks for the keep version option and if found, won't actually
        bump the version or release.
        """
        old_version = get_latest_tagged_version(self.project_name)
        if old_version is None:
            old_version = "untagged"
        if not self.keep_version:
            version_regex = re.compile(r"^(version:\s*)(.+)$", re.IGNORECASE)
            release_regex = re.compile(r"^(release:\s*)(.+)$", re.IGNORECASE)

            in_f = open(self.spec_file, 'r')
            out_f = open(self.spec_file + ".new", 'w')

            for line in in_f.readlines():
                version_match = re.match(version_regex, line)
                release_match = re.match(release_regex, line)

                if version_match and not zstream and not release:
                    current_version = version_match.group(2)
                    if hasattr(self, '_use_version'):
                        updated_content = self._use_version
                    else:
                        updated_content = self.get_submodule_version()

                    line = "".join([version_match.group(1), updated_content, "\n"])

                elif release_match:
                    current_release = release_match.group(2)
                    if hasattr(self, '_use_release'):
                        updated_content = self._use_release
                    elif release:
                        updated_content = increase_version(current_release)
                    elif zstream:
                        updated_content = increase_zstream(current_release)
                    else:
                        updated_content = reset_release(current_release)

                    line = "".join([release_match.group(1), updated_content, "\n"])

                out_f.write(line)

            in_f.close()
            out_f.close()
            shutil.move(self.spec_file + ".new", self.spec_file)

        new_version = get_spec_version_and_release(self.full_project_dir,
                                                   self.spec_file_name)
        if new_version.strip() == "":
            msg = "Error getting bumped package version, try: \n"
            msg = msg + "  'rpm -q --specfile %s'" % self.spec_file
            error_out(msg)
        info_out("Tagging new version of %s: %s -> %s" % (self.project_name,
                                                          old_version, new_version))

        return new_version
