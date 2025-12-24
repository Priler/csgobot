import socket
import time
from typing import Tuple

import cv2
import numpy as np
import lz4.frame


def recv_all(conn: socket.socket, length: int) -> bytes:
    buf = b""
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf


class StreamClient:

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 4000,
        resolution: Tuple[int, int] = (1280, 720),
    ):
        self.host = host
        self.port = port
        self.width, self.height = resolution
        self._socket: socket.socket = None

    def connect(self) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self.host, self.port))

    def disconnect(self) -> None:
        if self._socket:
            self._socket.close()
            self._socket = None

    def receive_frame(self) -> np.ndarray:
        size_len = int.from_bytes(self._socket.recv(1), byteorder="big")
        size = int.from_bytes(recv_all(self._socket, size_len), byteorder="big")
        compressed = recv_all(self._socket, size)
        pixels = lz4.frame.decompress(compressed)

        frame = np.frombuffer(pixels, dtype=np.uint8)
        frame = frame.reshape(self.height, self.width, 3)
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False


def run_viewer(host: str = "127.0.0.1", port: int = 4000) -> None:
    prev_time = time.time()
    font = cv2.FONT_HERSHEY_SIMPLEX

    with StreamClient(host, port) as client:
        while True:
            frame = client.receive_frame()

            now = time.time()
            fps = 1 / (now - prev_time) if now != prev_time else 0
            prev_time = now

            cv2.putText(frame, f"{int(fps)}", (7, 40), font, 1, (100, 255, 0), 3)
            cv2.imshow("Stream Viewer", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_viewer()
