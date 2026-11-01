from pipeline.rag.cve_collector import parse_response


def test_nvd_fixture() -> None:
    cve = {'id': 'CVE-2025-12345', 'vulnStatus': 'Analyzed', 'published': '2025-01-01',
        'descriptions': [{'lang': 'en', 'value': 'An IDOR permits reading another account.'}],
        'weaknesses': [{'description': [{'lang': 'en', 'value': 'CWE-639'}]}],
        'references': [{'url': 'https://example.org/advisory'}]}
    assert parse_response({'vulnerabilities': [{'cve': cve}, {'cve': {**cve, 'vulnStatus': 'Rejected'}}]}) == [
        dict(cve_id=cve['id'], summary=cve['descriptions'][0]['value'], cwe=['CWE-639'],
             published=cve['published'], refs=['https://example.org/advisory'])]
