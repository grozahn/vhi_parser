class StorageDbError(Exception):
    pass


class SavingError(IOError):
    pass


class ParsingError(Exception):
    pass


class NetworkError(Exception):
    pass


class PlottingError(Exception):
    pass
