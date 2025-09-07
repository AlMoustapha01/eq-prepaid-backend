"""Enums for the rules domain"""

from enum import Enum


class ProfileType(Enum):
    PREPAID = "PREPAID"
    HYBRID = "HYBRID"


class BalanceType(Enum):
    MAIN_BALANCE = "MAIN_BALANCE"
    CRED = "CRED"


class Status(Enum):
    DRAFT = "DRAFT"
    IN_PRODUCTION = "IN_PRODUCTION"
    TO_VALIDATE = "TO_VALIDATE"


class SectionStatus(Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
