from collections import deque
import time
import threading
import subprocess

class StealQueue:
    """Return the current steal time, or an average steal time for the
    last 10 seconds, 1 minute, or 10 minutes.
    """

    # 1. Scrape steal time from 'vmstat' once per second.
    # 2. Enqueue each steal time value.
    # 3. When get_average() is called calculate the average steal time
    #    for the given number of seconds.
    #
    # What's the largest number of seconds we will allow? I don't want to keep infinite data.
    # Deque can have a max length and then allow the oldest data to slip out of the queue. That
    # keeps you from having infinite data.

    def __init__(self):
        self.dq = deque(maxlen = 600)

    def runProcess(self, exe):    
        p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while(True):
            # returns None while subprocess is running
            retcode = p.poll() 
            line = p.stdout.readline()
            yield line
            if retcode is not None:
                break

    

    def get_average(self, seconds = 1):
        pass

    def get_10sec(self):
        return self.get_average(10)

    def get_1min(self):
        return self.get_average(60)

    def get_5min(self):
        return self.get_average(300)

    def get_10min(self):
        return self.get_average(600)

    def start(self):
        for line in self.runProcess('/usr/bin/vmstat 1'.split()):
            line = line.rstrip()
            first, last = line.rsplit(" ", 1)
            print("steal: {}".format(last))

    def _main():
        sq = StealQueue()
        t1 = threading.Thread(target=sq.start)
        t1.start()

        while True:
            time.sleep(3)
            print('From main thread')
    
if __name__ == "__main__":
    StealQueue._main()