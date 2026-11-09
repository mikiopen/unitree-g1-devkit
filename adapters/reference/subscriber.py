"""Static interface contract for a command subscriber; intentionally not executable."""

UDP_RECV_PORT = 2006
UDP_SEND_PORT = 3840


def describe_contract():
    """Keep calls inside a non-invoked function for static preflight inspection."""
    ChannelFactoryInitialize(0, "eth0")  # provided by a real vendor adapter


def forward_to_action_service(sock, payload):
    """Show the expected local forwarding endpoint without opening a socket."""
    sock.sendto(payload, ("127.0.0.1", 6789))
