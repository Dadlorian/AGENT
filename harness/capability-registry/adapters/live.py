#!/usr/bin/env python3
"""Live adapter for the component running on this host today: skills resolved
by directory path under .claude/skills/, indexed by docs/skill-manifest.json
(F-b3-07 "skill files"; blueprint state "registry record and version" -
home_today "capability packages resolved as files on disk"). Nothing there is
signed or versioned today (X-end-to-end-025: "Anthropic does not currently
publish the skill format as an explicitly versioned artifact"), which is
exactly the gap this adapter closes: it reads each skill.json the manifest
names (never writes into .claude/skills/), signs it, and gives it a synthetic
first version 1.0.0 the first time this adapter runs against it - the
"publish one record for every package that exists today" step of the proposed
migration (cap-capability-registry-implement instruction 4).

Reached only through the environment variables in README.md:
  SKILLS_DIR          the skill directories this host resolves by path (.claude/skills)
  SKILL_MANIFEST      the index naming which of them are registered (docs/skill-manifest.json)
  REGISTRY_KEY_FILE   the file holding the key this deployment signs with
  REGISTRY_NAMESPACE  the namespace published records are filed under (default: agentic-stack)
No network is involved: today's component is files on this host, so there is
no endpoint and no socket, and urllib is not imported.
"""
from __future__ import annotations

import json
import os

from interface import PublishRequest, Problem
from adapters.dryrun import SignedIndexAdapter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class LiveSkillFilesAdapter(SignedIndexAdapter):
    entity = ("the skill directories on this host (.claude/skills/, indexed by docs/skill-manifest.json), "
             "each signed and given a synthetic first version the first time this adapter runs")
    trust_anchor = "a key file this host holds"
    declared_gaps = SignedIndexAdapter.declared_gaps + (
        "the packaging format publishes no explicit version (F-b3-07, X-end-to-end-025), so every "
        "skill this adapter finds is registered as version 1.0.0 on first run; a second version "
        "needs a real change to the skill and a re-run",
        "this adapter reads .claude/skills/ and docs/skill-manifest.json, and never writes into either")

    def __init__(self):
        # deliberately not calling SignedIndexAdapter.__init__ via super() before
        # the env is read: a missing env var must refuse before any store state exists.
        self.resolutions = 0
        self.refusals = 0
        self.refusal_log = []
        self._store = {}
        self.head = "genesis"
        self.chain = []
        self.skills_dir = self._env("SKILLS_DIR")
        self.manifest_path = self._env("SKILL_MANIFEST")
        key_file = self._env("REGISTRY_KEY_FILE")
        self.namespace = os.environ.get("REGISTRY_NAMESPACE", "agentic-stack")
        if not os.path.isdir(self.skills_dir):
            raise Problem("adapter-unavailable", f"SKILLS_DIR {self.skills_dir} does not exist", retry_after_s=30)
        if not os.path.isfile(self.manifest_path):
            raise Problem("adapter-unavailable", f"SKILL_MANIFEST {self.manifest_path} does not exist",
                          retry_after_s=30)
        key = open(key_file, "rb").read().strip()
        if len(key) < 16:
            raise Problem("adapter-unavailable", "the signing key is shorter than 16 bytes", retry_after_s=30)
        self._key = key
        self._scan()

    @staticmethod
    def _env(name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise Problem("adapter-unavailable",
                          f"{name} is not set; the skill files on this host cannot be reached and "
                          f"nothing was registered", retry_after_s=30)
        return value

    def _scan(self) -> None:
        """Publish one record for every skill the manifest names and the
        filesystem carries a skill.json for - the shadow-publish step of the
        proposed migration, run against real files, writing nothing back to
        them."""
        manifest = json.load(open(self.manifest_path))
        names = [s["name"] for s in manifest.get("skills", [])]
        published = refused = missing = 0
        for name in names:
            path = os.path.join(self.skills_dir, name, "skill.json")
            if not os.path.isfile(path):
                missing += 1
                continue
            data = open(path, "rb").read()
            try:
                self.publish(PublishRequest(self.namespace, name, "1.0.0", "capability", data,
                                            actor="live:directory-scan"))
                published += 1
            except Problem:
                refused += 1
        self.scanned = {"names_in_manifest": len(names), "published": published,
                        "refused_as_already_published": refused, "missing_skill_json": missing}

    def _signer(self, request: PublishRequest) -> tuple:
        return "host-held-key-v1", self._key

    def _verifying_material(self, namespace: str, name: str) -> bytes | None:
        return self._key


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveSkillFilesAdapter
