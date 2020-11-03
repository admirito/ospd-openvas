# -*- coding: utf-8 -*-
# Copyright (C) 2014-2020 Greenbone Networks GmbH
#
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import unittest

from pathlib import Path
from collections import OrderedDict
from unittest.mock import patch, MagicMock

from ospd_openvas.notus.metadata import (
    NotusMetadataHandler,
    EXPECTED_FIELD_NAMES_LIST,
    METADATA_DIRECTORY_NAME,
)

from tests.helper import assert_called_once, assert_called


class LockFileTestCase(unittest.TestCase):
    @patch('ospd_openvas.nvticache.NVTICache')
    def setUp(self, MockNvti):
        self.nvti = MockNvti()

    @patch('ospd_openvas.notus.metadata.Openvas')
    def test_set_openvas_settings(self, MockOpenvas):
        openvas = MockOpenvas()
        openvas.get_settings.return_value = {'nasl_no_signature_check': 0}

        notus = NotusMetadataHandler()
        no_signature_check = notus.openvas_setting.get(
            "nasl_no_signature_check"
        )

        self.assertEqual(no_signature_check, 0)

    @patch('ospd_openvas.notus.metadata.Openvas')
    def test_metadata_path(self, MockOpenvas):
        openvas = MockOpenvas()
        openvas.get_settings.return_value = {'plugins_folder': './tests/notus'}
        notus = NotusMetadataHandler()

        self.assertIsNone(notus._metadata_path)
        self.assertEqual(
            notus.metadata_path, f'./tests/notus/{METADATA_DIRECTORY_NAME}/'
        )
        self.assertEqual(
            notus._metadata_path, f'./tests/notus/{METADATA_DIRECTORY_NAME}/'
        )

    def test_is_checksum_correct_check_disable(self):
        notus = NotusMetadataHandler()
        notus._openvas_settings_dict = {'nasl_no_signature_check': 1}

        self.assertTrue(notus.is_checksum_correct(Path("foo")))

    def test_is_checksum_correct_enabled_false(self):
        notus = NotusMetadataHandler(nvti=self.nvti)
        notus.nvti.get_file_checksum.return_value = "abc123"
        notus._openvas_settings_dict = {'nasl_no_signature_check': 0}

        self.assertFalse(
            notus.is_checksum_correct(Path("./tests/notus/example.csv"))
        )

    def test_is_checksum_correct_enabled_true(self):
        notus = NotusMetadataHandler(nvti=self.nvti)
        notus.nvti.get_file_checksum.return_value = (
            "aafbaf3fac1c64a4006a02ed4657b975f47b07cd2915c8186ff1739ac6216e72"
        )
        notus._openvas_settings_dict = {'nasl_no_signature_check': 0}

        self.assertTrue(
            notus.is_checksum_correct(Path("./tests/notus/example.csv"))
        )

    def test_check_advisory_dict(self):
        advisory_dict = OrderedDict(
            [
                ('OID', '1.3.6.1.4.1.25623.1.1.2.2020.1234'),
                (
                    'TITLE',
                    'VendorOS: Security Advisory for git (VendorOS-2020-1234)',
                ),
                ('CREATION_DATE', '1600269468'),
                ('LAST_MODIFICATION', '1601380531'),
                ('SOURCE_PKGS', "['git']"),
                ('ADVISORY_ID', 'VendorOS-2020-1234'),
                ('CVSS_BASE_VECTOR', 'AV:N/AC:L/Au:N/C:C/I:C/A:C'),
                ('CVSS_BASE', '10.0'),
                ('ADVISORY_XREF', 'https://example.com'),
                ('DESCRIPTION', 'The remote host is missing an update.'),
                ('INSIGHT', 'buffer overflow'),
                ('AFFECTED', "'p1' package(s) on VendorOS V2.0SP1"),
                ('CVE_LIST', "['CVE-2020-1234']"),
                (
                    'BINARY_PACKAGES_FOR_RELEASES',
                    "{'VendorOS V2.0SP1': ['p1-1.1']}",
                ),
                ('XREFS', '[]'),
            ]
        )

        notus = NotusMetadataHandler()
        self.assertTrue(notus._check_advisory_dict(advisory_dict))

    def test_check_advisory_dict_no_value(self):
        advisory_dict = OrderedDict(
            [
                ('OID', '1.3.6.1.4.1.25623.1.1.2.2020.1234'),
                (
                    'TITLE',
                    'VendorOS: Security Advisory for git (VendorOS-2020-1234)',
                ),
                ('CREATION_DATE', None),
                ('LAST_MODIFICATION', '1601380531'),
                ('SOURCE_PKGS', "['git']"),
                ('ADVISORY_ID', 'VendorOS-2020-1234'),
                ('CVSS_BASE_VECTOR', 'AV:N/AC:L/Au:N/C:C/I:C/A:C'),
                ('CVSS_BASE', '10.0'),
                ('ADVISORY_XREF', 'https://example.com'),
                ('DESCRIPTION', 'The remote host is missing an update.'),
                ('INSIGHT', 'buffer overflow'),
                ('AFFECTED', "'p1' package(s) on VendorOS V2.0SP1"),
                ('CVE_LIST', "['CVE-2020-1234']"),
                (
                    'BINARY_PACKAGES_FOR_RELEASES',
                    "{'VendorOS V2.0SP1': ['p1-1.1']}",
                ),
                ('XREFS', '[]'),
            ]
        )

        notus = NotusMetadataHandler()
        self.assertFalse(notus._check_advisory_dict(advisory_dict))

    def test_check_advisory_dict_no_package(self):
        advisory_dict = OrderedDict(
            [
                ('OID', '1.3.6.1.4.1.25623.1.1.2.2020.1234'),
                (
                    'TITLE',
                    'VendorOS: Security Advisory for git (VendorOS-2020-1234)',
                ),
                ('CREATION_DATE', '1600269468'),
                ('LAST_MODIFICATION', '1601380531'),
                ('SOURCE_PKGS', "[]"),
                ('ADVISORY_ID', 'VendorOS-2020-1234'),
                ('CVSS_BASE_VECTOR', 'AV:N/AC:L/Au:N/C:C/I:C/A:C'),
                ('CVSS_BASE', '10.0'),
                ('ADVISORY_XREF', 'https://example.com'),
                ('DESCRIPTION', 'The remote host is missing an update.'),
                ('INSIGHT', 'buffer overflow'),
                ('AFFECTED', "'p1' package(s) on VendorOS V2.0SP1"),
                ('CVE_LIST', "['CVE-2020-1234']"),
                (
                    'BINARY_PACKAGES_FOR_RELEASES',
                    "{'VendorOS V2.0SP1': ['p1-1.1']}",
                ),
                ('XREFS', '[]'),
            ]
        )

        notus = NotusMetadataHandler()
        self.assertFalse(notus._check_advisory_dict(advisory_dict))

    def test_check_advisory_dict_valerr(self):
        advisory_dict = OrderedDict(
            [
                ('OID', '1.3.6.1.4.1.25623.1.1.2.2020.1234'),
                (
                    'TITLE',
                    'VendorOS: Security Advisory for git (VendorOS-2020-1234)',
                ),
                ('CREATION_DATE', '1600269468'),
                ('LAST_MODIFICATION', '1601380531'),
                ('SOURCE_PKGS', "a"),
                ('ADVISORY_ID', 'VendorOS-2020-1234'),
                ('CVSS_BASE_VECTOR', 'AV:N/AC:L/Au:N/C:C/I:C/A:C'),
                ('CVSS_BASE', '10.0'),
                ('ADVISORY_XREF', 'https://example.com'),
                ('DESCRIPTION', 'The remote host is missing an update.'),
                ('INSIGHT', 'buffer overflow'),
                ('AFFECTED', "'p1' package(s) on VendorOS V2.0SP1"),
                ('CVE_LIST', "['CVE-2020-1234']"),
                (
                    'BINARY_PACKAGES_FOR_RELEASES',
                    "{'VendorOS V2.0SP1': ['p1-1.1']}",
                ),
                ('XREFS', '[]'),
            ]
        )

        notus = NotusMetadataHandler()
        self.assertFalse(notus._check_advisory_dict(advisory_dict))

    def test_format_xrefs(self):
        notus = NotusMetadataHandler()
        ret = notus._format_xrefs(
            "https://example.com", ["www.foo.net", "www.bar.net"]
        )

        self.assertEqual(
            ret, "URL:https://example.com, URL:www.foo.net, URL:www.bar.net"
        )

    def test_check_field_names_lsc(self):
        notus = NotusMetadataHandler()
        field_names_list = [
            "OID",
            "TITLE",
            "CREATION_DATE",
            "LAST_MODIFICATION",
            "SOURCE_PKGS",
            "ADVISORY_ID",
            "CVSS_BASE_VECTOR",
            "CVSS_BASE",
            "ADVISORY_XREF",
            "DESCRIPTION",
            "INSIGHT",
            "AFFECTED",
            "CVE_LIST",
            "BINARY_PACKAGES_FOR_RELEASES",
            "XREFS",
        ]

        self.assertTrue(notus._check_field_names_lsc(field_names_list))

    def test_check_field_names_lsc_unordered(self):
        notus = NotusMetadataHandler()
        field_names_list = [
            "TITLE",
            "OID",
            "CREATION_DATE",
            "LAST_MODIFICATION",
            "SOURCE_PKGS",
            "ADVISORY_ID",
            "CVSS_BASE_VECTOR",
            "CVSS_BASE",
            "ADVISORY_XREF",
            "DESCRIPTION",
            "INSIGHT",
            "AFFECTED",
            "CVE_LIST",
            "BINARY_PACKAGES_FOR_RELEASES",
            "XREFS",
        ]

        self.assertFalse(notus._check_field_names_lsc(field_names_list))

    def test_check_field_names_lsc_missing(self):
        notus = NotusMetadataHandler()
        field_names_list = [
            "OID",
            "CREATION_DATE",
            "LAST_MODIFICATION",
            "SOURCE_PKGS",
            "ADVISORY_ID",
            "CVSS_BASE_VECTOR",
            "CVSS_BASE",
            "ADVISORY_XREF",
            "DESCRIPTION",
            "INSIGHT",
            "AFFECTED",
            "CVE_LIST",
            "BINARY_PACKAGES_FOR_RELEASES",
            "XREFS",
        ]

        self.assertFalse(notus._check_field_names_lsc(field_names_list))

    def test_get_csv_filepath(self):
        path = Path("./tests/notus/example.csv").resolve()

        notus = NotusMetadataHandler(metadata_path="./tests/notus/")
        ret = notus._get_csv_filepaths()

        self.assertEqual(ret, [path])
