# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from pants.backend.python.pants_requirement import PantsRequirement
from pants.backend.python.python_artifact import PythonArtifact
from pants.backend.python.python_requirements import PythonRequirements
from pants.backend.python.rules import (
    download_pex_bin,
    inject_init,
    pex,
    pex_from_target_closure,
    prepare_chrooted_python_sources,
    pytest_coverage,
    pytest_runner,
    python_create_binary,
    repl,
    run_setup_py,
)
from pants.backend.python.subsystems import python_native_code, subprocess_environment
from pants.backend.python.targets.python_app import PythonApp
from pants.backend.python.targets.python_binary import PythonBinary
from pants.backend.python.targets.python_distribution import PythonDistribution
from pants.backend.python.targets.python_library import PythonLibrary
from pants.backend.python.targets.python_requirement_library import PythonRequirementLibrary
from pants.backend.python.targets.python_requirements_file import PythonRequirementsFile
from pants.backend.python.targets.python_tests import PythonTests
from pants.backend.python.targets.unpacked_whls import UnpackedWheels
from pants.backend.python.tasks.build_local_python_distributions import (
    BuildLocalPythonDistributions,
)
from pants.backend.python.tasks.gather_sources import GatherSources
from pants.backend.python.tasks.local_python_distribution_artifact import (
    LocalPythonDistributionArtifact,
)
from pants.backend.python.tasks.pytest_prep import PytestPrep
from pants.backend.python.tasks.pytest_run import PytestRun
from pants.backend.python.tasks.python_binary_create import PythonBinaryCreate
from pants.backend.python.tasks.python_bundle import PythonBundle
from pants.backend.python.tasks.python_repl import PythonRepl
from pants.backend.python.tasks.python_run import PythonRun
from pants.backend.python.tasks.resolve_requirements import ResolveRequirements
from pants.backend.python.tasks.select_interpreter import SelectInterpreter
from pants.backend.python.tasks.setup_py import SetupPy
from pants.backend.python.tasks.unpack_wheels import UnpackWheels
from pants.build_graph.build_file_aliases import BuildFileAliases
from pants.build_graph.resources import Resources
from pants.goal.task_registrar import TaskRegistrar as task
from pants.python.pex_build_util import PexBuilderWrapper
from pants.python.python_requirement import PythonRequirement


def global_subsystems():
    return {
        python_native_code.PythonNativeCode,
        subprocess_environment.SubprocessEnvironment,
        PexBuilderWrapper.Factory,
    }


def build_file_aliases():
    return BuildFileAliases(
        targets={
            PythonApp.alias(): PythonApp,
            PythonBinary.alias(): PythonBinary,
            PythonLibrary.alias(): PythonLibrary,
            PythonTests.alias(): PythonTests,
            PythonDistribution.alias(): PythonDistribution,
            "python_requirement_library": PythonRequirementLibrary,
            PythonRequirementsFile.alias(): PythonRequirementsFile,
            Resources.alias(): Resources,
            UnpackedWheels.alias(): UnpackedWheels,
        },
        objects={
            "python_requirement": PythonRequirement,
            "python_artifact": PythonArtifact,
            "setup_py": PythonArtifact,
        },
        context_aware_object_factories={
            "python_requirements": PythonRequirements,
            PantsRequirement.alias: PantsRequirement,
        },
    )


def build_file_aliases2():
    return BuildFileAliases(
        objects={"python_requirement": PythonRequirement, "setup_py": PythonArtifact,},
        context_aware_object_factories={"python_requirements": PythonRequirements,},
    )


def register_goals():
    task(name="interpreter", action=SelectInterpreter).install("pyprep")
    task(name="build-local-dists", action=BuildLocalPythonDistributions).install("pyprep")
    task(name="requirements", action=ResolveRequirements).install("pyprep")
    task(name="sources", action=GatherSources).install("pyprep")
    task(name="py", action=PythonRun).install("run")
    task(name="pytest-prep", action=PytestPrep).install("test")
    task(name="pytest", action=PytestRun).install("test")
    task(name="py", action=PythonRepl).install("repl")
    task(name="setup-py", action=SetupPy).install()
    task(name="py", action=PythonBinaryCreate).install("binary")
    task(name="py-wheels", action=LocalPythonDistributionArtifact).install("binary")
    task(name="py", action=PythonBundle).install("bundle")
    task(name="unpack-wheels", action=UnpackWheels).install()


def rules():
    return (
        *download_pex_bin.rules(),
        *inject_init.rules(),
        *prepare_chrooted_python_sources.rules(),
        *pex.rules(),
        *pex_from_target_closure.rules(),
        *pytest_coverage.rules(),
        *pytest_runner.rules(),
        *python_create_binary.rules(),
        *python_native_code.rules(),
        *repl.rules(),
        *run_setup_py.rules(),
        *subprocess_environment.rules(),
    )
