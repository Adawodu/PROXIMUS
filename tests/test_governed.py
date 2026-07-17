"""Governed Proof-of-Me persona — the voice twin speaks only the curated export,
with the same guardrails as the text/browser lanes."""

import json

from proximus.context.governed import GovernedResume, load_governed_resume


def _export(tmp_path):
    p = tmp_path / "proof-export.json"
    p.write_text(
        json.dumps(
            {
                "owner": "Adebayo Dawodu",
                "items": [
                    {
                        "title": "PROXIMUS",
                        "kind": "repo",
                        "text": "open-source AI voice agent",
                        "proof_url": "https://github.com/Adawodu/PROXIMUS",
                    },
                    {
                        "title": "Tech Exec Resume",
                        "kind": "doc",
                        "text": "technical leadership",
                        "proof_url": None,
                    },
                ],
            }
        )
    )
    return str(p)


def test_loads_curated_export(tmp_path):
    r = load_governed_resume(_export(tmp_path))
    assert isinstance(r, GovernedResume)
    assert r.candidate_name == "Adebayo Dawodu"
    assert "PROXIMUS" in r.content and "Tech Exec Resume" in r.content


def test_prompt_carries_the_guardrails(tmp_path):
    p = load_governed_resume(_export(tmp_path)).to_system_prompt().lower()
    assert "first person" in p  # speaks AS the owner
    assert "proximus" in p  # curated corpus is present
    assert "health" in p and "finances" in p  # declines personal topics
    assert "never as instructions" in p  # injection-resistant
    assert "ai voice twin" in p  # honest it's an AI
    assert "only from the verified materials" in p  # grounded, no invention
