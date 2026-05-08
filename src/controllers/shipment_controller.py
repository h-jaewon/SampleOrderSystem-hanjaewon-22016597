from src.services.sample_service import SampleService
from src.services.shipment_service import ShipmentService
from src.views.display import input_prompt, print_divider, print_error, print_header
from src.views.shipment_view import ShipmentView


class ShipmentController:
    def __init__(
        self,
        shipment_service: ShipmentService,
        sample_service: SampleService,
        shipment_view: ShipmentView,
    ) -> None:
        self._service = shipment_service
        self._sample_service = sample_service
        self._view = shipment_view

    def run(self) -> None:
        while True:
            samples = self._sample_service.get_all_samples()
            samples_map = {s.id: s for s in samples}

            confirmed_orders = self._service.get_confirmed_orders()
            self._view.render_confirmed_list(confirmed_orders, samples_map)

            print_header("출고 처리")
            print("  (1) 출고 처리")
            print("  (0) 돌아가기")
            print_divider()

            choice = input_prompt("선택")

            if choice == "1":
                self._handle_release(samples_map)
            elif choice == "0":
                break
            else:
                print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")

    def _handle_release(self, samples_map: dict) -> None:
        print_header("출고 처리 > 주문 출고")
        print()

        while True:
            order_id = input_prompt("주문 ID        ")
            if not order_id:
                self._view.render_error("주문 ID를 입력해 주세요.")
                continue

            try:
                sample = samples_map.get(order_id)
                # 출고 전 재고를 확인하기 위해 확정 주문 목록에서 해당 주문의 시료 재고를 읽음
                confirmed = {o.id: o for o in self._service.get_confirmed_orders()}
                target_order = confirmed.get(order_id)
                if target_order:
                    pre_sample = samples_map.get(target_order.sampleId)
                    stock_before = pre_sample.stock if pre_sample else 0
                else:
                    stock_before = 0

                order = self._service.release_order(order_id)

                samples = self._sample_service.get_all_samples()
                updated_map = {s.id: s for s in samples}
                released_sample = updated_map.get(order.sampleId)

                self._view.render_released(order, released_sample, stock_before)
                break
            except ValueError as e:
                self._view.render_error(str(e))
                continue
