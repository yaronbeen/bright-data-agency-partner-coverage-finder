import tool


def test_maps_provider_evidence_to_regions_and_specialties():
    report = tool.map_coverage(tool.SAMPLE)
    assert report["provider_count"] == 3
    assert "DACH" in report["regions"]
    assert report["evidence"]


def test_no_people_contacts_in_output():
    assert "contacts" not in tool.map_coverage(tool.SAMPLE)
