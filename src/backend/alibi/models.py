from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from .parsers import zone


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class InvestigationCreate(StrictModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default='', max_length=4000)

    @field_validator('name')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Name cannot be blank')
        return value.strip()


class IntakeOptions(StrictModel):
    source: str = Field(min_length=1, max_length=160)
    log_format: Literal['auto', 'syslog', 'access'] = 'auto'
    timezone: str = 'UTC'
    year: int | None = Field(default=None, ge=1970, le=2100)
    offset_seconds: float = Field(default=0, ge=-604800, le=604800)
    uncertainty_seconds: float = Field(default=0, ge=0, le=86400)
    correction_reason: str = Field(default='No clock correction applied', min_length=1, max_length=2000)

    @field_validator('timezone')
    @classmethod
    def valid_zone(cls, value):
        zone(value)
        return value

    @field_validator('source', 'correction_reason')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Value cannot be blank')
        return value.strip()


class ClockCorrection(StrictModel):
    offset_seconds: float = Field(ge=-604800, le=604800)
    uncertainty_seconds: float = Field(default=0, ge=0, le=86400)
    reason: str = Field(min_length=3, max_length=2000)

    @field_validator('reason')
    @classmethod
    def meaningful(cls, value):
        if len(value.strip()) < 3:
            raise ValueError('Document the supporting evidence for this correction')
        return value.strip()


class EvidenceRecord(IntakeOptions):
    correction_reason: str
    id: str
    investigation_id: str
    filename: str
    sha256: str
    size: int
    imported_at: str
    total_records: int
    parsed_records: int
    gap_records: int


class EventRecord(StrictModel):
    id: str
    investigation_id: str
    evidence_id: str
    filename: str
    source: str
    line_number: int
    byte_start: int
    byte_end: int
    raw_line: str
    error: str | None
    original_timestamp: str | None = None
    utc_timestamp: str | None = None
    corrected_timestamp: str | None = None
    interval_start: str | None = None
    interval_end: str | None = None
    kind: str | None = None
    message: str | None = None
    host: str | None = None
    service: str | None = None
    ip: str | None = None
    status: str | None = None
    timezone_basis: str | None = None
    anchor_id: str | None = None
    parser_version: str | None = None
    offset_seconds: float
    uncertainty_seconds: float


class TimelinePage(StrictModel):
    items: list[EventRecord]
    total: int
    limit: int
    offset: int
