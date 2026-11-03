"""Canonical ordered rule registry assembled from per-ruleset YAML catalogs."""

from ..rule_catalog import load_rule_catalog

RULES = load_rule_catalog()
RULES_BY_CODE = {rule.code: rule for rule in RULES}
