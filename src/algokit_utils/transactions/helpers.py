import algokit_algosdk as algosdk

__all__ = ["calculate_extra_program_pages"]


def calculate_extra_program_pages(approval: bytes | None, clear: bytes | None) -> int:
    """Calculate minimum number of extra_pages required for provided approval and clear programs."""
    total = len(approval or b"") + len(clear or b"")
    return max(0, (total - 1) // algosdk.constants.APP_PAGE_MAX_SIZE)
