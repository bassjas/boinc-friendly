from boinc_server import Boinc_Server
import signal

server = Boinc_Server(num_cpus=4, steal_bump_down=1, steal_emergency=10)

def signal_handler(sig, frame):
    if sig == signal.SIGUSR1:
        print(server.status())


def main():
    signal.signal(signal.SIGUSR1, signal_handler)
    server.boinc_loop()

if __name__ == "__main__":
    main()
