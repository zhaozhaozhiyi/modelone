"""Node rollout transport checks using a local fake SSH runner, never a network."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('batch_ssh', ROOT / 'install/kubernetes/rancher/批量ssh/batch_ssh.py')
batch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch)


class NodeTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)
        self.nodes = self.folder / 'nodes.txt'
        self.nodes.write_text('192.0.2.1\n192.0.2.2\n192.0.2.1 # duplicate\n')
        self.config = self.folder / 'nodes.json'
        self.config.write_text(json.dumps({'STAGE': '11'}))
        self.config.chmod(0o600)
        self.env = {'MODELONE_NODE_IPS_FILE': str(self.nodes), 'MODELONE_SSH_USER': 'operator',
                    'MODELONE_NODE_CONFIG_FILE': str(self.config)}

    def test_sequential_nodes_report_failures_and_continue(self):
        calls = []
        def fake_ssh(args, **kwargs):
            calls.append(args)
            self.assertIn('StrictHostKeyChecking=yes', args)
            self.assertIn('BatchMode=yes', args)
            return subprocess.CompletedProcess(args, 7 if len(calls) == 1 else 0, '', 'private remote output')
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            status = batch.deploy(self.env, fake_ssh)
        self.assertEqual(status, 1)
        self.assertEqual(len(calls), 2)
        self.assertNotIn('192.0.2.1: completed', output.getvalue())
        self.assertIn('192.0.2.2: completed', output.getvalue())
        self.assertNotIn('private remote output', errors.getvalue())

    def test_all_nodes_are_validated_before_connecting(self):
        self.nodes.write_text('192.0.2.1\n192.0.2.2;touch /tmp/invalid\n')
        calls = []
        with self.assertRaises(ValueError):
            batch.deploy(self.env, lambda *a, **k: calls.append(a))
        self.assertFalse(calls)

    def test_private_file_and_explicit_stage_are_required(self):
        self.config.chmod(0o644)
        with self.assertRaises(ValueError):
            batch.prepare(self.env)
        self.config.chmod(0o600)
        for config in ({}, {'STAGE': '44'}, {'STAGE': '11', 'BASH_ENV': '/malicious'}):
            self.config.write_text(json.dumps(config))
            with self.assertRaises(ValueError):
                batch.prepare(self.env)

    def test_config_is_shell_data_and_stage_failure_propagates(self):
        marker = self.folder / 'must-not-exist'
        token = 'quote\' = $(touch ' + str(marker) + '); `false`'
        self.config.write_text(json.dumps({'STAGE': '11', 'RANCHER_AGENT_TOKEN': token}))
        _, _, payload = batch.prepare(self.env)
        # Replace only the network and docker executables. Execute the actual
        # generated shell and selected init stage inside the temporary fixture.
        stub = self.folder / 'docker'
        stub.write_text('#!/bin/sh\nexit 9\n')
        stub.chmod(0o700)
        result = subprocess.run(['bash', '-s'], input=payload, text=True, capture_output=True,
                                env={**os.environ, 'PATH': str(self.folder) + os.pathsep + os.environ['PATH']})
        self.assertEqual(result.returncode, 9, result.stderr)
        self.assertFalse(marker.exists())
        self.assertNotIn(token, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
