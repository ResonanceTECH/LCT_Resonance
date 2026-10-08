import enum


class UserRole(str, enum.Enum):
    candidate = "candidate"
    employer = "employer"
    admin = "admin"


class UserStatus(str, enum.Enum):
    active = "active"
    blocked = "blocked"
    deleted = "deleted"


class WorkFormat(str, enum.Enum):
    remote = "remote"
    hybrid = "hybrid"
    office = "office"


class GradeVerificationStatus(str, enum.Enum):
    not_tested = "not_tested"
    failed = "failed"
    verified = "verified"


class ProfileVisibility(str, enum.Enum):
    private = "private"
    employers = "employers"
    public = "public"


class ContactsVisibility(str, enum.Enum):
    locked = "locked"
    after_accept = "after_accept"


class VacancyStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class VacancyVisibility(str, enum.Enum):
    private = "private"
    public = "public"


class TestAttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    expired = "expired"


class FspSyncStatus(str, enum.Enum):
    none = "none"
    synced = "synced"
    no_history = "no_history"
    stale = "stale"
    error = "error"


class OfferStatus(str, enum.Enum):
    sent = "sent"
    viewed = "viewed"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class ConsentType(str, enum.Enum):
    personal_data = "personal_data"
    profile_publication = "profile_publication"
    fsp_sync = "fsp_sync"
