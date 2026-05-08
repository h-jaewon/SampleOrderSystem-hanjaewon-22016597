from src.models.order import Order
from src.models.sample import Sample
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


class ShipmentView:
    def render_confirmed_list(self, orders: list[Order], samples_map: dict) -> None:
        print_header("출고 처리")
        if not orders:
            print("  출고 대기 중인 주문이 없습니다.")
            return

        print("  출고 대기 중인 주문 목록 (CONFIRMED)")
        headers = ["주문 ID", "시료명", "고객명", "수량"]
        col_widths = [10, 14, 14, 6]
        rows = [
            [
                order.id,
                samples_map[order.sampleId].name if order.sampleId in samples_map else order.sampleId,
                order.customerName,
                str(order.quantity),
            ]
            for order in orders
        ]
        print_table(headers, rows, col_widths)

    def render_released(self, order: Order, sample: Sample, stock_before: int) -> None:
        print()
        print_divider()
        print_success("출고 처리가 완료되었습니다. (CONFIRMED → RELEASED)")
        print(f"    주문 ID   : {order.id}")
        print(f"    시료명    : {sample.name}")
        print(f"    고객명    : {order.customerName}")
        print(f"    출고 수량 : {order.quantity} 개")
        print(f"    재고 변동 : {stock_before} 개 → {stock_before - order.quantity} 개 (-{order.quantity})")
        print(f"    상태      : {colorize('CONFIRMED', Color.GREEN)} → {colorize(order.status.value, Color.CYAN)}")
        pause()

    def render_empty(self) -> None:
        print("\n  출고 대기 중인 주문이 없습니다.")
        pause()

    def render_error(self, message: str) -> None:
        print_error(message)
