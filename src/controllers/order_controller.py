from src.services.order_service import OrderService
from src.views.display import input_prompt, print_divider, print_error, print_header
from src.views.order_view import OrderView


class OrderController:
    def __init__(self, service: OrderService, view: OrderView) -> None:
        self._service = service
        self._view = view

    def run(self) -> None:
        while True:
            print_header("시료 주문")
            print("  (1) 주문 접수")
            print("  (0) 돌아가기")
            print_divider()

            choice = input_prompt("선택")

            if choice == "1":
                self._handle_place_order()
            elif choice == "0":
                break
            else:
                print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")

    def _handle_place_order(self) -> None:
        print_header("시료 주문 > 주문 접수")
        print()

        while True:
            sample_id = input_prompt("시료 ID        ")
            if not sample_id:
                print_error("시료 ID를 입력해 주세요.")
                continue

            customer_name = input_prompt("고객명         ")
            if not customer_name:
                print_error("고객명을 입력해 주세요.")
                continue

            quantity_raw = input_prompt("수량           ")
            try:
                quantity = int(quantity_raw)
            except ValueError:
                print_error("수량은 정수로 입력해 주세요.")
                continue

            try:
                order = self._service.place_order(sample_id, customer_name, quantity)
                break
            except ValueError as e:
                print_error(str(e))
                continue

        self._view.render_placed(order)
