"""Context management for candidate information."""

from proximus.context.calls import CallManager, CallRecord, CallTranscriptEntry
from proximus.context.resume import Resume, ResumeManager

__all__ = ["CallManager", "CallRecord", "CallTranscriptEntry", "Resume", "ResumeManager"]
