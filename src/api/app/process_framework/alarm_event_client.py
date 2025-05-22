import logging
from opentelemetry import trace
from asyncio import Queue

from semantic_kernel.processes.kernel_process.kernel_process_message_channel import KernelProcessMessageChannel
from semantic_kernel.processes.kernel_process import KernelProcessEvent

logger = logging.getLogger("uvicorn.error")
tracer = trace.get_tracer(__name__)

class AlarmEventClient(KernelProcessMessageChannel):
    def __init__(self, queue: Queue):
        super().__init__()
        self.queue = queue

    @tracer.start_as_current_span("alarm_event_client")
    async def emit_event(self, process_event: KernelProcessEvent) -> None:
        logger.debug(f"Emitting event: {process_event}")
        await self.queue.put(process_event)
        pass

__all__ = [
    "AlarmEventClient",
]