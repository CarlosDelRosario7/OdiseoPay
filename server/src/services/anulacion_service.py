"""Anulación transaccional de operaciones comerciales."""

from collections import Counter
from datetime import datetime, timezone

from ..extensions import db
from ..models import Anulacion, Compra, Inventario, MovimientoInventario, Usuario, Venta


class ConflictoAnulacion(ValueError):
    """La operación no se puede anular en su estado actual."""


def anular(tipo, identificador, usuario_id, motivo):
    if not isinstance(motivo, str) or not motivo.strip() or len(motivo.strip()) > 255:
        raise ValueError("El motivo es obligatorio y no puede exceder 255 caracteres")
    if tipo not in {"VENTA", "COMPRA"}:
        raise ValueError("Tipo de operación inválido")
    if db.session.get(Usuario, usuario_id) is None:
        raise ValueError("Usuario no encontrado")

    modelo = Venta if tipo == "VENTA" else Compra
    operacion = db.session.get(modelo, identificador, with_for_update=True)
    if operacion is None:
        raise LookupError("Operación no encontrada")
    existente = db.session.scalar(
        db.select(Anulacion).where(
            Anulacion.tipo_operacion == tipo, Anulacion.id_operacion == identificador
        )
    )
    if existente:
        raise ConflictoAnulacion("La operación ya fue anulada")

    cantidades = Counter()
    for detalle in operacion.detalles:
        cantidades[detalle.id_producto] += detalle.cantidad
    if not cantidades:
        raise ConflictoAnulacion("La operación no tiene detalles que revertir")

    inventarios = {}
    for producto_id in sorted(cantidades):
        inventario = db.session.scalar(
            db.select(Inventario).where(Inventario.id_producto == producto_id).with_for_update()
        )
        if inventario is None:
            raise ConflictoAnulacion("Falta inventario para revertir la operación")
        if tipo == "COMPRA" and inventario.cantidad < cantidades[producto_id]:
            raise ConflictoAnulacion("No hay stock suficiente para anular la compra")
        inventarios[producto_id] = inventario

    registro = Anulacion(
        tipo_operacion=tipo,
        id_operacion=identificador,
        id_usuario=usuario_id,
        fecha_utc=datetime.now(timezone.utc).replace(tzinfo=None),
        motivo=motivo.strip(),
    )
    db.session.add(registro)
    for producto_id, cantidad in cantidades.items():
        inventario = inventarios[producto_id]
        inventario.cantidad += cantidad if tipo == "VENTA" else -cantidad
        db.session.add(MovimientoInventario(
            id_producto=producto_id,
            tipo="ENTRADA" if tipo == "VENTA" else "SALIDA",
            cantidad=cantidad,
            motivo=f"Anulación de {tipo.lower()} #{identificador}",
            id_usuario=usuario_id,
        ))
    db.session.commit()
    return registro


def serializar(registro):
    return {
        "id_anulacion": registro.id_anulacion,
        "tipo_operacion": registro.tipo_operacion,
        "id_operacion": registro.id_operacion,
        "id_usuario": registro.id_usuario,
        "usuario": registro.usuario.usuario,
        "fecha_utc": registro.fecha_utc.isoformat() + "Z",
        "motivo": registro.motivo,
    }
