from src.models.sample import Sample
from src.views.display import (
    ljust_v,
    pause,
    print_divider,
    print_error,
    print_header,
    print_success,
    print_table,
)

_COL_WIDTHS = [6, 14, 12, 6, 8]
_HEADERS = ["ID", "이름", "평균생산시간", "수율", "현재재고"]


class SampleView:
    def render_registered(self, sample: Sample) -> None:
        print()
        print_divider()
        print_success("시료가 등록되었습니다.")
        print(f"    시료 ID : {sample.id}")
        print(f"    이름    : {sample.name}")
        print(f"    생산시간: {sample.avgProductionTime}h")
        print(f"    수율    : {int(sample.yield_ * 100)}%")
        pause()

    def render_list(self, samples: list[Sample]) -> None:
        print(f"  총 {len(samples)}종의 시료가 등록되어 있습니다.")
        print()
        self._print_sample_table(samples)
        print_divider()
        pause()

    def render_search_result(self, samples: list[Sample], keyword: str) -> None:
        print()
        print_divider()
        if not samples:
            print("  검색 결과가 없습니다.")
            pause()
            return
        print(f"  검색 결과: {len(samples)}건")
        print()
        self._print_sample_table(samples)
        print_divider()
        pause()

    def render_empty(self) -> None:
        print("  등록된 시료가 없습니다.")
        pause()

    def render_error(self, message: str) -> None:
        print_error(message)

    def _print_sample_table(self, samples: list[Sample]) -> None:
        rows = []
        for s in samples:
            yield_pct = f"{int(s.yield_ * 100)}%"
            avg_time = f"{s.avgProductionTime} h"
            stock = f"{s.stock}  개"
            rows.append([s.id, s.name, avg_time, yield_pct, stock])
        print_table(_HEADERS, rows, _COL_WIDTHS)
