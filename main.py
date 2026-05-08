import src.database as _database
from src.controllers.approval_controller import ApprovalController
from src.controllers.monitoring_controller import MonitoringController
from src.controllers.order_controller import OrderController
from src.controllers.production_controller import ProductionController
from src.controllers.sample_controller import SampleController
from src.controllers.shipment_controller import ShipmentController
from src.database import init_db
from src.repositories.order_repository import OrderRepository
from src.repositories.production_queue import ProductionQueue
from src.repositories.sample_repository import SampleRepository
from src.services.approval_service import ApprovalService
from src.services.monitoring_service import MonitoringService
from src.services.order_service import OrderService
from src.services.production_service import ProductionService
from src.services.sample_service import SampleService
from src.services.shipment_service import ShipmentService
from src.views.approval_view import ApprovalView
from src.views.display import Color, colorize, input_prompt, print_error
from src.views.monitoring_view import MonitoringView
from src.views.order_view import OrderView
from src.views.production_view import ProductionView
from src.views.sample_view import SampleView
from src.views.shipment_view import ShipmentView


def _print_main_menu(
    sample_count: int,
    total_stock: int,
    reserved_count: int,
    producing_count: int,
) -> None:
    print("\n+======================================================+")
    print("|     S-Semi 반도체 시료 생산 주문 관리 시스템          |")
    print("+======================================================+")
    print(f"|  시료: {sample_count}종  총재고: {total_stock}개  "
          f"대기: {colorize(str(reserved_count), Color.BLUE)}건  "
          f"생산중: {colorize(str(producing_count), Color.YELLOW)}건")
    print("+======================================================+")
    print("|  (1) 시료 관리                                       |")
    print("|  (2) 시료 주문                                       |")
    print("|  (3) 주문 승인 / 거절                                |")
    print("|  (4) 모니터링                                        |")
    print("|  (5) 생산 라인 조회                                  |")
    print("|  (6) 출고 처리                                       |")
    print("|  (0) 종료                                            |")
    print("+======================================================+")


def main(
    sample_repository: SampleRepository | None = None,
    order_repository: OrderRepository | None = None,
    production_queue: ProductionQueue | None = None,
) -> None:
    init_db(_database.DB_PATH)
    if sample_repository is None:
        sample_repository = SampleRepository()
    if order_repository is None:
        order_repository = OrderRepository()
    if production_queue is None:
        production_queue = ProductionQueue()

    sample_service = SampleService(sample_repository)
    sample_view = SampleView()
    sample_controller = SampleController(sample_service, sample_view)

    order_service = OrderService(sample_repository, order_repository)
    order_view = OrderView()
    order_controller = OrderController(order_service, order_view)

    approval_service = ApprovalService(sample_repository, order_repository, production_queue)
    approval_view = ApprovalView()
    approval_controller = ApprovalController(approval_service, approval_view, order_repository)

    monitoring_service = MonitoringService(sample_repository, order_repository)
    monitoring_view = MonitoringView()
    monitoring_controller = MonitoringController(monitoring_service, monitoring_view)

    production_service = ProductionService(sample_repository, order_repository, production_queue)
    production_view = ProductionView()
    production_controller = ProductionController(production_service, sample_service, production_view)

    shipment_service = ShipmentService(sample_repository, order_repository)
    shipment_view = ShipmentView()
    shipment_controller = ShipmentController(shipment_service, sample_service, shipment_view)

    while True:
        samples = sample_service.get_all_samples()
        sample_count = len(samples)
        total_stock = sum(s.stock for s in samples)
        summary = monitoring_service.get_order_summary()
        reserved_count = summary["counts"].get("RESERVED", 0)
        producing_count = summary["counts"].get("PRODUCING", 0)

        _print_main_menu(sample_count, total_stock, reserved_count, producing_count)
        choice = input_prompt("선택")

        if choice == "1":
            sample_controller.run()
        elif choice == "2":
            order_controller.run()
        elif choice == "3":
            approval_controller.run()
        elif choice == "4":
            monitoring_controller.run()
        elif choice == "5":
            production_controller.run()
        elif choice == "6":
            shipment_controller.run()
        elif choice == "0":
            print("\n  시스템을 종료합니다.")
            break
        else:
            print_error("유효하지 않은 메뉴 번호입니다. 다시 입력해 주세요.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  시스템을 종료합니다.")
