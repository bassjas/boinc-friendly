from enum import IntFlag
import logging
import time
from datetime import datetime, timedelta
from boinc import Boinc
from top import Top
import sys
import signal

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

class Boinc_Server:
    def __init__(this, num_cpus=1, steal_bump_down=1, steal_emergency=10):
        this.total_cpus = num_cpus
        this.steal_bump_down = steal_bump_down
        this.steal_emergency = steal_emergency
        this.loop_num = 0
        this.raise_delay = 0

        # Read current boinc values for this server
        this.boinc = Boinc()
        this.boinc.read_global_prefs()
        this.current_cpus = int(this.boinc.get_max_cpus() * this.total_cpus / 100)
        this.current_limit = this.boinc.get_cpu_limit()

    def at_maximum(this):
        return this.current_cpus == this.total_cpus and this.current_limit == 100

    def at_minimum(this):
        return this.current_cpus == 1 and this.current_limit <= 20

    def cpu_as_percent(this):
        """ Return the current number of CPUs in use as a percentage of total CPUs"""
        return int(this.current_cpus / this.total_cpus * 100)

    def bump_down(this, emergency=False):
        """
            Parameters:
            emergency - if True, immediately drop to lowest level of effort

            Return Values:
            rv - True if we decreased the level of effort, False otherwise
        """
        rv = True
        if emergency:
            this.current_cpus = 1
            this.current_limit = 20
            this.boinc.set_max_cpus(this.cpu_as_percent())
            this.boinc.set_cpu_limit(this.current_limit)
        elif this.current_cpus > 1:
            this.current_cpus -= 1
            this.boinc.set_max_cpus(this.cpu_as_percent())
        elif this.current_limit > 20:
            this.current_limit -= 10
            this.boinc.set_cpu_limit(this.current_limit)
        else:
            # Nothing to do: already at lowest level of effort
            rv = False

        return rv

    def bump_up(this):
        """
            Return Values:
            rv - True if we increased the level of effort, False otherwise
        """
        rv = True
        if this.current_limit < 91:
            this.current_limit += 10
            this.boinc.set_cpu_limit(this.current_limit)
        elif this.current_cpus < this.total_cpus:
            this.current_cpus += 1
            this.boinc.set_max_cpus(this.cpu_as_percent())
        else:
            # Already at highest level of effort
            rv = False

        return rv

    def status(this):
        """Can be called to log and return operational status, maybe at a given interval
            or when a signal is caught"""
        rv = "Loop: {}; raise delay: {}; cpus: {}; limit: {}%".format(this.loop_num, 
            this.raise_delay, this.current_cpus, this.current_limit)
        logger.info(rv)
        return rv

    def boinc_loop(this):
        logger.info("Beginning loop")
        logger.info("Max cpus: %i%%; cpu limit: %i%%", this.boinc.get_max_cpus(),
                this.boinc.get_cpu_limit())
        this.raise_delay = 0
        this.loop_num = 0
        #while True:
        while True:
            this.loop_num += 1
            # Average steal time from top for 10 seconds
            seconds = 10
            steal = 0
            for counter in range(seconds):
                steal += Top().get_stealtime()
                time.sleep(1)
            stealtime = steal / seconds
            
            # Does steal time indicate we should bump up or down?
            rv = False
            if stealtime > this.steal_bump_down:
                this.raise_delay = 0
                rv = this.bump_down(stealtime > this.steal_emergency)
            elif this.raise_delay > 2:
                this.raise_delay = 0
                rv = this.bump_up()
            elif not this.at_maximum():
                this.raise_delay += 1
                logger.debug("Loop: %i; Steal: %.1f; incrementing raise delay: %i", 
                    this.loop_num, stealtime, this.raise_delay)
            
            if rv:
                logger.info("Loop: %i; Steal: %.1f; cpus: %i; limit: %i%%", 
                    this.loop_num, stealtime, this.boinc.get_max_cpus(), this.boinc.get_cpu_limit())
                this.boinc.write_global_prefs()
                this.boinc.reload_global_prefs()
    

    
