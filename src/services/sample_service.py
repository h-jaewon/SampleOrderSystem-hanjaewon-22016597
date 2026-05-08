from src.models.sample import Sample
from src.repositories.sample_repository import SampleRepository


class SampleService:
    def __init__(self, sample_repository: SampleRepository) -> None:
        self._sample_repository = sample_repository

    def register_sample(self, name: str, avgProductionTime: float, yield_: float) -> Sample:
        if not name.strip():
            raise ValueError("시료 이름은 필수 입력값입니다.")
        if avgProductionTime <= 0:
            raise ValueError("평균 생산시간은 0보다 커야 합니다.")
        if yield_ <= 0 or yield_ > 1:
            raise ValueError("수율은 0 초과 1 이하여야 합니다.")

        sample_id = f"S{len(self._sample_repository.get_all()) + 1:03d}"
        sample = Sample(id=sample_id, name=name, avgProductionTime=avgProductionTime, yield_=yield_)
        self._sample_repository.add(sample)
        return sample

    def get_all_samples(self) -> list[Sample]:
        return self._sample_repository.get_all()

    def search_samples_by_name(self, keyword: str) -> list[Sample]:
        return self._sample_repository.find_by_name(keyword)
