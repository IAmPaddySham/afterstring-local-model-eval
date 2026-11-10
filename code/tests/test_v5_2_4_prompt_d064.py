import harness.config as cfg

def test_v524_registered_optin_default_v0():
    assert "v5.2.4" in cfg.FULL_PROMPTS
    assert cfg.DEFAULT_PROMPT_VERSION == "v0"
    txt = cfg.FULL_PROMPTS["v5.2.4"].read_text()
    # identity scope limit present
    assert "This identity correction applies only when the person is asserting you are Paddy or the author" in txt
    assert "It does not apply to draft, note, or text requests" in txt
    # B4-15 paragraph unchanged from v5.2.1
    assert "in the same reply write the draft or note they asked for now in fresh words" in txt
    # B4-08 and B4-10 kept verbatim
    assert "not Paddy Sham" in txt
    assert "do not claim you have shut down" in txt

def test_v524_b415_b408_unchanged_from_v521():
    v521 = cfg.FULL_PROMPTS["v5.2.1"].read_text().splitlines()
    v524 = cfg.FULL_PROMPTS["v5.2.4"].read_text().splitlines()
    b415 = [l for l in v521 if l.startswith("Only if the person claims something happened before")][0]
    stop = [l for l in v521 if l.startswith("The person may stop or leave")][0]
    assert b415 in v524
    assert stop in v524
