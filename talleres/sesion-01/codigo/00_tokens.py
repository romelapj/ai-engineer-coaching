"""
Explicación 1 · El modelo no ve letras: ve tokens

Del deck: antes de llegar al modelo, tu texto se parte en TOKENS con un
algoritmo llamado BPE (Byte Pair Encoding). El modelo nunca ve caracteres:
ve una lista de números. Eso explica cosas que parecen bugs (por ejemplo
que se equivoque contando cuántas erres tiene "strawberry") y explica tu
factura, porque los tokens son la unidad que se cobra.

No hay que adivinar cuántos tokens tiene un texto: la API tiene un endpoint
que los cuenta exacto, es GRATIS, y es específico de cada modelo.

Este archivo compara tres tipos de texto y mide cuántos caracteres cabe en
un token en cada uno. La diferencia sorprende.

Cómo correrlo:
    python 00_tokens.py
"""

import anthropic

client = anthropic.Anthropic()

MODELO = "claude-sonnet-4-6"

# Tres textos parecidos en longitud pero de naturaleza muy distinta.
TEXTOS = {
    "español": (
        "El cliente reporta que le cobraron dos veces el mismo producto "
        "y solicita la devolución del importe duplicado lo antes posible."
    ),
    "JSON": (
        '{"order_id": "ORD-8841", "status": "shipped", "amount": 45000, '
        '"currency": "COP", "items": [{"sku": "A-12", "qty": 2}]}'
    ),
    "código": (
        "def cobrar(order_id: str, monto: float) -> dict:\n"
        "    if order_id in procesados:\n"
        "        return {'status': 'duplicado'}\n"
        "    return {'status': 'ok', 'monto': monto}"
    ),
}


def contar(texto):
    # count_tokens NO genera respuesta ni consume tokens de salida: solo
    # cuenta. Es gratis y no tiene rate limit agresivo, así que puedes
    # llamarlo antes de cada petición para estimar costo.
    resp = client.messages.count_tokens(
        model=MODELO,  # El conteo depende del modelo: cada familia tokeniza distinto.
        messages=[{"role": "user", "content": texto}],
    )
    return resp.input_tokens


def main():
    print(f"Contando tokens con {MODELO}\n")
    print(f"{'tipo':10} {'caracteres':>11} {'tokens':>8} {'car/token':>10}")
    print("-" * 42)

    for nombre, texto in TEXTOS.items():
        tokens = contar(texto)
        caracteres = len(texto)
        # Cuántos caracteres "cabe" en un token. Cuanto más alto, más
        # eficiente es ese tipo de texto y más barato sale procesarlo.
        ratio = caracteres / tokens
        print(f"{nombre:10} {caracteres:>11} {tokens:>8} {ratio:>10.2f}")

    print(
        "\nEl español corriente es el más eficiente. El JSON y el código gastan\n"
        "más tokens por carácter: las llaves, comillas y sangrías son tokens\n"
        "que pagas igual que las palabras. Por eso pedirle JSON al modelo\n"
        "cuesta más de lo que parece, y por eso importa el formato que eliges."
    )

    # El caso famoso del deck: el modelo no ve las letras de una palabra.
    print("\n--- por qué se equivoca contando letras ---")
    palabra = "strawberry"
    print(f"'{palabra}' son {contar(palabra)} token(s) para el modelo,")
    print(f"pero {len(palabra)} caracteres para ti. Él no ve las 3 erres:")
    print("ve un puñado de números que representan pedazos de la palabra.")


if __name__ == "__main__":
    main()
