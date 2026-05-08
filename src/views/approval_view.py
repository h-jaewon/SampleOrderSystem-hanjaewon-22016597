from src.models.order import Order, OrderStatus
from src.views.display import (
    Color,
    colorize,
    pause,
    print_divider,
    print_error,
    print_header,
    print_success,
    print_table,
)


class ApprovalView:
    def render_reserved_list(self, orders: list[Order]) -> None:
        print_header("주문 승인 / 거절")
        if not orders:
            print("  승인 대기 중인 주문이 없습니다.")
            return

        print("  승인 대기 중인 주문 목록")
        headers = ["주문 ID", "시료 ID", "고객명", "수량", "상태"]
        col_widths = [10, 10, 14, 6, 10]
        rows = [
            [
                order.id,
                order.sampleId,
                order.customerName,
                str(order.quantity),
                colorize(order.status.value, Color.BLUE),
            ]
            for order in orders
        ]
        print_table(headers, rows, col_widths)

    def render_approved(self, order: Order) -> None:
        print()
        print_divider()
        if order.status == OrderStatus.CONFIRMED:
            print_success("주문이 승인되었습니다. (재고 충분 → CONFIRMED)")
            colored_status = colorize(order.status.value, Color.GREEN)
        else:
            print_success("주문이 승인되었습니다. (재고 부족 → 생산 대기 등록)")
            colored_status = colorize(order.status.value, Color.YELLOW)
        print(f"    주문 ID   : {order.id}")
        print(f"    시료 ID   : {order.sampleId}")
        print(f"    고객명    : {order.customerName}")
        print(f"    수량      : {order.quantity} 개")
        print(f"    상태      : {colored_status}")
        pause()

    def render_rejected(self, order: Order) -> None:
        print()
        print_divider()
        print_success("주문이 거절되었습니다.")
        print(f"    주문 ID   : {order.id}")
        print(f"    시료 ID   : {order.sampleId}")
        print(f"    고객명    : {order.customerName}")
        print(f"    수량      : {order.quantity} 개")
        print(f"    상태      : {colorize(order.status.value, Color.RED)}")
        pause()

    def render_error(self, message: str) -> None:
        print_error(message)
