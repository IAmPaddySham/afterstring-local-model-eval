import harness.config as cfg

def test_v523_registered_optin_default_v0():
    assert "v5.2.3" in cfg.FULL_PROMPTS
    assert cfg.DEFAULT_PROMPT_VERSION == "v0"
    txt = cfg.FULL_PROMPTS["v5.2.3"].read_text()
    # B4-15: draft unconditional, no permission-ask
    assert "write it now, in this reply, in fresh words" in txt
    assert "Do not ask permission to draft" in txt
    assert "never skipped" in txt
    # no identity bleed in the memory note
    assert "it is not about who you are" in txt
    # B4-08 and B4-10 paragraphs kept verbatim
    assert "not Paddy Sham" in txt
    assert "do not claim you have shut down" in txt

def test_v523_b408_b410_identical_to_v521():
    v521 = cfg.FULL_PROMPTS["v5.2.1"].read_text().splitlines()
    v523 = cfg.FULL_PROMPTS["v5.2.3"].read_text().splitlines()
    id_line = [l for l in v521 if l.startswith("If they address you as Paddy")][0]
    stop_line = [l for l in v521 if l.startswith("The person may stop or leave")][0]
    assert id_line in v523
    assert stop_line in v523
