from flask import current_app
from google import genai


def analizar_inventario(productos):
    api_key = current_app.config["GEMINI_API_KEY"]
    model = current_app.config["GEMINI_MODEL"]

    if not api_key:
        raise RuntimeError("Gemini no está configurado correctamente.")

    client = genai.Client(api_key=api_key)

    lineas = []

    for producto in productos:
        inventario = producto.inventario

        if inventario is None:
            continue

        lineas.append(
            f"- Producto: {producto.nombre}; "
            f"cantidad: {inventario.cantidad}; "
            f"stock mínimo: {inventario.stock_minimo}; "
            f"precio compra: {producto.precio_compra}; "
            f"precio venta: {producto.precio_venta}; "
            f"ubicación: {inventario.ubicacion or 'No especificada'}"
        )

    if not lineas:
        return "No hay información de inventario disponible para analizar."

    datos = "\n".join(lineas)

    prompt = f"""
Eres un asistente de análisis de inventario para OdiseoPay.

Analiza exclusivamente los datos proporcionados.
No inventes productos, cantidades, precios ni ubicaciones.
No puedes modificar el inventario ni realizar operaciones.

Identifica:
1. Productos con cantidad igual o menor al stock mínimo.
2. Productos que deberían priorizarse para reposición.
3. Observaciones relevantes sobre el inventario.
4. Recomendaciones breves y claras para el administrador.

DATOS DEL INVENTARIO:
{datos}
"""

    response = client.interactions.create(
        model=model,
        input=prompt,
    )

    return response.output_text