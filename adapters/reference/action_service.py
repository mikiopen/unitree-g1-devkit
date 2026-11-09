"""Static action-service contract; intentionally not executable."""

UDP_IP = "127.0.0.1"
UDP_PORT = 6789


class ReferenceActionService:
    def __init__(self):
        self.action_map = {
            "2001": {"path": "actions/init"},
            "2091": {"type": "emergency_stop"},
        }

    def describe_contract(self):
        ChannelFactoryInitialize(0, "eth0")  # provided by a real vendor adapter
