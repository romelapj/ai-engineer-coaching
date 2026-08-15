"""
Explicación 5 · Embeddings, similitud coseno, y por qué hay que medir

Del deck: cambiamos de tema, no de herramienta. Un embedding es un vector
(una lista de números, aquí 384) donde la DIRECCIÓN codifica el significado:
dos frases que quieren decir lo mismo apuntan hacia el mismo lado, aunque no
compartan ni una palabra.

Para medir "cuánto apuntan al mismo lado" se usa la similitud coseno: el
coseno del ángulo entre los dos vectores. 1 = misma dirección, 0 = sin
relación. En código son tres operaciones: producto punto dividido entre el
producto de las longitudes.

Esto es la base de RAG, de la búsqueda semántica y de la deduplicación.
Y lo vas a construir entero en la sesión 04.

Este archivo corre las MISMAS cuatro frases en inglés y en español, con un
modelo de embeddings local, y compara. El resultado es incómodo a propósito:
es la lección del día.

La API de Anthropic no expone embeddings. Usamos el modelo local que trae
Chroma (all-MiniLM-L6-v2): no necesita otra API key y corre en tu máquina.

Cómo correrlo:
    python 04_embeddings.py
"""

import math

from chromadb.utils import embedding_functions

# La primera vez descarga el modelo (~80 MB); después es instantáneo.
embed = embedding_functions.DefaultEmbeddingFunction()


def coseno(a, b):
    # Producto punto: suma de multiplicar los vectores elemento a elemento.
    # Es grande cuando los dos apuntan hacia el mismo lado.
    punto = sum(x * y for x, y in zip(a, b))
    # La "longitud" (norma) de cada vector: la raíz de la suma de cuadrados.
    norma_a = math.sqrt(sum(x * x for x in a))
    norma_b = math.sqrt(sum(y * y for y in b))
    # Dividir entre las longitudes deja solo el ÁNGULO: así una frase larga
    # y una corta se pueden comparar de igual a igual.
    return punto / (norma_a * norma_b)


# Las mismas cuatro ideas, en dos idiomas. La primera es la referencia; la
# segunda significa lo mismo sin compartir palabras; la tercera es del mismo
# mundo pero otra intención; la cuarta no tiene nada que ver.
FRASES = {
    "inglés": [
        "pay with a credit card",
        "checkout with visa",
        "charged twice for the same item",
        "recipe for cheese arepas",
    ],
    "español": [
        "pagar con tarjeta de crédito",
        "checkout con visa",
        "me cobraron dos veces",
        "receta de arepas de queso",
    ],
}


def comparar(idioma, frases):
    vectores = embed(frases)
    print(f"\n--- {idioma} ---")
    print(f'similitud contra "{frases[0]}":\n')
    for frase, vector in zip(frases, vectores):
        sim = coseno(vectores[0], vector)
        # Barra visual para ver la escala de un vistazo. Se recorta en 0
        # porque el coseno puede salir negativo (vectores en direcciones
        # opuestas) y una barra de largo negativo no existe.
        barra = "█" * max(0, int(sim * 30))
        print(f"  {sim:+.3f}  {barra:<30}  {frase}")
    return vectores


def main():
    vectores_en = comparar("inglés", FRASES["inglés"])
    # float() porque el modelo devuelve numpy.float32 y se imprime feo.
    print(f"\n(cada frase es un vector de {len(vectores_en[0])} números; "
          f"los 5 primeros: {[round(float(v), 3) for v in vectores_en[0][:5]]})")

    comparar("español", FRASES["español"])

    print(
        "\n=== la lección ===\n"
        "En inglés funciona: 'checkout with visa' queda por encima del resto\n"
        "sin compartir una sola palabra con la referencia, y las arepas caen\n"
        "casi a cero. Eso es lo que un buscador por palabras clave no puede\n"
        "hacer, y es el problema que resuelve RAG.\n"
        "\n"
        "En español SE ROMPE: las arepas puntúan MÁS ALTO que 'checkout con\n"
        "visa'. El orden queda al revés. Y no es un bug de tu código.\n"
        "\n"
        "all-MiniLM-L6-v2 está entrenado en inglés. Con español devuelve\n"
        "números perfectamente válidos y perfectamente inútiles: no falla,\n"
        "no avisa, simplemente miente en silencio. Si montaras un RAG en\n"
        "español sobre este modelo, recuperaría documentos al azar y te\n"
        "costaría días entender por qué.\n"
        "\n"
        "Dos cosas que llevarte:\n"
        "  1. El modelo de embeddings tiene que hablar TU idioma. Para\n"
        "     español: voyage-3.5, multilingual-e5 o bge-m3.\n"
        "  2. Esto no se descubre leyendo la documentación: se descubre\n"
        "     midiendo, con cuatro frases que tú ya sabes cómo deberían\n"
        "     ordenarse. Cinco minutos de esto ahorran una semana después."
    )


if __name__ == "__main__":
    main()
