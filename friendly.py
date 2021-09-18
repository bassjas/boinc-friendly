import logging
import re
import subprocess
from datetime import datetime, timedelta

logging.basicConfig(filename='/var/log/stealmon.log', level=logging.INFO,
        format='%(asctime)s:%(levelname)s: %(message)s')


class Sysstat:

    # Eventually execute system command to get current sar data.
    # For now, fake it.
    _sample = """09:35:01 PM     CPU     %user     %nice   %system   %iowait    %steal     %idle
09:45:01 PM     all      1.27     79.32     18.95      0.00      0.46      0.00
09:55:01 PM     all      1.28     79.18     19.10      0.00      0.43      0.02
Average:        all      1.21     66.69     31.64      0.00      0.40      0.05"""

    def _split_sar_line(line):
        return re.split('  +', line)

    def _get_last_line(input):
        input = str(input)
        newline = input.strip().rindex('\n')
        lastline = input[newline + 1:]
        lastline = Sysstat._split_sar_line(lastline)
        return lastline

    def _sar(mins_ago):
        #sar_data = Sysstat._sample
        hourago = datetime.today() - timedelta(minutes=mins_ago)
        timestring = hourago.strftime('%H:%M')
        process = subprocess.run(['sar', '-s', '{}'.format(timestring), '-u'], 
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
            universal_newlines=True)

        final_line = Sysstat._get_last_line(process.stdout)
        data = {}
        data["user"] = float(final_line[2])
        data['nice'] = float(final_line[3])
        data['system'] = float(final_line[4])
        data['iowait'] = float(final_line[5])
        data['steal'] = float(final_line[6])
        data['idle'] = float(final_line[7])
        return data
        
    def __init__(self, minutes=60):
        """Gather sar data averaged from minutes ago"""
        self.data = Sysstat._sar(minutes)

    def get_steal_time(self):
        return self.data['steal']
    
    def _main():
        stat = Sysstat()
        print("Current steal time: {}".format(stat.get_steal_time()))

    

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
        f.write(
"""<global_preferences>
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


def set_boinc_lower(boinc):
    cpus = new_cpus = boinc.get_max_cpus() # Number of CPUs assigned to BOINC
    limit = new_limit = boinc.get_cpu_limit() # per-CPU workload in percent

    if cpus == 25 and limit == 50: # Already at lowest setting
        logging.debug("Already at lowest setting")
        return

    if cpus > 25:
        new_cpus = cpus - 25
    if limit > 50:
        new_limit = 50
    
    # These are the lowest limits I'm prepared to go
    if new_cpus < 25:
        new_cpus = 25
    if limit < 50:
        new_limit = 50

    if new_cpus != cpus or new_limit != limit:
        set_boinc(new_cpus, new_limit)

def set_boinc_higher(boinc):
    cpus = new_cpus = boinc.get_max_cpus()
    limit = new_limit = boinc.get_cpu_limit()

    if cpus == 100 and limit == 100: # Already at highest setting
        return

    if limit < 100:
        new_limit = 100
    elif cpus < 100:
        new_cpus = cpus + 25

    # Enforce maximum value limit
    if new_cpus > 100:
        new_cpus = 100
    if new_limit > 100:
        new_limit = 100

    if new_cpus != cpus or new_limit != limit:
        set_boinc(new_cpus, new_limit)

def set_boinc(cpus, limit):
    logging.info("Setting max_ncpus_pct = %i; cpu_usage_limit = %i",
                            cpus, limit)
    boinc.set_max_cpus(cpus)
    boinc.set_cpu_limit(limit)
    boinc.write_global_prefs()
    boinc.reload_global_prefs()

def main():
    # Get sar stats for the last 60 minutes
    stats = Sysstat()
    
    # Get current level of BIONC effort
    boinc = Boinc()
    boinc.read_global_prefs()

    logging.info("Steal time: %f; ncpu_pct: %i; cpu_limit: %i",
            stats.get_steal_time(), boinc.get_max_cpus(),
            boinc.get_cpu_limit())

    if stats.get_steal_time() > 50 and boinc.get_max_cpus() > 25:
        logging.info("Setting BOINC to minimum")
        set_boinc(cpus = 25, limit = 50)
    elif stats.get_steal_time() > 20 and boinc.get_max_cpus() > 25:
        logging.info("Attempting to lower BOINC workload")
        set_boinc_lower(boinc)
    elif boinc.get_max_cpus() < 100:
        logging.info("Attempting to raise BOINC workload")
        set_boinc_higher(boinc)


if __name__ == "__main__":
    main()