from src.models.order import Order
from src.views.display import pause, print_divider, print_success


class OrderView:
    def render_placed(self, order: Order) -> None:
        print()
        print_divider()
        print_success("주문이 접수되었습니다.")
        print(f"    주문 ID   : {order.id}")
        print(f"    시료 ID   : {order.sampleId}")
        print(f"    고객명    : {order.customerName}")
        print(f"    수량      : {order.quantity} 개")
        print(f"    상태      : {order.status.value}")
        pause()

