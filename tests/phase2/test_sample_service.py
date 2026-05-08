import pytest

from src.repositories.sample_repository import SampleRepository
from src.services.sample_service import SampleService


@pytest.fixture
def service():
    repo = SampleRepository()
    return SampleService(repo)


def test_tc_2_01_register_sample_returns_correct_values(service):
    sample = service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0.85)

    assert sample.id == "S001"
    assert sample.name == "GaAs-100"
    assert sample.avgProductionTime == 2.5
    assert sample.yield_ == 0.85
    assert sample.stock == 0


def test_tc_2_02_empty_name_raises_value_error(service):
    with pytest.raises(ValueError, match="시료 이름은 필수 입력값입니다."):
        service.register_sample(name="", avgProductionTime=2.5, yield_=0.85)


def test_tc_2_03_whitespace_only_name_raises_value_error(service):
    with pytest.raises(ValueError, match="시료 이름은 필수 입력값입니다."):
        service.register_sample(name="   ", avgProductionTime=2.5, yield_=0.85)


def test_tc_2_04_avg_production_time_zero_raises_value_error(service):
    with pytest.raises(ValueError, match="평균 생산시간은 0보다 커야 합니다."):
        service.register_sample(name="GaAs-100", avgProductionTime=0, yield_=0.85)


def test_tc_2_05_avg_production_time_negative_raises_value_error(service):
    with pytest.raises(ValueError, match="평균 생산시간은 0보다 커야 합니다."):
        service.register_sample(name="GaAs-100", avgProductionTime=-1.0, yield_=0.85)


def test_tc_2_06_avg_production_time_small_positive_is_valid(service):
    sample = service.register_sample(name="GaAs-100", avgProductionTime=0.001, yield_=0.85)

    assert sample.avgProductionTime == 0.001


def test_tc_2_07_yield_zero_raises_value_error(service):
    with pytest.raises(ValueError, match="수율은 0 초과 1 이하여야 합니다."):
        service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0)


def test_tc_2_08_yield_over_one_raises_value_error(service):
    with pytest.raises(ValueError, match="수율은 0 초과 1 이하여야 합니다."):
        service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=1.001)


def test_tc_2_09_yield_exactly_one_is_valid(service):
    sample = service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=1.0)

    assert sample.yield_ == 1.0


def test_tc_2_10_yield_small_positive_is_valid(service):
    sample = service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0.001)

    assert sample.yield_ == 0.001


def test_tc_2_11_get_all_samples_returns_correct_count(service):
    service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0.85)
    service.register_sample(name="GaAs-200", avgProductionTime=3.0, yield_=0.90)
    service.register_sample(name="SiC-300", avgProductionTime=1.5, yield_=0.75)

    samples = service.get_all_samples()

    assert len(samples) == 3


def test_tc_2_12_get_all_samples_empty_repository_returns_empty_list(service):
    samples = service.get_all_samples()

    assert samples == []


def test_tc_2_13_search_by_name_partial_match_returns_matching_samples(service):
    service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0.85)
    service.register_sample(name="GaAs-200", avgProductionTime=3.0, yield_=0.90)
    service.register_sample(name="SiC-300", avgProductionTime=1.5, yield_=0.75)

    results = service.search_samples_by_name("GaAs")

    assert len(results) == 2
    names = [s.name for s in results]
    assert "GaAs-100" in names
    assert "GaAs-200" in names


def test_tc_2_14_search_by_name_is_case_insensitive(service):
    service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0.85)
    service.register_sample(name="SiC-300", avgProductionTime=1.5, yield_=0.75)

    results = service.search_samples_by_name("gaas")

    assert len(results) == 1
    assert results[0].name == "GaAs-100"


def test_tc_2_15_search_by_name_no_match_returns_empty_list(service):
    service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0.85)

    results = service.search_samples_by_name("존재하지않는이름")

    assert results == []


def test_tc_2_16_multiple_registrations_produce_unique_ids(service):
    s1 = service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0.85)
    s2 = service.register_sample(name="GaAs-200", avgProductionTime=3.0, yield_=0.90)
    s3 = service.register_sample(name="SiC-300", avgProductionTime=1.5, yield_=0.75)

    assert s1.id == "S001"
    assert s2.id == "S002"
    assert s3.id == "S003"
    assert len({s1.id, s2.id, s3.id}) == 3


def test_tc_2_17_sequential_registrations_have_incrementing_ids(service):
    s1 = service.register_sample(name="GaAs-100", avgProductionTime=2.5, yield_=0.85)
    s2 = service.register_sample(name="GaAs-200", avgProductionTime=3.0, yield_=0.90)

    assert s1.id == "S001"
    assert s2.id == "S002"
