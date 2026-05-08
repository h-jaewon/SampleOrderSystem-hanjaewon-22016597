from src.models.sample import Sample
from src.services.sample_service import SampleService
from src.ui.display import (
    input_prompt,
    pause,
    print_divider,
    print_error,
    print_header,
    print_success,
)


def show_sample_menu(service: SampleService) -> None:
    while True:
        print_header("시료 관리")
        print("  (1) 시료 등록")
        print("  (2) 시료 조회")
        print("  (3) 시료 검색")
        print("  (0) 돌아가기")
        print_divider()

        choice = input_prompt("선택")

        if choice == "1":
            _register_sample(service)
        elif choice == "2":
            _list_samples(service)
        elif choice == "3":
            _search_samples(service)
        elif choice == "0":
            break
        else:
            print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")


def _register_sample(service: SampleService) -> None:
    print_header("시료 관리 > 시료 등록")
    print("  새로운 시료를 등록합니다.")
    print()

    while True:
        name = input_prompt("시료 이름       ")
        if not name:
            print_error("시료 이름은 필수 입력값입니다.")
            continue

        try:
            avg_time_raw = input_prompt("평균 생산시간(h)")
            avg_production_time = float(avg_time_raw)
        except ValueError:
            print_error("평균 생산시간은 숫자로 입력해 주세요.")
            continue

        try:
            yield_raw = input_prompt("수율 (0~1)     ")
            yield_ = float(yield_raw)
        except ValueError:
            print_error("수율은 숫자로 입력해 주세요.")
            continue

        try:
            sample = service.register_sample(name, avg_production_time, yield_)
            break
        except ValueError as e:
            print_error(str(e))

    print()
    print_divider()
    print_success("시료가 등록되었습니다.")
    print(f"    시료 ID : {sample.id}")
    print(f"    이름    : {sample.name}")
    print(f"    생산시간: {sample.avgProductionTime}h")
    print(f"    수율    : {int(sample.yield_ * 100)}%")
    pause()


def _list_samples(service: SampleService) -> None:
    print_header("시료 관리 > 시료 조회")

    samples = service.get_all_samples()

    if not samples:
        print("  등록된 시료가 없습니다.")
        pause()
        return

    print(f"  총 {len(samples)}종의 시료가 등록되어 있습니다.")
    print()
    _print_sample_table(samples)
    print_divider()
    pause()


def _search_samples(service: SampleService) -> None:
    print_header("시료 관리 > 시료 검색")
    print()

    keyword = input_prompt("검색어를 입력하세요")

    samples = service.search_samples_by_name(keyword)

    print()
    print_divider()

    if not samples:
        print("  검색 결과가 없습니다.")
        pause()
        return

    print(f"  검색 결과: {len(samples)}건")
    print()
    _print_sample_table(samples)
    print_divider()
    pause()


def _print_sample_table(samples: list[Sample]) -> None:
    header = f"  {'ID':<6}{'이름':<14}{'평균생산시간':<12}{'수율':<8}{'현재재고'}"
    separator = f"  {'----':<6}{'------------':<14}{'----------':<12}{'------':<8}{'--------'}"
    print(header)
    print(separator)
    for s in samples:
        yield_pct = f"{int(s.yield_ * 100)}%"
        avg_time = f"{s.avgProductionTime} h"
        stock = f"{s.stock}  개"
        print(f"  {s.id:<6}{s.name:<14}{avg_time:<12}{yield_pct:<8}{stock}")
