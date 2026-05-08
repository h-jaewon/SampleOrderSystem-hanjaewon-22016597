import sys
import unicodedata

USE_COLOR = sys.stdout.isatty()

DIVIDER = "-" * 60


class Color:
    RESET  = "\033[0m"
    GREEN  = "\033[32m"
    YELLOW = "\033[33m"
    RED    = "\033[31m"
    BLUE   = "\033[34m"
    CYAN   = "\033[36m"
    BOLD   = "\033[1m"


def colorize(text: str, color: str) -> str:
    if not USE_COLOR:
        return text
    return f"{color}{text}{Color.RESET}"


def vlen(text: str) -> int:
    w = 0
    for ch in str(text):
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def ljust_v(text: str, width: int) -> str:
    text = str(text)
    padding = max(0, width - vlen(text))
    return text + " " * padding


def print_table(headers: list[str], rows: list[list[str]], col_widths: list[int]) -> None:
    def _border(left: str, mid: str, right: str, fill: str) -> str:
        parts = [fill * (w + 2) for w in col_widths]
        return left + mid.join(parts) + right

    def _row_line(cells: list[str], color: str | None = None) -> str:
        parts = []
        for cell, width in zip(cells, col_widths):
            padded = ljust_v(str(cell), width)
            if color and USE_COLOR:
                parts.append(f" {color}{padded}{Color.RESET} ")
            else:
                parts.append(f" {padded} ")
        return "│" + "│".join(parts) + "│"

    top = _border("┌", "┬", "┐", "─")
    mid = _border("├", "┼", "┤", "─")
    bot = _border("└", "┴", "┘", "─")

    print(top)
    print(_row_line(headers, color=Color.CYAN))
    for row in rows:
        print(mid)
        print(_row_line(row))
    print(bot)


def print_header(title: str) -> None:
    print(f"\n[ {title} ]")
    print(DIVIDER)


def print_divider() -> None:
    print(DIVIDER)


def print_success(message: str) -> None:
    msg = f"  [완료] {message}"
    print(colorize(msg, Color.GREEN))


def print_error(message: str) -> None:
    msg = f"  [오류] {message}"
    print(colorize(msg, Color.RED))


def input_prompt(label: str) -> str:
    return input(f"  {label} >> ").strip()


def pause(message: str = "이전 메뉴로 돌아갑니다") -> None:
    input(f"\n  엔터를 누르면 {message}.")
