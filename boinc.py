import subprocess
from top import Top

class Boinc:

    _global_filename = '/var/lib/boinc/global_prefs_override.xml'
    #_global_filename = 'c:/Users/bassj/Projects/Stealmon/global_prefs_override.xml'
    
    def __init__(self):
        self.max_ncpus = 0
        self.cpu_usage_limit = 0        

    def get_max_cpus(self):
        return self.max_ncpus

    def set_max_cpus(self, pct):
        if pct < 0 or pct > 100:
            raise ValueError("Requires percentage from 0 to 100")
        self.max_ncpus = pct

    def get_cpu_limit(self):
        return self.cpu_usage_limit

    def set_cpu_limit(self, pct):
        if pct < 0 or pct > 100:
            raise ValueError("Requires percentage from 0 to 100")
        self.cpu_usage_limit = pct

    def read_global_prefs(self):
        f = open(self._global_filename)
        for line in f.readlines():
            if 'max_ncpus' in line:
                left_caret = line.index('>')
                right_caret = line.rindex('<')
                self.max_ncpus = int(line[left_caret + 1:right_caret])
                
            elif 'cpu_usage_limit' in line:
                left_caret = line.index('>')
                right_caret = line.rindex('<')
                self.cpu_usage_limit = int(line[left_caret + 1:right_caret])

    def write_global_prefs(self):
        f = open(self._global_filename, 'w')
        f.write("""
<global_preferences>
    <max_ncpus>{}</max_ncpus>
    <cpu_usage_limit>{}</cpu_usage_limit>
</global_preferences>""".format(self.max_ncpus, self.cpu_usage_limit))

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