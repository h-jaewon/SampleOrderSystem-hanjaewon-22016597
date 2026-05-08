from src.models.order import Order
from src.models.production_job import ProductionJob
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


class ProductionView:
    def render_status(self, status: dict, samples_map: dict) -> None:
        print_header("생산 라인 조회")

        current = status["current"]
        queue = status["queue"]

        if current is None:
            print("  현재 진행 중인 생산 작업이 없습니다.")
        else:
            job: ProductionJob = current["job"]
            sample = samples_map.get(job.sampleId)
            sample_name = sample.name if sample else job.sampleId
            print("\n  [현재 생산 중]")
            headers = ["주문 ID", "시료명", "주문 수량", "생산 수량", "예상 완료 시간(h)"]
            col_widths = [10, 14, 10, 10, 16]
            rows = [
                [
                    job.orderId,
                    sample_name,
                    str(current["quantity"]),
                    str(job.plannedQuantity),
                    f"{job.totalProductionTime:.1f}",
                ]
            ]
            print_table(headers, rows, col_widths)

        if queue:
            print("\n  [생산 대기 큐]")
            headers2 = ["순번", "주문 ID", "시료명", "주문 수량", "생산 수량", "예상 완료 시간(h)"]
            col_widths2 = [4, 10, 14, 10, 10, 16]
            rows2 = []
            for idx, item in enumerate(queue, start=1):
                job2: ProductionJob = item["job"]
                sample2 = samples_map.get(job2.sampleId)
                sample_name2 = sample2.name if sample2 else job2.sampleId
                rows2.append([
                    str(idx),
                    job2.orderId,
                    sample_name2,
                    str(item["quantity"]),
                    str(job2.plannedQuantity),
                    f"{job2.totalProductionTime:.1f}",
                ])
            print_table(headers2, rows2, col_widths2)

    def render_completed(self, order: Order, job: ProductionJob, sample: Sample) -> None:
        print()
        print_divider()
        print_success("생산이 완료되었습니다. (PRODUCING → CONFIRMED)")
        print(f"    주문 ID   : {order.id}")
        print(f"    시료명    : {sample.name}")
        print(f"    주문 수량 : {order.quantity} 개")
        stock_before = sample.stock - job.plannedQuantity
        print(f"    재고 변동 : {stock_before} 개 → {sample.stock} 개 (+{job.plannedQuantity})")
        print(f"    상태      : {colorize('PRODUCING', Color.YELLOW)} → {colorize(order.status.value, Color.GREEN)}")
        pause()

    def render_empty(self) -> None:
        print("\n  진행 중인 생산 작업이 없습니다.")
        pause()

    def render_error(self, message: str) -> None:
        print_error(message)
