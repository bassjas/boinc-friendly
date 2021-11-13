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

    def get_average(self, seconds = 1):
        """
        Return the average stealtime over the last n seconds.
        If we have less than n seconds of data use it all.
        """
        # It's an error if seconds is not >=1 and <=600
        if seconds > len(self.dq):
            seconds = len(self.dq)
        mylist = list(self.dq)[:seconds]
        total = 0
        for i in mylist:
            total = total + i
        return int(total / seconds)

    def runProcess(self, exe):    
        p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while(True):
            # returns None while subprocess is running
            retcode = p.poll() 
            line = p.stdout.readline()
            yield line
            if retcode is not None:
                break 

    def loop(self):
        """
        Start the subprocess that will run vmstat.
        Loop over the output and extract the stealtime values.
        """
        for line in self.runProcess('/usr/bin/vmstat 1'.split()):
            line = line.rstrip()
            first, last = line.rsplit(maxsplit=1)
            try:
                stealtime = int(last)
                self.dq.appendleft(stealtime)
                print(self.dq)
            except ValueError:
                pass # vmstat periodically prints column headers, not data

    def _main():
        sq = StealQueue()
        t1 = threading.Thread(target=sq.loop)
        t1.start()

        while True:
            time.sleep(3)
            print('From main thread: average = {}'.format(sq.get_average(5)))
    
if __name__ == "__main__":
    StealQueue._main()