# from functools import lru_cache
# from typing import Annotated

# from fastapi import Depends
# from semantic_kernel.processes.kernel_process import KernelProcess
# from app.process_framework.processes.process_alarm import build_process_alarm_process

# def create_process_alarm_process() -> KernelProcess:
#     kernel_process = build_process_alarm_process()
#     return kernel_process


# @lru_cache
# def get_create_process_alarm_process() -> KernelProcess:
#     return create_process_alarm_process()

# KernelProcessDependency = Annotated[KernelProcess, Depends(get_create_process_alarm_process)]

# __all__ = [
#     'get_create_process_alarm_process',
#     'KernelProcessDependency'
# ]