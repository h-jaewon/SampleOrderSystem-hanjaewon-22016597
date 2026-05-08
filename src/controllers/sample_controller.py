from src.services.sample_service import SampleService
from src.views.display import input_prompt, print_divider, print_error, print_header
from src.views.sample_view import SampleView


class SampleController:
    def __init__(self, service: SampleService, view: SampleView) -> None:
        self._service = service
        self._view = view

    def run(self) -> None:
        while True:
            print_header("시료 관리")
            print("  (1) 시료 등록")
            print("  (2) 시료 조회")
            print("  (3) 시료 검색")
            print("  (0) 돌아가기")
            print_divider()

            choice = input_prompt("선택")

            if choice == "1":
                self._handle_register()
            elif choice == "2":
                self._handle_list()
            elif choice == "3":
                self._handle_search()
            elif choice == "0":
                break
            else:
                print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")

    def _handle_register(self) -> None:
        print_header("시료 관리 > 시료 등록")
        print("  새로운 시료를 등록합니다.")
        print()

        while True:
            name = input_prompt("시료 이름       ")
            if not name:
                self._view.render_error("시료 이름은 필수 입력값입니다.")
                continue

            try:
                avg_time_raw = input_prompt("평균 생산시간(h)")
                avg_production_time = float(avg_time_raw)
            except ValueError:
                self._view.render_error("평균 생산시간은 숫자로 입력해 주세요.")
                continue

            try:
                yield_raw = input_prompt("수율 (0~1)     ")
                yield_ = float(yield_raw)
            except ValueError:
                self._view.render_error("수율은 숫자로 입력해 주세요.")
                continue

            try:
                sample = self._service.register_sample(name, avg_production_time, yield_)
                break
            except ValueError as e:
                self._view.render_error(str(e))

        self._view.render_registered(sample)

    def _handle_list(self) -> None:
        print_header("시료 관리 > 시료 조회")

        samples = self._service.get_all_samples()

        if not samples:
            self._view.render_empty()
            return

        self._view.render_list(samples)

    def _handle_search(self) -> None:
        print_header("시료 관리 > 시료 검색")
        print()

        keyword = input_prompt("검색어를 입력하세요")
        samples = self._service.search_samples_by_name(keyword)

        self._view.render_search_result(samples, keyword)
