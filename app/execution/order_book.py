from app.execution.order import Order


class OrderBook:
    """
    Stores and manages orders.
    """

    def __init__(self):

        self.orders: list[Order] = []

        self.next_order_id = 1

    def add(self, order: Order):

        order.order_id = self.next_order_id

        self.next_order_id += 1

        self.orders.append(order)

        return order

    def get(self, order_id: int):

        for order in self.orders:

            if order.order_id == order_id:

                return order

        return None

    def pending(self):

        return [
            order
            for order in self.orders
            if order.status == "NEW"
        ]

    def all(self):

        return self.orders

    def count(self):

        return len(self.orders)