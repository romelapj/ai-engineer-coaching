"""
Explicación 4 · El estimado contra la factura

Del deck, paso 4 del Token-ó-metro: haz una llamada real y compara tu
estimación con lo que de verdad reporta la API. ¿Qué tan cerca quedaste?

Esto cierra el ciclo del día: contar (gratis) → estimar el costo → llamar →
comparar. Es el mismo ciclo que vas a montar en producción, solo que allí
el "comparar" vive en un dashboard.

Aviso importante que se ve aquí: los tokens de ENTRADA son predecibles
(count_tokens acierta casi exacto). Los de SALIDA no: no sabes cuánto va a
escribir el modelo hasta que escribe. Por eso la salida es la parte
peligrosa de un presupuesto.

Cómo correrlo:
    python 03_estimado_vs_real.py
"""

import anthropic

client = anthropic.Anthropic()

MODELO = "claude-sonnet-4-6"
PRECIO_ENTRADA = 3.00  # USD por millón de tokens (sonnet-4-6, agosto 2026)
PRECIO_SALIDA = 15.00  # USD por millón. Nota que la salida cuesta 5 veces más.

PROMPT = (
    "Explica en un párrafo corto qué es un token en un modelo de lenguaje, "
    "para alguien que nunca ha programado."
)


def main():
    # --- 1. Estimación previa (gratis) ------------------------------------
    conteo = client.messages.count_tokens(
        model=MODELO,
        messages=[{"role": "user", "content": PROMPT}],
    )
    estimado_entrada = conteo.input_tokens
    print(f"Estimación previa (count_tokens): {estimado_entrada} tokens de entrada")
    print(f"Costo de entrada estimado: ${estimado_entrada * PRECIO_ENTRADA / 1_000_000:.6f}")

    # --- 2. La llamada real -----------------------------------------------
    resp = client.messages.create(
        model=MODELO,
        max_tokens=1024,
        messages=[{"role": "user", "content": PROMPT}],
    )
    real_entrada = resp.usage.input_tokens
    real_salida = resp.usage.output_tokens

    print(f"\nReal (resp.usage): {real_entrada} entrada / {real_salida} salida")
    print(f"stop_reason: {resp.stop_reason}")

    # --- 3. La comparación -------------------------------------------------
    diferencia = real_entrada - estimado_entrada
    print(f"\nDiferencia en la entrada: {diferencia:+d} tokens")
    print(
        "  (una diferencia pequeña es normal: la API agrega unos pocos tokens\n"
        "   de estructura al armar el mensaje)"
    )

    costo_real = (
        real_entrada * PRECIO_ENTRADA / 1_000_000
        + real_salida * PRECIO_SALIDA / 1_000_000
    )
    print(f"\nCosto real de esta llamada: ${costo_real:.6f}")
    porcentaje_salida = real_salida * PRECIO_SALIDA / (
        real_entrada * PRECIO_ENTRADA + real_salida * PRECIO_SALIDA
    )
    print(f"De ese costo, la SALIDA fue el {porcentaje_salida:.0%}")

    print(
        "\nEsa es la lección del día: puedes estimar la entrada con precisión\n"
        "antes de gastar un centavo, pero la salida no la sabes hasta que\n"
        "ocurre, y suele ser la mayor parte de la factura. Controlarla es\n"
        "prompt (pedir respuestas cortas) y max_tokens, no suerte."
    )


if __name__ == "__main__":
    main()
