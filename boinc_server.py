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
        this.num_cpus = num_cpus
        this.steal_bump_down = steal_bump_down
        this.steal_emergency = steal_emergency

    def at_maximum(this, boinc):
        return boinc.get_max_cpus() == this.num_cpus and boinc.get_cpu_limit() == 100

    def at_minimum(this, boinc):
        return boinc.get_max_cpus() == 1 and boinc.get_cpu_limit() == 20

    def bump_down(this, boinc, emergency=False):
        """
            Parameters:
            emergency - if True, immediately drop to lowest level of effort

            Return Values:
            rv - True if we decreased the level of effort, False otherwise
        """
        rv = True
        if emergency:
            boinc.set_max_cpus(1)
            boinc.set_cpu_limit(20)
        elif boinc.get_max_cpus() > 1:
            boinc.set_max_cpus(boinc.get_max_cpus() -1)
        elif boinc.get_cpu_limit() > 20:
            boinc.set_cpu_limit(boinc.get_cpu_limit() - 10)
        else:
            # Nothing to do: already at lowest level of effort
            rv = False

        if rv:
            boinc.write_global_prefs()
            boinc.reload_global_prefs()
        return rv

    def bump_up(this, boinc):
        """
            Return Values:
            rv - True if we increased the level of effort, False otherwise
        """
        rv = True
        if boinc.get_cpu_limit() < 100:
            boinc.set_cpu_limit(boinc.get_cpu_limit() + 10)
        elif boinc.get_max_cpus() < this.num_cpus:
            boinc.set_max_cpus(boinc.get_max_cpus() + 1)
        else:
            # Already at highest level of effort
            rv = False

        if rv:
            boinc.write_global_prefs()
            boinc.reload_global_prefs()
        return rv

    def boinc_loop(this):
        logger.info("Beginning loop")
        raise_delay = 0
        while True:
            # Average steal time from top for 10 seconds
            seconds = 10
            steal = 0
            for counter in range(seconds):
                steal += Top().get_stealtime()
                time.sleep(1)
            stealtime = steal / seconds

            # Get current level of BIONC effort
            boinc = Boinc()
            boinc.read_global_prefs()
            
            # Does steal time indicate we should bump up or down?
            if stealtime > this.steal_bump_down and not this.at_minimum(boinc):
                rv = this.bump_down(boinc, stealtime > this.steal_emergency)
                raise_delay = 0
                if rv:
                    logger.info("Steal: %.1f; lowered level of effort", stealtime)
            elif this.at_maximum(boinc):
                raise_delay = 0
            elif raise_delay > 2:
                raise_delay = 0
                rv = this.bump_up(boinc)
                if rv:
                    logger.info("Steal: %.1f; raised BOINC level of effort", stealtime)
            else:
                raise_delay += 1
                logger.debug("Steal: %.1f; incrementing raise delay: %i", stealtime, raise_delay)

    

    
