from src.controllers.order_controller import OrderController
from src.controllers.sample_controller import SampleController
from src.repositories.order_repository import OrderRepository
from src.repositories.sample_repository import SampleRepository
from src.services.order_service import OrderService
from src.services.sample_service import SampleService
from src.views.display import input_prompt, print_error
from src.views.order_view import OrderView
from src.views.sample_view import SampleView


def _print_main_menu() -> None:
    print("\n+======================================================+")
    print("|     S-Semi 반도체 시료 생산 주문 관리 시스템          |")
    print("+======================================================+")
    print("|  (1) 시료 관리                                       |")
    print("|  (2) 시료 주문                                       |")
    print("|  (3) 주문 승인 / 거절    (준비 중)                   |")
    print("|  (4) 모니터링            (준비 중)                   |")
    print("|  (5) 생산 라인 조회      (준비 중)                   |")
    print("|  (6) 출고 처리           (준비 중)                   |")
    print("|  (0) 종료                                            |")
    print("+======================================================+")


def main(
    sample_repository: SampleRepository | None = None,
    order_repository: OrderRepository | None = None,
) -> None:
    if sample_repository is None:
        sample_repository = SampleRepository()
    if order_repository is None:
        order_repository = OrderRepository()

    sample_service = SampleService(sample_repository)
    sample_view = SampleView()
    sample_controller = SampleController(sample_service, sample_view)

    order_service = OrderService(sample_repository, order_repository)
    order_view = OrderView()
    order_controller = OrderController(order_service, order_view)

    while True:
        _print_main_menu()
        choice = input_prompt("선택")

        if choice == "1":
            sample_controller.run()
        elif choice == "2":
            order_controller.run()
        elif choice in ("3", "4", "5", "6"):
            print("\n  아직 준비 중인 기능입니다.")
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
