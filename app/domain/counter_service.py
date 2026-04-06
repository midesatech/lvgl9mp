# Caso de uso: contador de clicks
class CounterService:
    """Caso de uso: mantener y consultar un contador."""

    def __init__(self):
        self._count = 0

    def increment(self):
        self._count += 1
        print("[CounterService] Click #{} registrado".format(self._count))

    def reset(self):
        self._count = 0

    @property
    def value(self) -> int:
        return self._count
