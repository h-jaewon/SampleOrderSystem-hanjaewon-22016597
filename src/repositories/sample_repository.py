from typing import Optional

from src.models.sample import Sample


class SampleRepository:
    def __init__(self) -> None:
        self._store: dict[str, Sample] = {}

    def add(self, sample: Sample) -> None:
        if sample.id in self._store:
            raise ValueError(f"이미 존재하는 시료 ID입니다: {sample.id}")
        self._store[sample.id] = sample

    def get(self, sample_id: str) -> Optional[Sample]:
        return self._store.get(sample_id)

    def get_all(self) -> list[Sample]:
        return list(self._store.values())

    def find_by_name(self, name: str) -> list[Sample]:
        keyword = name.lower()
        return [s for s in self._store.values() if keyword in s.name.lower()]
