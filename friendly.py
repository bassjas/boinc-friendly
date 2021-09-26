import logging
import re
import subprocess
import time
from datetime import datetime, timedelta
from top import Top

#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('/var/log/stealmon.log')
fh.setLevel(logging.DEBUG)
# create console handler that does not show DEBUG but only
# INFO and above
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s:%(levelname)s: %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

class Boinc:

    _global_filename = '/var/lib/boinc/global_prefs_override.xml'
    #_global_filename = 'c:/Users/bassj/Projects/Stealmon/global_prefs_override.xml'
    
    def __init__(self):
        self.max_ncpus_pct = 0
        self.cpu_usage_limit = 0        

    def get_max_cpus(self):
        return self.max_ncpus_pct

    def set_max_cpus(self, pct):
        if pct < 0 or pct > 100:
            raise ValueError("Requires percentage from 0 to 100")
        self.max_ncpus_pct = pct

    def get_cpu_limit(self):
        return self.cpu_usage_limit

    def set_cpu_limit(self, pct):
        if pct < 0 or pct > 100:
            raise ValueError("Requires percentage from 0 to 100")
        self.cpu_usage_limit = pct

    def read_global_prefs(self):
        f = open(self._global_filename)
        for line in f.readlines():
            if 'max_ncpus_pct' in line:
                left_caret = line.index('>')
                right_caret = line.rindex('<')
                self.max_ncpus_pct = int(line[left_caret + 1:right_caret])
                
            elif 'cpu_usage_limit' in line:
                left_caret = line.index('>')
                right_caret = line.rindex('<')
                self.cpu_usage_limit = int(line[left_caret + 1:right_caret])

    def write_global_prefs(self):
        f = open(self._global_filename, 'w')
        f.write("""
<global_preferences>
    <max_ncpus_pct>{}</max_ncpus_pct>
    <cpu_usage_limit>{}</cpu_usage_limit>
</global_preferences>""".format(self.max_ncpus_pct, self.cpu_usage_limit))

    def reload_global_prefs(self):
        """Execute shell command to reload BOINC global preferences"""
        process = subprocess.run(['boinccmd','--read_global_prefs_override'], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            universal_newlines=True)
        return process.returncode
             
    def _main():
        b = Boinc()
        print("Max number of CPUs: {}".format(b.get_max_cpus()))
        print("Max CPU workload: {}".format(b.get_cpu_limit()))

        b.read_global_prefs()
        print("Max number of CPUs: {}".format(b.get_max_cpus()))
        print("Max CPU workload: {}".format(b.get_cpu_limit()))

        b.set_max_cpus(100)
        b.set_cpu_limit(100)
        b.write_global_prefs()
        print("Max number of CPUs: {}".format(b.get_max_cpus()))
        print("Max CPU workload: {}".format(b.get_cpu_limit()))

def cpu_limit(steal_time):
    # If steal_time is greater than X : Y is new percent of CPUs to use
    thresholds = {
        45 : 20,
        25 : 40,
        15 : 60,
        5 : 80,
    }

    rv = 100
    for level, threshold in thresholds.items():
        if steal_time > level:
            rv = threshold
            break
    return rv

def cpu_bump_up(current_cpu):
    """Given a "current" cpu percentage, return the next highest cpu percentage
    we could bump up to
    """
    # This should be an exact copy of the thresholds array in cpu_limit()
    thresholds = {
        45 : 20,
        25 : 40,
        15 : 60,
        5 : 80,
    }
    rv = 100
    for level, threshold in thresholds.items():
        if threshold > current_cpu):
            rv = threshold
            break
    return rv

def set_boinc(boinc, cpus = 100, limit = 100):
    logger.debug("Setting max_ncpus_pct = %i; cpu_usage_limit = %i",
                            cpus, limit)
    boinc.set_max_cpus(cpus)
    boinc.set_cpu_limit(limit)
    boinc.write_global_prefs()
    boinc.reload_global_prefs()

def main():

# I started this "while True" thing to make a daemon out of friendly.py
# but if I did that I'd want to use top rather than sar as my source of
# info because sar doesn't really change minute-by-minute.
# I should probably start a new file to do that. Or add a new class
# to handle top.
    raise_delay = 0
    while True:
        # Average steal time from top for 10 seconds
        for steal in range(10):
            steal += Top().get_stealtime()
            time.sleep(1)
        stealtime = steal / 10
        
        # Get current level of BIONC effort
        boinc = Boinc()
        boinc.read_global_prefs()

        cpus = cpu_limit(stealtime)
        if boinc.get_max_cpus() == cpus:
            # CPUs are set at the correct level for the given steal time.
            # Reset the raise_delay because conditions are not met to 
            # raise the CPU
            raise_delay = 0
        elif boinc.get_max_cpus() > cpus:
            # Turn down cpus right away
            logger.info("Steal: %.1f; Setting cpu%% to %i", stealtime, cpus)
            set_boinc(boinc,cpus)
            raise_delay = 0
        elif boinc.get_max_cpus() < cpus:
            # We turn up cpus slowly, using a delay since last change
            if raise_delay > 3:
                cpus = cpu_bump_up(boinc.get_max_cpus())
                logger.info("Steal: %.1f; Setting cpu%% to %i", stealtime, cpus)
                set_boinc(boinc, cpus)
                raise_delay = 0
            else:
                raise_delay += 1
                logger.debug("Steal: %.1f; incrementing raise delay: %i", stealtime, raise_delay)


if __name__ == "__main__":
    main()