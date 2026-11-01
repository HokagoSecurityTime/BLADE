import pytest
from training.data.assemble_policy_pilot import validate


def fixture():
    row={'id':'x','path':'/replies/{replyId}','oas_snippet':'{"path_params":["replyId"]}',
         'enrichment':{'facts':[{'json_pointer':'/description','text':'Only the original author may edit.'}]}}
    decision=dict(id='x',label='owner_match',confidence=.8,rationale='Author-only edit is explicit.',
        policy_status='supported',evidence_strength='explicit',object_param='replyId',owner_lookup=None,
        lookup_status='unresolved',lookup_reason='No physical DB mapping.',roles=[],allowed_membership=[],
        evidence=[{'pointer':'/description','quote':'Only the original author may edit.'}])
    return row,decision


def test_policy_independent_of_lookup():
    row,decision=fixture()
    validate(row,decision)


def test_supported_without_evidence_rejected():
    row,decision=fixture()
    decision['evidence']=[]
    with pytest.raises(ValueError,match='evidence'):validate(row,decision)


def test_fabricated_quote_rejected():
    row,decision=fixture()
    decision['evidence'][0]['quote']='Admins may bypass'
    with pytest.raises(ValueError,match='Citation mismatch'):validate(row,decision)


def test_unverified_lookup_cannot_be_executable():
    row,decision=fixture()
    decision['owner_lookup']={'table':'replies','id_col':'id','owner_col':'user_id'}
    with pytest.raises(ValueError,match='Unverified'):validate(row,decision)
