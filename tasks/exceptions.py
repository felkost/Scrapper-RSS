"""Custom exceptions for the RSS reader."""


class UnhandledException(Exception):
    pass


class InvalidXMLError(UnhandledException):
    pass


class InvalidRSSError(UnhandledException):
    pass
