DIVIDER = "-" * 60


def print_header(title: str) -> None:
    print(f"\n[ {title} ]")
    print(DIVIDER)


def print_divider() -> None:
    print(DIVIDER)


def print_success(message: str) -> None:
    print(f"  [완료] {message}")


def print_error(message: str) -> None:
    print(f"  [오류] {message}")


def input_prompt(label: str) -> str:
    return input(f"  {label} >> ").strip()


def pause(message: str = "이전 메뉴로 돌아갑니다") -> None:
    input(f"\n  엔터를 누르면 {message}.")
