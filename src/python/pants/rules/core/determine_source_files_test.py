# Copyright 2020 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from pathlib import PurePath
from typing import Iterable, List, NamedTuple, Optional
from unittest.mock import Mock

from pants.base.specs import (
    AscendantAddresses,
    DescendantAddresses,
    FilesystemLiteralSpec,
    FilesystemResolvedGlobSpec,
    OriginSpec,
    SiblingAddresses,
    SingleAddress,
)
from pants.build_graph.address import Address
from pants.build_graph.files import Files
from pants.engine.legacy.structs import TargetAdaptor, TargetAdaptorWithOrigin
from pants.engine.rules import RootRule
from pants.engine.selectors import Params
from pants.rules.core.determine_source_files import (
    AllSourceFilesRequest,
    SourceFiles,
    SpecifiedSourceFilesRequest,
)
from pants.rules.core.determine_source_files import rules as determine_source_files_rules
from pants.rules.core.strip_source_roots import rules as strip_source_roots_rules
from pants.testutil.option.util import create_options_bootstrapper
from pants.testutil.test_base import TestBase


class TargetSources(NamedTuple):
    source_root: str
    source_files: List[str]

    @property
    def source_file_absolute_paths(self) -> List[str]:
        return [PurePath(self.source_root, name).as_posix() for name in self.source_files]


class DetermineSourceFilesTest(TestBase):

    SOURCES1 = TargetSources("src/python", ["s1.py", "s2.py", "s3.py"])
    SOURCES2 = TargetSources("tests/python", ["t1.py", "t2.java"])
    SOURCES3 = TargetSources("src/java", ["j1.java", "j2.java"])

    @classmethod
    def rules(cls):
        return (
            *super().rules(),
            *determine_source_files_rules(),
            *strip_source_roots_rules(),
            RootRule(SpecifiedSourceFilesRequest),
        )

    def mock_target(
        self,
        sources: TargetSources,
        *,
        origin: Optional[OriginSpec] = None,
        include_sources: bool = True,
        type_alias: Optional[str] = None,
    ) -> TargetAdaptorWithOrigin:
        sources_field = Mock()
        sources_field.snapshot = self.make_snapshot(
            {fp: "" for fp in (sources.source_file_absolute_paths if include_sources else [])}
        )
        adaptor = TargetAdaptor(
            address=Address.parse(f"{sources.source_root}:lib"),
            type_alias=type_alias,
            sources=sources_field,
        )
        if origin is None:
            origin = SiblingAddresses(sources.source_root)
        return TargetAdaptorWithOrigin(adaptor, origin)

    def get_all_source_files(
        self,
        adaptors_with_origins: Iterable[TargetAdaptorWithOrigin],
        *,
        strip_source_roots: bool = False,
    ) -> List[str]:
        request = AllSourceFilesRequest(
            (adaptor_with_origin.adaptor for adaptor_with_origin in adaptors_with_origins),
            strip_source_roots=strip_source_roots,
        )
        result = self.request_single_product(
            SourceFiles, Params(request, create_options_bootstrapper())
        )
        return sorted(result.snapshot.files)

    def get_specified_source_files(
        self,
        adaptors_with_origins: Iterable[TargetAdaptorWithOrigin],
        *,
        strip_source_roots: bool = False,
    ) -> List[str]:
        request = SpecifiedSourceFilesRequest(
            adaptors_with_origins, strip_source_roots=strip_source_roots,
        )
        result = self.request_single_product(
            SourceFiles, Params(request, create_options_bootstrapper())
        )
        return sorted(result.snapshot.files)

    def test_address_specs(self) -> None:
        target1 = self.mock_target(
            self.SOURCES1, origin=SingleAddress(directory=self.SOURCES1.source_root, name="lib")
        )
        target2 = self.mock_target(
            self.SOURCES2, origin=SiblingAddresses(self.SOURCES2.source_root)
        )
        target3 = self.mock_target(
            self.SOURCES3, origin=DescendantAddresses(self.SOURCES3.source_root)
        )
        target4 = self.mock_target(
            self.SOURCES1, origin=AscendantAddresses(self.SOURCES1.source_root)
        )

        def assert_all_source_files_resolved(
            target: TargetAdaptorWithOrigin, sources: TargetSources
        ) -> None:
            expected = sources.source_file_absolute_paths
            assert self.get_all_source_files([target]) == expected
            assert self.get_specified_source_files([target]) == expected

        assert_all_source_files_resolved(target1, self.SOURCES1)
        assert_all_source_files_resolved(target2, self.SOURCES2)
        assert_all_source_files_resolved(target3, self.SOURCES3)
        assert_all_source_files_resolved(target4, self.SOURCES1)
        # NB: target1 and target4 refer to the same files. We should be able to handle this
        # gracefully.
        combined_targets = [target1, target2, target3, target4]
        combined_expected = sorted(
            [
                *self.SOURCES1.source_file_absolute_paths,
                *self.SOURCES2.source_file_absolute_paths,
                *self.SOURCES3.source_file_absolute_paths,
            ]
        )
        assert self.get_all_source_files(combined_targets) == combined_expected
        assert self.get_specified_source_files(combined_targets) == combined_expected

    def test_filesystem_specs(self) -> None:
        # Literal file arg.
        target1_all_sources = self.SOURCES1.source_file_absolute_paths
        target1_slice = slice(0, 1)
        target1 = self.mock_target(
            self.SOURCES1, origin=FilesystemLiteralSpec(target1_all_sources[0])
        )

        # Glob file arg that matches the entire target's `sources`.
        target2_all_sources = self.SOURCES2.source_file_absolute_paths
        target2_slice = slice(0, len(target2_all_sources))
        target2_origin = FilesystemResolvedGlobSpec(
            f"{self.SOURCES2.source_root}/*.py", files=tuple(target2_all_sources)
        )
        target2 = self.mock_target(self.SOURCES2, origin=target2_origin)

        # Glob file arg that only matches a subset of the target's `sources` _and_ includes resolved
        # files not owned by the target.
        target3_all_sources = self.SOURCES3.source_file_absolute_paths
        target3_slice = slice(0, 1)
        target3_origin = FilesystemResolvedGlobSpec(
            f"{self.SOURCES3.source_root}/*.java",
            files=tuple(
                PurePath(self.SOURCES3.source_root, name).as_posix()
                for name in [self.SOURCES3.source_files[0], "other_target.java", "j.tmp.java"]
            ),
        )
        target3 = self.mock_target(self.SOURCES3, origin=target3_origin)

        def assert_file_args_resolved(
            target: TargetAdaptorWithOrigin, all_sources: List[str], expected_slice: slice
        ) -> None:
            assert self.get_all_source_files([target]) == all_sources
            assert self.get_specified_source_files([target]) == all_sources[expected_slice]

        assert_file_args_resolved(target1, target1_all_sources, target1_slice)
        assert_file_args_resolved(target2, target2_all_sources, target2_slice)
        assert_file_args_resolved(target3, target3_all_sources, target3_slice)

        combined_targets = [target1, target2, target3]
        assert self.get_all_source_files(combined_targets) == sorted(
            [*target1_all_sources, *target2_all_sources, *target3_all_sources]
        )
        assert self.get_specified_source_files(combined_targets) == sorted(
            [
                *target1_all_sources[target1_slice],
                *target2_all_sources[target2_slice],
                *target3_all_sources[target3_slice],
            ]
        )

    def test_strip_source_roots(self) -> None:
        target1 = self.mock_target(self.SOURCES1)
        target2 = self.mock_target(self.SOURCES2)
        target3 = self.mock_target(self.SOURCES3)

        # We must be careful to not strip source roots for `files` targets.
        files_target = self.mock_target(self.SOURCES1, type_alias=Files.alias())
        files_expected = self.SOURCES1.source_file_absolute_paths

        def assert_source_roots_stripped(
            target: TargetAdaptorWithOrigin, sources: TargetSources
        ) -> None:
            expected = sources.source_files
            assert self.get_all_source_files([target], strip_source_roots=True) == expected
            assert self.get_specified_source_files([target], strip_source_roots=True) == expected

        assert_source_roots_stripped(target1, self.SOURCES1)
        assert_source_roots_stripped(target2, self.SOURCES2)
        assert_source_roots_stripped(target3, self.SOURCES3)

        assert self.get_all_source_files([files_target], strip_source_roots=True) == files_expected
        assert (
            self.get_specified_source_files([files_target], strip_source_roots=True)
            == files_expected
        )

        combined_targets = [target1, target2, target3, files_target]
        combined_expected = sorted(
            [
                *self.SOURCES1.source_files,
                *self.SOURCES2.source_files,
                *self.SOURCES3.source_files,
                *files_expected,
            ],
        )
        assert (
            self.get_all_source_files(combined_targets, strip_source_roots=True)
            == combined_expected
        )
        assert (
            self.get_specified_source_files(combined_targets, strip_source_roots=True)
            == combined_expected
        )

    def test_gracefully_handle_no_sources(self) -> None:
        target = self.mock_target(self.SOURCES1, include_sources=False)
        assert self.get_all_source_files([target]) == []
        assert self.get_specified_source_files([target]) == []
        assert self.get_all_source_files([target], strip_source_roots=True) == []
        assert self.get_specified_source_files([target], strip_source_roots=True) == []
