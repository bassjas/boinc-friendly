from enum import IntFlag
import logging
import time
from datetime import datetime, timedelta
from boinc import Boinc
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

class Boinc_Server:
    def __init__(this, num_cpus=1, steal_bump_down=1, steal_emergency=10):
        this.total_cpus = num_cpus
        this.steal_bump_down = steal_bump_down
        this.steal_emergency = steal_emergency
        this.current_cpus = num_cpus
        this.current_limit = 100

    def at_maximum(this):
        return this.current_cpus == this.total_cpus and this.current_limit == 100

    def at_minimum(this):
        return this.current_cpus == 1 and this.current_limit <= 20

    def bump_down(this, boinc, emergency=False):
        """
            Parameters:
            emergency - if True, immediately drop to lowest level of effort

            Return Values:
            rv - True if we decreased the level of effort, False otherwise
        """
        rv = True
        if emergency:
            boinc.set_max_cpus(int(100 / this.total_cpus))
            boinc.set_cpu_limit(20)
        elif this.current_cpus > 1:
            this.current_cpus -= 1
            boinc.set_max_cpus(int(this.current_cpus / this.total_cpus * 100))
        elif this.current_limit > 20:
            this.current_limit -= 10
            boinc.set_cpu_limit(this.current_limit)
        else:
            # Nothing to do: already at lowest level of effort
            rv = False

        return rv

    def bump_up(this, boinc):
        """
            Return Values:
            rv - True if we increased the level of effort, False otherwise
        """
        rv = True
        if this.current_limit < 100:
            this.current_limit += 10
            boinc.set_cpu_limit(this.current_limit)
        elif this.current_cpus < this.total_cpus:
            this.current_cpus += 1
            boinc.set_max_cpus(this.current_cpus)
        else:
            # Already at highest level of effort
            rv = False

        return rv

    def boinc_loop(this):
        logger.info("Beginning loop")
        raise_delay = 0
        loop_num = 0
        #while True:
        while True:
            loop_num += 1
            # Average steal time from top for 10 seconds
            seconds = 10
            steal = 0
            for counter in range(seconds):
                steal += Top().get_stealtime()
                time.sleep(1)
            stealtime = steal / seconds

            # Get current level of BIONC effort
            boinc = Boinc()
            #boinc.read_global_prefs()
            
            # Does steal time indicate we should bump up or down?
            rv = False
            if stealtime > this.steal_bump_down:
                raise_delay = 0
                rv = this.bump_down(boinc, stealtime > this.steal_emergency)
            elif raise_delay > 2:
                raise_delay = 0
                rv = this.bump_up(boinc)
            elif not this.at_maximum():
                raise_delay += 1
                logger.debug("Loop: %i; Steal: %.1f; incrementing raise delay: %i", 
                    loop_num, stealtime, raise_delay)
            
            if rv:
                logger.info("Loop: %i; Steal: %.1f; cpus: %i; limit: %i%%", 
                    loop_num, stealtime, boinc.get_max_cpus(), boinc.get_cpu_limit())
                boinc.write_global_prefs()
                boinc.reload_global_prefs()
    

    
