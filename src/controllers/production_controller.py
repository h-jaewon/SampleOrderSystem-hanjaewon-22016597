from src.services.production_service import ProductionService
from src.services.sample_service import SampleService
from src.views.display import input_prompt, print_divider, print_error, print_header
from src.views.production_view import ProductionView


class ProductionController:
    def __init__(
        self,
        production_service: ProductionService,
        sample_service: SampleService,
        production_view: ProductionView,
    ) -> None:
        self._service = production_service
        self._sample_service = sample_service
        self._view = production_view

    def run(self) -> None:
        while True:
            samples = self._sample_service.get_all_samples()
            samples_map = {s.id: s for s in samples}

            status = self._service.get_production_status()
            self._view.render_status(status, samples_map)

            print_header("생산 라인")
            print("  (1) 생산 완료 처리")
            print("  (0) 돌아가기")
            print_divider()

            choice = input_prompt("선택")

            if choice == "1":
                self._handle_complete(samples_map)
            elif choice == "0":
                break
            else:
                print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")

    def _handle_complete(self, samples_map: dict) -> None:
        # 완료 처리 전 현재 생산 중인 job 정보를 먼저 확인
        status_before = self._service.get_production_status()
        current = status_before.get("current")
        if current is None:
            self._view.render_empty()
            return

        job = current["job"]
        current_sample = samples_map.get(job.sampleId)
        stock_before = current_sample.stock if current_sample else 0

        try:
            order = self._service.complete_production()
        except ValueError as e:
            print_error(str(e))
            return

        # 완료 후 갱신된 시료 정보로 재고 변동 표시
        samples = self._sample_service.get_all_samples()
        updated_map = {s.id: s for s in samples}
        sample = updated_map.get(order.sampleId)
        self._view.render_completed(order, job, sample, stock_before)
