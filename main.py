from src.repositories.sample_repository import SampleRepository
from src.services.sample_service import SampleService
from src.ui.display import input_prompt, print_error
from src.ui.sample_menu import show_sample_menu


def _print_main_menu() -> None:
    print("\n+======================================================+")
    print("|     S-Semi 반도체 시료 생산 주문 관리 시스템          |")
    print("+======================================================+")
    print("|  (1) 시료 관리                                       |")
    print("|  (2) 시료 주문           (준비 중)                   |")
    print("|  (3) 주문 승인 / 거절    (준비 중)                   |")
    print("|  (4) 모니터링            (준비 중)                   |")
    print("|  (5) 생산 라인 조회      (준비 중)                   |")
    print("|  (6) 출고 처리           (준비 중)                   |")
    print("|  (0) 종료                                            |")
    print("+======================================================+")


def main() -> None:
    sample_repository = SampleRepository()
    sample_service = SampleService(sample_repository)

    while True:
        _print_main_menu()
        choice = input_prompt("선택")

        if choice == "1":
            show_sample_menu(sample_service)
        elif choice in ("2", "3", "4", "5", "6"):
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
