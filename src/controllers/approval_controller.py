from src.services.approval_service import ApprovalService
from src.views.approval_view import ApprovalView
from src.views.display import input_prompt, print_divider, print_error, print_header


class ApprovalController:
    def __init__(
        self,
        service: ApprovalService,
        view: ApprovalView,
    ) -> None:
        self._service = service
        self._view = view

    def run(self) -> None:
        while True:
            reserved_orders = self._service.get_reserved_orders()
            self._view.render_reserved_list(reserved_orders)

            print_header("주문 승인 / 거절")
            print("  (1) 승인")
            print("  (2) 거절")
            print("  (0) 돌아가기")
            print_divider()

            choice = input_prompt("선택")

            if choice == "1":
                self._handle_approve()
            elif choice == "2":
                self._handle_reject()
            elif choice == "0":
                break
            else:
                print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")

    def _handle_approve(self) -> None:
        print_header("주문 승인 / 거절 > 승인")
        print()

        while True:
            order_id = input_prompt("주문 ID        ")
            if not order_id:
                print_error("주문 ID를 입력해 주세요.")
                continue

            try:
                order = self._service.approve_order(order_id)
                break
            except ValueError as e:
                print_error(str(e))
                continue

        self._view.render_approved(order)

    def _handle_reject(self) -> None:
        print_header("주문 승인 / 거절 > 거절")
        print()

        while True:
            order_id = input_prompt("주문 ID        ")
            if not order_id:
                print_error("주문 ID를 입력해 주세요.")
                continue

            try:
                order = self._service.reject_order(order_id)
                break
            except ValueError as e:
                print_error(str(e))
                continue

        self._view.render_rejected(order)
