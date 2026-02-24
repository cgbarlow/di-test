"""Tests for plugin manifest validation."""

import json
import os

import pytest

PLUGIN_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".claude-plugin")
MANIFEST_PATH = os.path.join(PLUGIN_DIR, "plugin.json")


class TestPluginManifest:
    """Tests for .claude-plugin/plugin.json."""

    def test_manifest_exists(self):
        assert os.path.isfile(MANIFEST_PATH), f"plugin.json not found at {MANIFEST_PATH}"

    def test_manifest_is_valid_json(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_has_required_fields(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        required = ["name", "version", "description", "author", "skills"]
        for field in required:
            assert field in data, f"Missing required field: {field}"

    def test_name_is_di_test(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        assert data["name"] == "di-test"

    def test_version_is_semver(self):
        import re

        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        assert re.match(r"^\d+\.\d+\.\d+$", data["version"])

    def test_skills_is_list(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        assert isinstance(data["skills"], list)
        assert len(data["skills"]) == 7

    def test_each_skill_has_name_and_path(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        for skill in data["skills"]:
            assert "name" in skill, f"Skill missing 'name': {skill}"
            assert "path" in skill, f"Skill missing 'path': {skill}"

    def test_skill_names(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        expected_names = {"scan", "scan-status", "results", "summary", "report", "list-scans", "visual-scan"}
        actual_names = {s["name"] for s in data["skills"]}
        assert actual_names == expected_names

    def test_has_hooks_section(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        assert "hooks" in data
        assert isinstance(data["hooks"], dict)

    def test_has_mcp_servers(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        assert "mcpServers" in data
        assert "cwac" in data["mcpServers"]


class TestSkillFiles:
    """Tests that SKILL.md files exist for each declared skill."""

    SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")

    def test_all_skill_dirs_exist(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        for skill in data["skills"]:
            skill_dir = os.path.join(self.SKILLS_DIR, skill["name"])
            assert os.path.isdir(skill_dir), f"Skill directory not found: {skill_dir}"

    def test_all_skill_md_files_exist(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        for skill in data["skills"]:
            skill_md = os.path.join(self.SKILLS_DIR, skill["name"], "SKILL.md")
            assert os.path.isfile(skill_md), f"SKILL.md not found: {skill_md}"

    def test_skill_md_files_not_empty(self):
        with open(MANIFEST_PATH, "r") as f:
            data = json.load(f)
        for skill in data["skills"]:
            skill_md = os.path.join(self.SKILLS_DIR, skill["name"], "SKILL.md")
            assert os.path.getsize(skill_md) > 50, f"SKILL.md too small: {skill_md}"


class TestMarketplaceJson:
    """Tests for marketplace.json."""

    MARKETPLACE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "marketplace.json")

    def test_marketplace_exists(self):
        assert os.path.isfile(self.MARKETPLACE_PATH)

    def test_marketplace_is_valid_json(self):
        with open(self.MARKETPLACE_PATH, "r") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_marketplace_has_source(self):
        with open(self.MARKETPLACE_PATH, "r") as f:
            data = json.load(f)
        assert "source" in data
        assert data["source"] == "."
