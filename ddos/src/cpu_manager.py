import platform
import os
from ..utils.ulog import log


class CPUManager:
    @staticmethod
    def randomize_cpu() -> None:
        current_pid = os.getpid()


        if platform.system().lower() == "linux":
            log.warning(f"cpu affinity setting on linux (currnt: {platform.system()})")
            return
        
        try:
            cpu_count = os.cpu_count()

            if not cpu_count:
                log.error("Unable to determine CPU count.")
                return
            
            cpu_ids = list(range(cpu_count))
            log.warning(f"Available CPUs: {cpu_ids}")

            os.sched_setaffinity(current_pid, cpu_ids)

            log.info(f"Set CPU affinity for PID {current_pid} to CPUs: {cpu_ids}")

        except (AttributeError, OSError) as e:
            log.error(f"Failed to set CPU affinity: {e}")


