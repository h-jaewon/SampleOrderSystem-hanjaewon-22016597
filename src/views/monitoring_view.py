from src.models.order import Order, OrderStatus
from src.views.display import (
    Color,
    colorize,
    pause,
    print_header,
    print_table,
)

_STATUS_COLORS = {
    OrderStatus.RESERVED.value: Color.BLUE,
    OrderStatus.PRODUCING.value: Color.YELLOW,
    OrderStatus.CONFIRMED.value: Color.GREEN,
    OrderStatus.RELEASED.value: Color.CYAN,
}

_MONITORED_STATUSES = [
    OrderStatus.RESERVED.value,
    OrderStatus.PRODUCING.value,
    OrderStatus.CONFIRMED.value,
    OrderStatus.RELEASED.value,
]

_STOCK_COLORS = {
    "여유": Color.GREEN,
    "부족": Color.YELLOW,
    "고갈": Color.RED,
}


class MonitoringView:
    def render_order_summary(self, summary: dict) -> None:
        print_header("모니터링 > 주문량 확인")
        counts: dict[str, int] = summary["counts"]
        orders: dict[str, list[Order]] = summary["orders"]

        print("\n  [상태별 주문 건수]")
        headers = ["상태", "건수"]
        col_widths = [12, 6]
        rows = [
            [colorize(status, _STATUS_COLORS.get(status, "")), str(counts[status])]
            for status in _MONITORED_STATUSES
        ]
        print_table(headers, rows, col_widths)

        for status in _MONITORED_STATUSES:
            status_orders = orders[status]
            if not status_orders:
                continue
            color = _STATUS_COLORS.get(status, "")
            print(f"\n  [{colorize(status, color)} 주문 목록]")
            headers2 = ["주문 ID", "시료 ID", "고객명", "수량"]
            col_widths2 = [10, 10, 14, 6]
            rows2 = [
                [o.id, o.sampleId, o.customerName, str(o.quantity)]
                for o in status_orders
            ]
            print_table(headers2, rows2, col_widths2)

        pause()

    def render_stock_status(self, stock_list: list[dict]) -> None:
        print_header("모니터링 > 재고량 확인")
        if not stock_list:
            print("  등록된 시료가 없습니다.")
            pause()
            return

        headers = ["시료 ID", "시료명", "현재 재고", "상태"]
        col_widths = [8, 16, 10, 6]
        rows = [
            [
                item["sample"].id,
                item["sample"].name,
                str(item["sample"].stock),
                colorize(item["status"], _STOCK_COLORS.get(item["status"], "")),
            ]
            for item in stock_list
        ]
        print_table(headers, rows, col_widths)
        pause()
