import m5
import json
import dataclasses

from gem5.isas import ISA
from m5.objects import (
    ArmDefaultRelease,
    AddrRange,
)
from gem5.utils.requires import requires
from gem5.resources.workload import CustomWorkload
from gem5.resources.resource import BinaryResource
from gem5.simulate.simulator import Simulator
from m5.objects import VExpress_GEM5_Foundation
from gem5.components.boards.arm_baremetal_board import ArmBareMetalBoard
from gem5.components.memory import DRAMSysMem
from gem5.components.processors.cpu_types import CPUTypes
from gem5.components.processors.simple_processor import SimpleProcessor
from gem5.simulate.exit_event import ExitEvent
from dataclasses import dataclass

from pim_config import Statistics

requires(isa_required=ISA.ARM)

from gem5.components.cachehierarchies.classic.private_l1_private_l2_cache_hierarchy import (
    PrivateL1PrivateL2CacheHierarchy,
)
from gem5.components.cachehierarchies.classic.no_cache import NoCache

cache_hierarchy = PrivateL1PrivateL2CacheHierarchy(
    l1d_size="16kB", l1i_size="16kB", l2_size="256kB"
)

memory = DRAMSysMem(
    configuration="ext/dramsys/DRAMSys/configs/hbm2-example.json",
    size="4GiB",
)
processor = SimpleProcessor(cpu_type=CPUTypes.TIMING, num_cores=1, isa=ISA.ARM)
release = ArmDefaultRelease()
platform = VExpress_GEM5_Foundation()

board = ArmBareMetalBoard(
    clk_freq="3GHz",
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
    release=release,
    platform=platform,
)

# HBM2 requires line size of 32 Bytes
board.cache_line_size = 32

#for core in processor.get_cores():
#    core.core.fetchBufferSize = 32

workload = CustomWorkload(
    "set_baremetal_workload",
    {
        "kernel": BinaryResource("vadd"),
    },
)
board.set_workload(workload)


@dataclass
class WorkloadTime:
    start: int
    end: int


workload_time = WorkloadTime(0, 0)


def exit_event():
    print(f"Workload begin @{m5.curTick()}")
    workload_time.start = m5.curTick()
    m5.stats.reset()
    yield False

    print(f"Workload end @{m5.curTick()}")
    workload_time.end = m5.curTick()
    m5.stats.dump()
    yield False

    print(f"Exit simulation @{m5.curTick()}...")
    yield True


simulator = Simulator(
    board=board, on_exit_event={ExitEvent.EXIT: exit_event()}
)

simulator.run()

print(f"Workload took {workload_time.end - workload_time.start}")

statistics = Statistics(workload_time.end - workload_time.start)
print(json.dumps(dataclasses.asdict(statistics)))
