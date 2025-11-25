"""
Application constants and enums
Centralized location for all hardcoded values
"""
from enum import Enum


# ============================================================================
# ERROR MESSAGES
# ============================================================================

class ErrorMessages:
    """Centralized error messages for consistent API responses"""
    
    # Authentication errors
    EMAIL_ALREADY_EXISTS = "Email already registered"
    INVALID_CREDENTIALS = "Incorrect email or password"
    INACTIVE_USER = "Inactive user"
    NO_PASSWORD_SET = "User has no password set. Please contact administrator."
    INCORRECT_CURRENT_PASSWORD = "Incorrect current password"
    INSUFFICIENT_PERMISSIONS = "Insufficient permissions"
    USER_NOT_FOUND = "User not found"
    
    # Vendor errors
    VENDOR_NOT_FOUND = "Vendor not found"
    VENDOR_ALREADY_EXISTS = "Vendor with this ID already exists"
    INVALID_VENDOR_COUNTRY = "Invalid vendor country"
    INVALID_CIF_FORMAT = "CIF must be exactly 6 numeric digits"
    
    # Contract errors
    CONTRACT_NOT_FOUND = "Contract not found"
    CONTRACT_ALREADY_EXISTS = "Contract with this ID already exists"
    INVALID_CONTRACT_DATES = "End date must be after start date"
    INVALID_EXTENSION_DATE = "Extension date must be after current end date"
    CONTRACT_ALREADY_TERMINATED = "Contract is already terminated"
    VENDOR_REQUIRED = "Vendor is required for contract creation"
    
    # Document errors
    INVALID_FILE_TYPE = "Only PDF files are allowed"
    FILE_TOO_LARGE = "File size exceeds maximum allowed size"
    DOCUMENT_REQUIRED = "This document is required"
    
    # Validation errors
    INVALID_EMAIL_FORMAT = "Invalid email format"
    INVALID_PHONE_FORMAT = "Invalid phone number format"
    INVALID_DATE_FORMAT = "Invalid date format"
    INVALID_DEPARTMENT = "Invalid department"
    INVALID_ROLE = "Invalid role"
    
    # General errors
    INTERNAL_SERVER_ERROR = "Internal server error"
    INVALID_REQUEST = "Invalid request"
    RESOURCE_NOT_FOUND = "Resource not found"


# ============================================================================
# SUCCESS MESSAGES
# ============================================================================

class SuccessMessages:
    """Success messages for API responses"""
    
    PASSWORD_CHANGED = "Password changed successfully"
    PASSWORD_SET = "Password set successfully for user {email}"
    VENDOR_CREATED = "Vendor created successfully"
    VENDOR_UPDATED = "Vendor updated successfully"
    VENDOR_DELETED = "Vendor deleted successfully"
    CONTRACT_CREATED = "Contract created successfully"
    CONTRACT_UPDATED = "Contract updated successfully"
    CONTRACT_DELETED = "Contract deleted successfully"
    CONTRACT_EXTENDED = "Contract extended successfully"
    CONTRACT_TERMINATED = "Contract terminated successfully"


# ============================================================================
# DATE INTERVALS
# ============================================================================

class DateInterval(int, Enum):
    """Date intervals in days for various operations"""
    
    FIFTEEN_DAYS = 15
    THIRTY_DAYS = 30
    SIXTY_DAYS = 60
    NINETY_DAYS = 90
    ONE_TWENTY_DAYS = 120
    
    ONE_YEAR_DAYS = 365
    TWO_YEARS_DAYS = 730
    THREE_YEARS_DAYS = 1095
    FIVE_YEARS_DAYS = 1825


# ============================================================================
# VENDOR CONSTANTS
# ============================================================================

class VendorPrefix(str, Enum):
    """Vendor ID prefixes based on bank"""
    
    ARUBA_BANK = "AB"
    ORCO_BANK = "OB"


class VendorCountry:
    """Special vendor countries with specific logic"""
    
    ARUBA = "Aruba"
    CURACAO = "Curacao"
    BONAIRE = "Bonaire"
    SAINT_MARTIN_DUTCH = "Saint Martin (Dutch)"
    SAINT_MARTIN_FRENCH = "Saint Martin (French)"
    UNITED_STATES = "United States"
    
    # Countries that don't require city, state, zip
    NO_EXTRA_ADDRESS_FIELDS = [
        ARUBA,
        CURACAO,
        BONAIRE,
        SAINT_MARTIN_DUTCH,
        SAINT_MARTIN_FRENCH
    ]


# ============================================================================
# FILE CONSTANTS
# ============================================================================

class FileConstants:
    """File upload constants"""
    
    # File size limits (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Allowed file types
    ALLOWED_FILE_TYPES = ["application/pdf"]
    ALLOWED_EXTENSIONS = [".pdf"]
    
    # Upload directory
    UPLOAD_DIR = "uploads"
    VENDOR_DOCS_DIR = "uploads/vendors"
    CONTRACT_DOCS_DIR = "uploads/contracts"


# ============================================================================
# PAGINATION CONSTANTS
# ============================================================================

class PaginationConstants:
    """Pagination defaults and limits"""
    
    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100
    MIN_PAGE_SIZE = 1


# ============================================================================
# VALIDATION PATTERNS
# ============================================================================

class ValidationPatterns:
    """Regex patterns for validation"""
    
    # Phone number: allows digits, spaces, hyphens, plus, parentheses
    PHONE_NUMBER = r'^[\d\s\-\+\(\)]+$'
    
    # CIF: exactly 6 digits
    CIF = r'^\d{6}$'
    
    # Vendor ID: AB or OB followed by digits
    VENDOR_ID = r'^(AB|OB)\d+$'
    
    # Contract ID: C followed by digits
    CONTRACT_ID = r'^C\d+$'
    
    # User ID: U followed by digits
    USER_ID = r'^U\d+$'


# ============================================================================
# DUE DILIGENCE CONSTANTS
# ============================================================================

class DueDiligenceConstants:
    """Due diligence related constants"""
    
    # Years to add based on material outsourcing
    MATERIAL_OUTSOURCING_YEARS = 3
    NON_MATERIAL_OUTSOURCING_YEARS = 5
    
    # Alert frequencies (in days)
    ALERT_FREQUENCIES = [15, 30, 60, 90, 120]


# ============================================================================
# CONTRACT CONSTANTS
# ============================================================================

class ContractConstants:
    """Contract related constants"""
    
    # Renewal periods (in years)
    RENEWAL_PERIODS = [1, 2, 3]
    
    # Notice periods (in days)
    NOTICE_PERIODS = [15, 30, 60, 90, 120]
    
    # Expiration notice frequencies (in days)
    EXPIRATION_NOTICE_FREQUENCIES = [15, 30, 60, 90, 120]


# ============================================================================
# LIMITS
# ============================================================================

class Limits:
    """Various limits for the application"""
    
    # Vendor limits
    MAX_VENDOR_ADDRESSES = 2
    MAX_VENDOR_EMAILS = 2
    MAX_VENDOR_PHONES = 2
    
    # String length limits
    MAX_VENDOR_NAME_LENGTH = 255
    MAX_CONTRACT_DESCRIPTION_LENGTH = 100
    MAX_EMAIL_LENGTH = 255
    MAX_PHONE_LENGTH = 20
    MAX_ADDRESS_LENGTH = 500
    
    # Numeric limits
    MAX_CONTRACT_AMOUNT = 999999999999.99  # 15 digits, 2 decimals
    MIN_CONTRACT_AMOUNT = 0.01


# ============================================================================
# HTTP STATUS CODES (for reference)
# ============================================================================

class HTTPStatus:
    """HTTP status codes used in the application"""
    
    # Success
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    
    # Client errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    
    # Server errors
    INTERNAL_SERVER_ERROR = 500


# ============================================================================
# AUTHENTICATION CONSTANTS
# ============================================================================

class AuthConstants:
    """Authentication related constants"""
    
    # Token settings (should be overridden by environment variables)
    DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    DEFAULT_ALGORITHM = "HS256"
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 100
    
    # Role mappings
    ROLE_NAME_TO_VALUE = {
        "CONTRACT_ADMIN": "Contract Admin",
        "CONTRACT_MANAGER": "Contract Manager",
        "CONTRACT_MANAGER_BACKUP": "Contract Manager Backup"
    }
    
    VALID_ROLES = [
        "Contract Admin",
        "Contract Manager",
        "Contract Manager Backup"
    ]
    
    DEFAULT_ROLE = "Contract Manager"