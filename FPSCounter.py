import time


class FPSCounter:
    def __init__(self):
        self.start_time = time.time()
        self.frame_count = 0

    def increment_frame_count(self):
        self.frame_count += 1

    def get_fps(self):
        elapsed_time = time.time() - self.start_time
        if elapsed_time > 0:
            fps = self.frame_count / elapsed_time
            return fps
        else:
            return 0

    def get_elapsed_time(self):
        return time.time() - self.start_time

    def reset_elapsed_time(self):
        now = time.time()
        ret = now - self.start_time
        self.start_time = now
        return ret

    def reset(self):
        self.start_time = time.time()
        self.frame_count = 0


'''
# Example usage:
fps_counter = FPSCounter()

# call do_fps_counting in main loop
def do_fps_counting(report_frequency=30):
    fps_counter.increment_frame_count()
    if fps_counter.frame_count > report_frequency:
        fps = fps_counter.get_fps()
        fps_counter.reset()
        return f"FPS: {fps:.2f}"

while in_loop:    
    fps = do_fps_counting()  # will return an output every 30 loops by default
        if fps:
            print(f'Achieving {fps} loops per second')
'''
