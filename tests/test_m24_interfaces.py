"""M24 additive CLI/Web interface contracts."""
from __future__ import annotations

from pathlib import Path

from valuation_hub import cli_entry_m24
from valuation_hub.web_wacc import render_wacc_lab


def test_m24_cli_intercepts_only_new_wacc_surface_and_v04_validation()->None:
    for command in ('wacc-source-build','wacc-source-validate','wacc-candidate-build','wacc-candidate-validate','wacc-review-build','wacc-review-validate','wacc-finalize','wacc-validate','binding-build-with-wacc','binding-validate','web'):
        assert cli_entry_m24._command([command])==command
    assert cli_entry_m24._command(['share-bridge-validate']) is None
    assert cli_entry_m24._command(['debt-validate']) is None
    assert cli_entry_m24._command(['binding-build-with-diluted-shares']) is None


def test_wacc_candidate_parser_requires_explicit_scenario_targets()->None:
    args=cli_entry_m24._parser().parse_args(['wacc-candidate-build','inputs.json','--entity-id','ENTITY:1','--financial-scope','CFS','--capital-currency','KRW','--as-of','2026-09-12','--scenario-name','BASE','--scenario-name','BULL'])
    assert args.command=='wacc-candidate-build'
    assert args.inputs==Path('inputs.json')
    assert args.scenario_name==['BASE','BULL']


def test_wacc_web_lab_is_assumption_only_and_no_write()->None:
    page=render_wacc_lab()
    assert 'ASSUMPTION · HUMAN REVIEW · CALCULATE/VALIDATE ONLY' in page
    assert 'Calculated WACC ≠ reviewed assumption ≠ historical fact.' in page
    assert '/api/wacc/' in page
    assert 'NO DRAFT APPLY · NO FILE WRITE · NO PROMOTION · NO CANONICAL WRITE' in page
    assert '/api/wacc/apply' not in page
    assert '/api/wacc/file-write' not in page
    assert '/api/wacc/canonical' not in page
