import hashlib
import time

class Utils():
    def test_hashrate():
        timeout = time.time() + 1

        nonse = 0
        hashes = 0

        while True:
            if time.time() >= timeout:
                break

            nonse += 1
            hashlib.sha256(str(nonse).encode())
            hashes += 1

        return hashes