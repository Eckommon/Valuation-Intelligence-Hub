"""M21 CLI/Web interface contracts."""
from __future__ import annotations

import json
from pathlib import Path

from valuation_hub import cli_entry
from valuation_hub.sec_live import TransportResponse, capture_companyfacts_snapshot
from valuation_hub.web_dilution import render_dilution_lab


def _snapshot()->dict:
    payload={"cik":1234567,"entityName":"CLI Dilution Fixture","facts":{"us-gaap":{
        "WeightedAverageNumberOfSharesOutstandingBasic":{"units":{"shares":[{"start":"2026-04-01","end":"2026-06-30","val":100,"accn":"0001234567-26-000030","fy":2026,"fp":"Q2","form":"10-Q","filed":"2026-08-05","frame":"CY2026Q2"}]}},
        "WeightedAverageNumberOfDilutedSharesOutstanding":{"units":{"shares":[{"start":"2026-04-01","end":"2026-06-30","val":110,"accn":"0001234567-26-000030","fy":2026,"fp":"Q2","form":"10-Q","filed":"2026-08-05","frame":"CY2026Q2"}]}}
    }}}
    body=json.dumps(payload,separators=(',',':')).encode()
    def transport(locator:str,*,user_agent:str)->TransportResponse:return TransportResponse(status=200,content_type='application/json',body=body,final_locator=locator)
    return capture_companyfacts_snapshot('1234567',user_agent='Valuation-Intelligence-Hub test@example.com',transport=transport,fetched_at='2026-09-12T10:40:00+00:00')


def test_cli_dispatch_exposes_m21_commands()->None:
    for command in ('dilution-sec-extract','dilution-normalize','dilution-observation-validate','dilution-derive','dilution-validate'):
        assert cli_entry._command([command])==command


def test_cli_dilution_round_trip(tmp_path:Path,capsys)->None:
    sp=tmp_path/'snapshot.json';sp.write_text(json.dumps(_snapshot()))
    observations=[]
    for metric in ('weighted_average_basic_shares','weighted_average_diluted_shares'):
        assert cli_entry.main(['dilution-sec-extract',str(sp),metric,'--period-start','2026-04-01','--period-end','2026-06-30','--form','10-Q'])==0
        candidate=json.loads(capsys.readouterr().out);cp=tmp_path/f'{metric}-candidate.json';cp.write_text(json.dumps(candidate))
        assert cli_entry.main(['dilution-normalize',str(cp)])==0
        observation=json.loads(capsys.readouterr().out);op=tmp_path/f'{metric}-observation.json';op.write_text(json.dumps(observation));observations.append(op)
        assert cli_entry.main(['dilution-observation-validate',str(op)])==0
        checked=json.loads(capsys.readouterr().out);assert checked['status']=='PASS_SHARE_DILUTION_OBSERVATION_VALIDATION'
    assert cli_entry.main(['dilution-derive',str(observations[0]),str(observations[1])])==0
    derived=json.loads(capsys.readouterr().out);dp=tmp_path/'derived.json';dp.write_text(json.dumps(derived))
    assert derived['semantic_boundary']['valuation_date_direct_bind'] is False
    assert cli_entry.main(['dilution-validate',str(dp)])==0
    checked=json.loads(capsys.readouterr().out);assert checked['status']=='PASS_HISTORICAL_DILUTION_VALIDATION'


def test_web_dilution_lab_is_historical_calculate_only()->None:
    page=render_dilution_lab()
    assert 'HISTORICAL ONLY · NOT VALUATION-DATE SHARES · CALCULATE ONLY' in page
    assert 'weighted-average diluted shares ≠ valuation-date fully diluted shares' in page
    assert '/api/dilution/derive' in page
    assert '/api/dilution/file-write' not in page
    assert '/api/dilution/canonical' not in page
