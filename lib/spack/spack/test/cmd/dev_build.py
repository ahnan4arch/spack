# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)
import pytest
import os
import pytest
import spack.spec
import spack.environment as ev
from spack.main import SpackCommand, SpackCommandError

dev_build = SpackCommand('dev-build')
install = SpackCommand('install')
env = SpackCommand('env')


def test_dev_build_basics(tmpdir, mock_packages, install_mockery):
    spec = spack.spec.Spec('dev-build-test-install@0.0.0').concretized()

    with tmpdir.as_cwd():
        with open(spec.package.filename, 'w') as f:
            f.write(spec.package.original_string)

        dev_build('dev-build-test-install@0.0.0')

    assert spec.package.filename in os.listdir(spec.prefix)
    with open(os.path.join(spec.prefix, spec.package.filename), 'r') as f:
        assert f.read() == spec.package.replacement_string


def test_dev_build_before(tmpdir, mock_packages, install_mockery):
    spec = spack.spec.Spec('dev-build-test-install@0.0.0').concretized()

    with tmpdir.as_cwd():
        with open(spec.package.filename, 'w') as f:
            f.write(spec.package.original_string)

        dev_build('-b', 'edit', 'dev-build-test-install@0.0.0')

        assert spec.package.filename in os.listdir(os.getcwd())
        with open(spec.package.filename, 'r') as f:
            assert f.read() == spec.package.original_string

    assert not os.path.exists(spec.prefix)


def test_dev_build_until(tmpdir, mock_packages, install_mockery):
    spec = spack.spec.Spec('dev-build-test-install@0.0.0').concretized()

    with tmpdir.as_cwd():
        with open(spec.package.filename, 'w') as f:
            f.write(spec.package.original_string)

        dev_build('-u', 'edit', 'dev-build-test-install@0.0.0')

        assert spec.package.filename in os.listdir(os.getcwd())
        with open(spec.package.filename, 'r') as f:
            assert f.read() == spec.package.replacement_string

    assert not os.path.exists(spec.prefix)


def test_dev_build_before_until(tmpdir, mock_packages, install_mockery):
    spec = spack.spec.Spec('dev-build-test-install@0.0.0').concretized()

    with tmpdir.as_cwd():
        with open(spec.package.filename, 'w') as f:
            f.write(spec.package.original_string)

        with pytest.raises(SystemExit):
            dev_build('-u', 'edit', '-b', 'edit',
                      'dev-build-test-install@0.0.0')

        with pytest.raises(SpackCommandError):
            dev_build('-u', 'phase_that_does_not_exist',
                      'dev-build-test-install@0.0.0')

        with pytest.raises(SpackCommandError):
            dev_build('-b', 'phase_that_does_not_exist',
                      'dev-build-test-install@0.0.0')


def test_dev_build_drop_in(tmpdir, mock_packages, monkeypatch,
                           install_mockery):
    def print_spack_cc(*args):
        # Eat arguments and print environment variable to test
        print(os.environ.get('CC', ''))
    monkeypatch.setattr(os, 'execvp', print_spack_cc)

    # `module unload cray-libsci` in test environment causes failure
    # It does not fail for actual installs
    # build_environment.py imports module directly, so we monkeypatch it there
    # rather than in module_cmd
    def module(*args):
        pass
    monkeypatch.setattr(spack.build_environment, 'module', module)

    output = dev_build('-b', 'edit', '--drop-in', 'sh',
                       'dev-build-test-install@0.0.0')
    assert "lib/spack/env" in output


def test_dev_build_fails_already_installed(tmpdir, mock_packages,
                                           install_mockery):
    spec = spack.spec.Spec('dev-build-test-install@0.0.0').concretized()

    with tmpdir.as_cwd():
        with open(spec.package.filename, 'w') as f:
            f.write(spec.package.original_string)

        dev_build('dev-build-test-install@0.0.0')
        output = dev_build('dev-build-test-install@0.0.0', fail_on_error=False)
        assert 'Already installed in %s' % spec.prefix in output


def test_dev_build_fails_no_spec():
    output = dev_build(fail_on_error=False)
    assert 'requires a package spec argument' in output


def test_dev_build_fails_multiple_specs(mock_packages):
    output = dev_build('libelf', 'libdwarf', fail_on_error=False)
    assert 'only takes one spec' in output


def test_dev_build_fails_nonexistent_package_name(mock_packages):
    output = dev_build('no_such_package', fail_on_error=False)
    assert "No package for 'no_such_package' was found" in output


def test_dev_build_fails_no_version(mock_packages):
    output = dev_build('dev-build-test-install', fail_on_error=False)
    assert 'dev-build spec must have a single, concrete version' in output


def test_dev_build_env(tmpdir, mock_packages, install_mockery,
                       mutable_mock_env_path):
    # setup dev-build-test-install package for dev build
    build_dir = tmpdir.mkdir('build')
    spec = spack.spec.Spec('dev-build-test-install@0.0.0').concretized()
    with build_dir.as_cwd():
        with open(spec.package.filename, 'w') as f:
            f.write(spec.package.original_string)

    # setup environment
    envdir = tmpdir.mkdir('env')
    with envdir.as_cwd():
        with open('spack.yaml', 'w') as f:
            f.write("""\
env:
  specs:
  - dev-build-test-install@0.0.0

  dev-build:
    dev-build-test-install:
      source: %s
      version: 0.0.0
""" % build_dir)

        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

    assert spec.package.filename in os.listdir(spec.prefix)
    with open(os.path.join(spec.prefix, spec.package.filename), 'r') as f:
        assert f.read() == spec.package.replacement_string


def test_dev_build_env_version_mismatch(tmpdir, mock_packages, install_mockery,
                                        mutable_mock_env_path):
    # setup dev-build-test-install package for dev build
    build_dir = tmpdir.mkdir('build')
    spec = spack.spec.Spec('dev-build-test-install@0.0.0').concretized()
    with build_dir.as_cwd():
        with open(spec.package.filename, 'w') as f:
            f.write(spec.package.original_string)

    # setup environment
    envdir = tmpdir.mkdir('env')
    with envdir.as_cwd():
        with open('spack.yaml', 'w') as f:
            f.write("""\
env:
  specs:
  - dev-build-test-install@0.0.0

  dev-build:
    dev-build-test-install:
      source: %s
      version: 1.1.1
""" % build_dir)

        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            with pytest.raises(ev.SpackEnvironmentError):
                install()


def test_dev_build_multiple(tmpdir, mock_packages, install_mockery,
                            mutable_mock_env_path, mock_fetch):
    # setup dev-build-test-install package for dev build
    leaf_dir = tmpdir.mkdir('leaf')
    leaf_spec = spack.spec.Spec('dev-build-test-install@0.0.0').concretized()
    with leaf_dir.as_cwd():
        with open(leaf_spec.package.filename, 'w') as f:
            f.write(leaf_spec.package.original_string)

    # setup dev-build-test-dependent package for dev build
    root_dir = tmpdir.mkdir('root')
    root_spec = spack.spec.Spec('dev-build-test-dependent@0.0.0').concretized()
    with root_dir.as_cwd():
        with open(root_spec.package.filename, 'w') as f:
            f.write(root_spec.package.original_string)

    # setup environment
    envdir = tmpdir.mkdir('env')
    with envdir.as_cwd():
        with open('spack.yaml', 'w') as f:
            f.write("""\
env:
  specs:
  - dev-build-test-install@0.0.0
  - dev-build-test-dependent@0.0.0

  dev-build:
    dev-build-test-install:
      source: %s
      version: 0.0.0
    dev-build-test-dependent:
      source: %s
      version: 0.0.0
""" % (leaf_dir, root_dir))

        env('create', 'test', './spack.yaml')
        with ev.read('test'):
            install()

    for spec in (leaf_spec, root_spec):
        assert spec.package.filename in os.listdir(spec.prefix)
        with open(os.path.join(spec.prefix, spec.package.filename), 'r') as f:
            assert f.read() == spec.package.replacement_string
