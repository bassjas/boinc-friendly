from boinc_server import Boinc_Server

def main():
    server = Boinc_Server(num_cpus=1, steal_bump_down=1, steal_emergency=10)
    server.boinc_loop()

if __name__ == "__main__":
    main()