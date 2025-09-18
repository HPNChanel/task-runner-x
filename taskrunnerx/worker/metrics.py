
from time import time


class Timer:
    def __enter__(self):
        self.start = time()
        return self
    
    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time() - self.start
