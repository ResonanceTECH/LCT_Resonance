import enum

# Values mirror frontend/src/entities/types.ts and src/shared/lib/labels.ts.


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


class Readiness(str, enum.Enum):
    actively_looking = "actively_looking"
    open_to_offers = "open_to_offers"
    not_looking = "not_looking"


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
    active = "active"
    closed = "closed"
    archived = "archived"


class TestAttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    expired = "expired"


class FspSyncStatus(str, enum.Enum):
    none = "none"
    synced = "synced"
    no_history = "no_history"
    stale = "stale"
    error = "error"


class OfferStatus(str, enum.Enum):
    new = "new"
    viewed = "viewed"
    accepted = "accepted"
    declined = "declined"
    withdrawn = "withdrawn"  # P1, the frontend has no UI for it yet


class ConsentType(str, enum.Enum):
    personal_data = "personal_data"
    profile_publication = "profile_publication"
    fsp_sync = "fsp_sync"


class NotificationType(str, enum.Enum):
    offer_new = "offer_new"
    offer_accepted = "offer_accepted"
    offer_declined = "offer_declined"
    fsp_synced = "fsp_synced"
    application = "application"
    system = "system"
