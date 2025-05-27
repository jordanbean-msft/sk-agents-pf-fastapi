from semantic_kernel.kernel_pydantic import KernelBaseModel


class ChatCreateThreadOutput(KernelBaseModel):
    thread_id: str


__all__ = ["ChatCreateThreadOutput"]
