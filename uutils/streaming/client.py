import socket
import time

import cv2
import mss
import numpy

from zlib import decompress
import lz4.frame

import pygame

WIDTH = 1280
HEIGHT = 720

def recvall(conn, length):
    """ Retreive all pixels. """

    buf = b''
    while len(buf) < length:
        data = conn.recv(length - len(buf))
        if not data:
            return data
        buf += data
    return buf

def main(host='192.168.50.210', port=4000):
    title = "[MSS] FPS benchmark"
    new_frame_time, prev_frame_time, fps = 0, 0, 0
    last_time = time.time()

    font = cv2.FONT_HERSHEY_SIMPLEX
    watching = True    

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    try:
        while watching:
            print("STEP 1")

            # Retreive the size of the pixels length, the pixels length and pixels
            size_len = int.from_bytes(sock.recv(1), byteorder='big')
            print(f"step 1.1 (size_len = {size_len})")
            size = int.from_bytes(recvall(sock, size_len), byteorder='big')
            print(f"step 1.2 (size = {size})")
            pixels_recvd = recvall(sock, size)
            # pixels = decompress(pixels_recvd)
            pixels = lz4.frame.decompress(pixels_recvd)

            print(f"STEP 2 (size = {len(pixels_recvd)})")

            # convert received pixels to cv2 image
            buf_as_np_array = numpy.frombuffer(pixels, numpy.uint8)
            rgb = buf_as_np_array.reshape(HEIGHT, WIDTH, 3)
            img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

            print("STEP 3")

            # calc fps
            new_frame_time = time.time()
            fps = 1/(new_frame_time-prev_frame_time)
            prev_frame_time = new_frame_time
            fps = int(fps)

            # display fps
            cv2.putText(img, str(fps), (7, 40), font, 1, (100, 255, 0), 3, cv2.LINE_AA)

            # display grabbed image (480p)
            # imS = cv2.resize(img, (854, 480))
            cv2.imshow(title, img)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                cv2.destroyAllWindows()
                break
    finally:
        sock.close()

if __name__ == '__main__':
    main()