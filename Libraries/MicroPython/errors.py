# wheellog_euc_micropython/errors.py

class EUC_Error(Exception):
    """Eccezione base per errori della libreria."""
    pass

class BLEScanError(EUC_Error):
    """Errore durante la scansione BLE."""
    pass

class BLEConnectionError(EUC_Error):
    """Errore durante la connessione BLE."""
    pass

class BLECommunicationError(EUC_Error):
    """Errore durante la lettura/scrittura BLE."""
    pass

class EUCParseError(EUC_Error):
    """Errore durante il parsing dei dati EUC."""
    pass

class EUCCommandError(EUC_Error):
    """Errore durante l'invio di un comando EUC."""
    pass
