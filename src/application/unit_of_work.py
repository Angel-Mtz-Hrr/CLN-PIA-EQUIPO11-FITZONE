from sqlalchemy.orm import Session
from src.infrastructure.repositories import ClaseGrupalRepository, MembresiaRepository


class UnitOfWork:
    """
    Coordina el turno de trabajo. Garantiza que o se guarda todo (commit)
    o no se guarda nada (rollback) para evitar datos a medias.
    """

    def __init__(self, db_session: Session):
        self.db = db_session
        self.clases = ClaseGrupalRepository(db_session)
        self.membresias = MembresiaRepository(db_session)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type is not None:
            self.db.rollback()

    def confirmar(self, agregado=None):
        """Guarda los cambios y despacha eventos si todo salió bien."""
        self.db.commit()

        # Si el agregado (ej. ClaseGrupal) tiene eventos pendientes, los procesamos
        if agregado and hasattr(agregado, "eventos") and agregado.eventos:
            for evento in agregado.eventos:
                # Aquí en el futuro se conecta el envío de correos o actualización del historial
                print(f" [EVENTO DISPARADO] -> {evento.__class__.__name__}: {evento}")
            agregado.limpiar_eventos()
