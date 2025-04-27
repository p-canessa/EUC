# wheellog_euc_micropython/errors.py

class WheelLogError(Exception):
    """Eccezione base per errori della libreria WheelLog."""
    pass

class BLEScanError(WheelLogError):
    """Errore durante la scansione BLE."""
    pass

class BLEConnectionError(WheelLogError):
    """Errore durante la connessione BLE."""
    pass

class BLECommunicationError(WheelLogError):
    """Errore durante la lettura/scrittura BLE."""
    pass

class EUCParseError(WheelLogError):
    """Errore durante il parsing dei dati EUC."""
    pass

class EUCCommandError(WheelLogError):
    """Errore durante l'invio di un comando EUC."""
    pass
