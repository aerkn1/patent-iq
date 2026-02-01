class AppError(Exception):
    """Base application error"""


class ValidationError(AppError):
    pass


class NotFoundError(AppError):
    pass


class DataUnavailableError(AppError):
    pass

class InternalServerError(AppError):
    pass