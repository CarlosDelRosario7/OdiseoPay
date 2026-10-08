from .ia_routes import ia_blueprint
from .auth_routes import auth_blueprint
from .categoria_routes import categoria_blueprint
from .cliente_routes import cliente_blueprint
from .compra_routes import compra_blueprint
from .detalle_compra_routes import detalle_compra_blueprint
from .detalle_venta_routes import detalle_venta_blueprint
from .inventario_routes import inventario_blueprint
from .movimiento_inventario_routes import movimiento_blueprint
from .producto_routes import producto_blueprint
from .proveedor_routes import proveedor_blueprint
from .usuario_routes import usuario_blueprint
from .venta_routes import venta_blueprint


def register_routes(app):
    for blueprint in (
        auth_blueprint,
        categoria_blueprint,
        cliente_blueprint,
        compra_blueprint,
        detalle_compra_blueprint,
        detalle_venta_blueprint,
        ia_blueprint,
        inventario_blueprint,
        movimiento_blueprint,
        producto_blueprint,
        proveedor_blueprint,
        usuario_blueprint,
        venta_blueprint,
    ):
        app.register_blueprint(blueprint)