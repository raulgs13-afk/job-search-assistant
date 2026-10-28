from jobassistant.models import JobPosting, JobSearch


def make_job(location):
    return JobPosting(
        source="test",
        external_id=1,
        title="Python Developer",
        location=location,
        description="...",
        url="https://example.com/job/1",
    )


def test_default_search():
    assert JobSearch().locations == ["Málaga", "Madrid"]


def test_location_match_ignores_accents():
    assert make_job("Málaga, Málaga").matches_locations(["Malaga"])


def test_location_no_match():
    assert not make_job("Barcelona").matches_locations(["Málaga", "Madrid"])