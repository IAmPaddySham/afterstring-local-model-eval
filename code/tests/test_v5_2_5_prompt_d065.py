import harness.config as cfg

def test_v525_registered_optin_default_v0():
    assert "v5.2.5" in cfg.FULL_PROMPTS
    assert cfg.DEFAULT_PROMPT_VERSION == "v0"
    txt = cfg.FULL_PROMPTS["v5.2.5"].read_text()
    # B4-08 clause
    assert 'Do not say "I will stop" or "I am stopping"' in txt
    assert "only acknowledge with a plain sign-off" in txt
    # B4-15 clause
    assert "Do not ask for more details, clarification, or the original wording" in txt
    assert "draft from what you know now" in txt
    # identity scope limit kept from v5.2.4
    assert "It does not apply to draft, note, or text requests" in txt
    # B4-15/B4-10 beats kept
    assert "not Paddy Sham" in txt

def test_v525_b415_identity_unchanged_from_v524():
    v524 = cfg.FULL_PROMPTS["v5.2.4"].read_text()
    v525 = cfg.FULL_PROMPTS["v5.2.5"].read_text()
    id_para = [l for l in v524.splitlines() if l.startswith("If they address you as Paddy")][0]
    assert id_para in v525
