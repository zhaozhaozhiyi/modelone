"""Regression tests for the rendered Kubernetes manifest entrypoint.

The test uses a temporary release tree and a fake kubectl executable. It
verifies that source-tree paths are mapped into the image-rewritten release
tree without touching a real cluster.
"""
from pathlib import Path
import importlib.util
import os
import shlex
import subprocess
import tempfile
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "install/kubernetes/modelone-manifests.sh"
rewrite_spec = importlib.util.spec_from_file_location(
    "modelone_manifest_rewriter", ROOT / "scripts/rewrite_deployment_images.py"
)
rewrite = importlib.util.module_from_spec(rewrite_spec)
rewrite_spec.loader.exec_module(rewrite)


class ManifestEntrypointTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        # macOS exposes /var through a /private symlink; use canonical paths
        # because the shell helper compares PWD textually.
        self.root = Path(self.tempdir.name).resolve()
        self.source = self.root / "source"
        self.release = self.root / "release"
        self.manifests = self.release / "platform-manifests/kubernetes"
        (self.manifests / "argo").mkdir(parents=True)
        (self.manifests / "prometheus/grafana").mkdir(parents=True)
        (self.manifests / "kubeflow/train-operator/manifests/overlays/standalone").mkdir(parents=True)
        (self.source / "prometheus").mkdir(parents=True)
        (self.release / "kubernetes.yaml").write_text("kind: List\n")
        (self.manifests / "argo/install-3.4.3-all.yaml").write_text("kind: List\n")
        (self.manifests / "kubeflow/train-operator/manifests/overlays/standalone/kustomization.yaml").write_text(
            "apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\n"
        )
        (self.manifests / "argo/worker.yaml").write_text("kind: List\n")
        (self.manifests / "prometheus/grafana/dashboards.yaml").write_text("kind: List\n")
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "kubectl.calls"
        fake = self.bin / "kubectl"
        fake.write_text("#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$MODELONE_TEST_CALLS\"\n")
        fake.chmod(0o755)

    def run_helper(self, body):
        env = os.environ.copy()
        env.update({
            "PATH": str(self.bin) + os.pathsep + env.get("PATH", ""),
            "MODELONE_SOURCE_ROOT": str(self.source),
            "MODELONE_RELEASE_DIR": str(self.release),
            "MODELONE_MANIFEST_ROOT": str(self.manifests),
            "MODELONE_ARGO_MANIFEST_DIR": str(self.manifests / "argo"),
            "MODELONE_KUBERNETES_MANIFEST": str(self.release / "kubernetes.yaml"),
            "MODELONE_TEST_CALLS": str(self.calls),
        })
        script = "set -eu\nsource %s\n%s\n" % (shlex.quote(str(HELPER)), body)
        return subprocess.run(["bash", "-c", script], cwd=self.source, env=env, capture_output=True, text=True)

    def test_source_paths_map_to_release_tree(self):
        result = self.run_helper(
            "printf '%s\\n' \"$(modelone_manifest argo/worker.yaml)\"\n"
            "cd \"$MODELONE_SOURCE_ROOT/prometheus\"\n"
            "printf '%s\\n' \"$(modelone_manifest ./grafana/dashboards.yaml)\"\n"
            "cd \"$MODELONE_SOURCE_ROOT\"\n"
            "printf '%s\\n' \"$(modelone_kustomize kubeflow/train-operator/manifests/overlays/standalone)\""
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                str(self.manifests / "argo/worker.yaml"),
                str(self.manifests / "prometheus/grafana/dashboards.yaml"),
                str(self.manifests / "kubeflow/train-operator/manifests/overlays/standalone"),
            ],
        )

    def test_kubectl_wrapper_rewrites_filenames_and_rejects_missing_paths(self):
        result = self.run_helper(
            "kubectl apply -f argo/worker.yaml -k kubeflow/train-operator/manifests/overlays/standalone"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.calls.read_text().strip(),
            "apply -f %s -k %s" % (
                self.manifests / "argo/worker.yaml",
                self.manifests / "kubeflow/train-operator/manifests/overlays/standalone",
            ),
        )
        missing = self.run_helper("kubectl apply -f argo/missing.yaml")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("缺少", missing.stderr)

    def test_release_paths_are_allowed_and_parent_traversal_is_rejected(self):
        allowed = self.run_helper(
            "test \"$(modelone_manifest \"$MODELONE_KUBERNETES_MANIFEST\")\" = \"$MODELONE_KUBERNETES_MANIFEST\""
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        rejected = self.run_helper("modelone_manifest ../outside.yaml")
        self.assertNotEqual(rejected.returncode, 0)
        self.assertIn("非法", rejected.stderr)

    def test_configured_domain_replaces_wildcards_and_adds_https_gateway(self):
        gateway = self.root / "gateway.yaml"
        gateway.write_text(
            "apiVersion: networking.istio.io/v1alpha3\n"
            "kind: Gateway\n"
            "metadata:\n  name: kubeflow-gateway\n"
            "spec:\n  servers:\n  - hosts: ['*']\n"
            "    port:\n      number: 80\n      protocol: HTTP\n"
        )
        virtual = self.root / "virtual.yaml"
        virtual.write_text(
            "apiVersion: networking.istio.io/v1alpha3\n"
            "kind: VirtualService\n"
            "spec:\n  hosts: ['*']\n"
        )
        before = dict(rewrite.brand.BRAND)
        try:
            rewrite.brand.BRAND.update(public_domain="modelone.example.test", tls_secret_name="modelone-tls")
            rewrite.render_network_manifest(gateway)
            rewrite.render_network_manifest(virtual)
        finally:
            rewrite.brand.BRAND.clear()
            rewrite.brand.BRAND.update(before)
        gateway_doc = next(yaml.safe_load_all(gateway.read_text()))
        self.assertEqual(gateway_doc["spec"]["servers"][0]["hosts"], ["modelone.example.test"])
        https = next(server for server in gateway_doc["spec"]["servers"] if server["port"]["number"] == 443)
        self.assertEqual(https["tls"], {"credentialName": "modelone-tls", "mode": "SIMPLE"})
        virtual_doc = next(yaml.safe_load_all(virtual.read_text()))
        self.assertEqual(virtual_doc["spec"]["hosts"], ["modelone.example.test"])

    def test_ingress_uses_stable_api_and_configured_tls(self):
        ingress = self.root / "ingress.yaml"
        ingress.write_text((ROOT / "install/kubernetes/ingress.yaml").read_text())
        before = dict(rewrite.brand.BRAND)
        try:
            rewrite.brand.BRAND.update(public_domain="modelone.example.test", tls_secret_name="modelone-tls")
            rewrite.render_network_manifest(ingress)
        finally:
            rewrite.brand.BRAND.clear()
            rewrite.brand.BRAND.update(before)
        documents = [document for document in yaml.safe_load_all(ingress.read_text()) if document]
        self.assertTrue(documents)
        for document in documents:
            self.assertEqual(document["apiVersion"], "networking.k8s.io/v1")
            self.assertEqual(
                document["spec"]["tls"],
                [{"hosts": ["modelone.example.test"], "secretName": "modelone-tls"}],
            )
            for rule in document["spec"]["rules"]:
                self.assertEqual(rule["host"], "modelone.example.test")
                for path in rule["http"]["paths"]:
                    self.assertEqual(path["pathType"], "Prefix")
                    self.assertIn("service", path["backend"])

    def test_kubernetes_sources_do_not_use_removed_api_versions(self):
        forbidden = {
            "extensions/v1beta1",
            "apps/v1beta1",
            "apps/v1beta2",
            "autoscaling/v2beta1",
            "autoscaling/v2beta2",
            "batch/v1beta1",
            "networking.k8s.io/v1beta1",
            "policy/v1beta1",
            "rbac.authorization.k8s.io/v1beta1",
        }
        violations = []
        paths = list((ROOT / "install/kubernetes").rglob("*.yaml"))
        paths.extend((ROOT / "install/kubernetes").rglob("*.yml"))
        for path in paths:
            for number, document in enumerate(yaml.safe_load_all(path.read_text()), 1):
                if document and document.get("apiVersion") in forbidden:
                    violations.append(f"{path.relative_to(ROOT)} document {number}: {document['apiVersion']}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
