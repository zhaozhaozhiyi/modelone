"""Isolated notebook startup checks; no host services or cluster are changed."""
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


init = load('notebook_init', 'images/jupyter-notebook/notebook_init.py')
runtime = load('notebook_runtime', 'myapp/notebook_runtime.py')


class NotebookTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.env = {'USERNAME': 'tester', 'SSH_PORT': '10021'}
        self.calls = []

    def run_command(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if args[:2] == ['ssh-keygen', '-l']:
            return subprocess.run(args, **kwargs)

    def initialize(self):
        init.initialize(self.env, self.root, self.run_command)

    def config(self):
        return (self.root / 'etc/ssh/sshd_config').read_text()

    def test_missing_credentials_keeps_notebook_files_and_disables_ssh(self):
        self.initialize()
        self.assertTrue((self.root / 'mnt/tester/examples').is_symlink())
        self.assertEqual([args for args, _ in self.calls], [['service', 'ssh', 'stop']])
        self.assertIn('PermitRootLogin no', self.config())
        self.assertIn('PermitEmptyPasswords no', self.config())
        self.initialize()

    def test_spark_configuration_works_without_ssh_and_is_idempotent(self):
        self.env.update(MODELONE_NOTEBOOK_SPARK='true', SPARK_HOME='/spark',
                        PORT1='10022', PORT2='10023', SERVICE_EXTERNAL_IP='192.0.2.5')
        spark = self.root / 'spark/conf/spark-defaults.conf'
        spark.parent.mkdir(parents=True)
        spark.write_text('spark.driver.port 9999\nspark.executor.memory=2g\n')
        self.initialize()
        first = spark.read_text()
        self.initialize()
        self.assertEqual(first, spark.read_text())
        self.assertIn('spark.executor.memory=2g', first)
        self.assertEqual(first.count('spark.driver.port='), 1)
        self.assertIn('spark.driver.port=10022', first)

    def test_password_file_preserves_equals_and_never_enters_arguments(self):
        password = 'unit-test=password=1234'
        source = self.root / 'password'
        source.write_text(password + '\n')
        self.env.update(runtime.parse_environment('NOTEBOOK_ROOT_PASSWORD_FILE=/password\nX=a=b=='))
        self.assertEqual(self.env['X'], 'a=b==')
        self.initialize()
        calls = dict((args[0], kwargs) for args, kwargs in self.calls)
        self.assertEqual(calls['chpasswd']['input'], 'root:' + password + '\n')
        self.assertTrue(all(password not in str(args) for args, _ in self.calls))
        self.assertIn('PasswordAuthentication yes', self.config())
        self.assertIn('PermitEmptyPasswords no', self.config())
        self.assertEqual(self.calls[-1][0], ['service', 'ssh', 'start'])

    def test_invalid_or_conflicting_credentials_leave_daemon_disabled(self):
        for value in ('short', 'a' * 20 + '\nroot:bad'):
            self.env['NOTEBOOK_ROOT_PASSWORD'] = value
            with self.assertRaises(ValueError):
                self.initialize()
            self.assertIn('PermitRootLogin no', self.config())
        self.env.update(NOTEBOOK_ROOT_PASSWORD='a' * 20, NOTEBOOK_ROOT_PASSWORD_FILE='/missing')
        with self.assertRaises(ValueError):
            self.initialize()
        self.assertNotIn(['service', 'ssh', 'start'], [args for args, _ in self.calls])

    def test_chpasswd_failure_prevents_start(self):
        self.env['NOTEBOOK_ROOT_PASSWORD'] = 'test-password=123456'
        def fail(args, **kwargs):
            self.run_command(args, **kwargs)
            if args == ['chpasswd']:
                raise subprocess.CalledProcessError(1, args)
        with self.assertRaises(subprocess.CalledProcessError):
            init.initialize(self.env, self.root, fail)
        self.assertIn('PermitRootLogin no', self.config())
        self.assertNotIn(['service', 'ssh', 'start'], [args for args, _ in self.calls])

    def test_public_key_disables_password_login(self):
        subprocess.run(['ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-f', str(self.root / 'key')], check=True)
        self.env['NOTEBOOK_SSH_PUBLIC_KEY_FILE'] = '/key.pub'
        self.initialize()
        self.assertIn('PermitRootLogin prohibit-password', self.config())
        self.assertIn('PasswordAuthentication no', self.config())
        self.assertIn('PubkeyAuthentication yes', self.config())
        keys = self.root / 'run/modelone/authorized_keys'
        self.assertEqual(keys.stat().st_mode & 0o777, 0o600)
        self.assertIn(['ssh-keygen', '-l', '-f', str(keys)], [args for args, _ in self.calls])

    def test_invalid_public_key_prevents_start(self):
        (self.root / 'key.pub').write_text('not-a-key')
        self.env['NOTEBOOK_SSH_PUBLIC_KEY_FILE'] = '/key.pub'
        with self.assertRaises(subprocess.CalledProcessError):
            self.initialize()
        self.assertNotIn(['service', 'ssh', 'start'], [args for args, _ in self.calls])

    def test_invalid_environment_names_and_workspace_are_rejected(self):
        with self.assertRaises(ValueError):
            runtime.parse_environment('BAD KEY=value')
        self.env['USERNAME'] = '../escape'
        with self.assertRaises(ValueError):
            self.initialize()

    @unittest.skipUnless(os.environ.get('MODELONE_NOTEBOOK_TEST_IMAGE'), 'optional local container check')
    def test_launcher_waits_for_initialization_and_propagates_failure(self):
        image = os.environ['MODELONE_NOTEBOOK_TEST_IMAGE']
        script = self.root / 'init.sh'
        for status in (1, 0):
            script.write_text('#!/bin/sh\necho setup-finished\nexit ' + str(status) + '\n')
            result = subprocess.run([
                'docker', 'run', '--rm', '--pull=never', '--network=none', '--entrypoint', 'sh',
                '--mount', 'type=bind,source=' + str(script) + ',target=/init.sh,readonly',
                image, '-c', runtime.initialization_command('modelone-test') + 'echo ide-started'
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, status, result.stderr)
            self.assertEqual('ide-started' in result.stdout, status == 0)
            if status:
                self.assertIn('setup-finished', result.stderr)


if __name__ == '__main__':
    unittest.main()
