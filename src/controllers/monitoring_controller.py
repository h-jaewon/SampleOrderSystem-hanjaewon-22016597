from src.services.monitoring_service import MonitoringService
from src.views.display import input_prompt, print_divider, print_error, print_header
from src.views.monitoring_view import MonitoringView


class MonitoringController:
    def __init__(
        self,
        monitoring_service: MonitoringService,
        monitoring_view: MonitoringView,
    ) -> None:
        self._service = monitoring_service
        self._view = monitoring_view

    def run(self) -> None:
        while True:
            print_header("모니터링")
            print("  (1) 주문량 확인")
            print("  (2) 재고량 확인")
            print("  (0) 돌아가기")
            print_divider()

            choice = input_prompt("선택")

            if choice == "1":
                summary = self._service.get_order_summary()
                self._view.render_order_summary(summary)
            elif choice == "2":
                stock_list = self._service.get_stock_status()
                self._view.render_stock_status(stock_list)
            elif choice == "0":
                break
            else:
                print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")
