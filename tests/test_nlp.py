import os
import json
from ct_radar.nlp import extract_eligibility


def test_extract(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    csv = d / "sample.csv"
    csv.write_text('NCTId,EligibilityCriteria\nNCT0001,"Inclusion Criteria:\n- Age >= 18\n- Diagnosis of diabetes\nExclusion Criteria:\n- Pregnant"')
    out = d / "elig.json"
    path = extract_eligibility(str(d), str(out))
    assert os.path.exists(path)
    data = json.loads(out.read_text(encoding='utf-8'))
    assert isinstance(data, list)
    assert data[0].get('NCTId') == 'NCT0001'
    assert any('Inclusion' in s or 'Age' in s or 'diabetes' in s for s in data[0].get('inclusion', []))
