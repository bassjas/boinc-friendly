import re
import subprocess

class Top:
    """Encapsulate the 'top' command to get the current CPU steal time"""

    _fake_top_str = """top - 16:19:30 up 31 days, 19:41,  4 users,  load average: 24.85, 24.96, 24.98
    Tasks: 333 total,  26 running, 307 sleeping,   0 stopped,   0 zombie
    %Cpu(s):  0.5 us, 33.7 sy, 65.9 ni,  0.0 id,  0.0 wa,  0.0 hi,  0.0 si,  17.7 st
    MiB Mem :  24032.6 total,  18849.6 free,   2206.1 used,   2976.9 buff/cache
    MiB Swap:   3860.0 total,   3860.0 free,      0.0 used.  21416.8 avail Mem

        PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
    3283219 boinc     39  19   91584  90736   2392 R 106.2   0.4 314:05.08 wcgrid_+
    3291945 boinc     39  19   82420  81588   2392 R 106.2   0.3 196:23.48 wcgrid_+
    3294172 boinc     39  19   80304  79520   2392 R 106.2   0.3 168:13.83 wcgrid_+
    3295643 boinc     39  19   78352  77660   2392 R 106.2   0.3 145:03.25 wcgrid_+
    3305780 boinc     39  19   68196  67524   2392 R 106.2   0.3  13:15.88 wcgrid_+
    3283248 boinc     39  19   91288  90536   2392 R 100.0   0.4 312:10.96 wcgrid_+
    """

    _pattern = None

    def __init__(self, fake_it=False):
        """Run the 'top' command in a subprocess and get its stealtime information.
        
        fake_it -- If True, use _fake_top_str as the output from 'top'.  This allows 
                development on a server without 'top' installed
        """

        if self._pattern == None:
            # This pattern looks for '0.0 st' or '00.0 st' followed by a word boundary.
            self._pattern = re.compile(r'\d?\d\.\d st\b')
        
        if fake_it:
            result = self._fake_top_str
        else:
            process = subprocess.run(['top', '-bn1'], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                universal_newlines=True)
            result = process.stdout
        
        m = self._pattern.search(result)
        self.steal_time = m.group()

    def get_stealtime(self):
        return self.steal_time

top = Top(fake_it=True)
print(top.get_stealtime())