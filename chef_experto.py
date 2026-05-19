import collections
if not hasattr(collections, 'Mapping'):
    import collections.abc
    collections.Mapping = collections.abc.Mapping
    collections.MutableMapping = collections.abc.MutableMapping

from experta import Fact, KnowledgeEngine, Rule, TEST, MATCH
import json
import os
import ollama

# Importar librerias para el pdf
try:
    from pdf import FPDF # type: ignore
except ImportError:
    FPDF = None  # No se puede generar el pdf

# 1. DEFINICION DE HECHOS
class Plato(Fact):
    """Nombre del plato y sus instrucciones de preparacion."""
    nombre: str
    instrucciones: str
    macros: dict # {'calorias': int, 'proteinas': int, 'carbohidratos': int, 'grasas': int}
    pass

class Ingrediente(Fact):
    """Relacion plato -> ingrediente necesario."""
    plato: str
    ingrediente: str
    pass

class Deseo(Fact):
    """Lo que el usuario expresa que quiere comer (termino de busqueda)."""
    termino: str
    contexto: list  #Etiquetas asociadas al deseo [ligero, rapido, vegetariano, etc.]
    pass

class RecetaSugerida(Fact):
    """Resultado de la inferencia: plato que satisface el deseo."""
    plato: str
    instrucciones: str
    macros: dict # {'calorias': int, 'proteinas': int, 'carbohidratos': int, 'grasas': int}
    pass


# LLM | Inteligencia Artificial con OLLAMA
def llm_interpretar_deseo(texto_usuario):
    """
    Llama a Ollama local para convertir lenguaje natural en JSON estructurado que contenga el deseo y su contexto.
    """
    if not ollama:
        print("Ollama no esta disponible. No se puede interpretar deseos complejos.")
        return {"termino": texto_usuario, "contexto": []}
    
    model_name = "llama3"

    prompt = f"""
    Eres un asistente de cocina experto. El usuario dice: "{texto_usuario}". 
    Debes de analizar su deseo y devolver Solo un objeto JSON valido con esta estructura exacta:
{{
    "termino": "palabra clave principal para buscar (ej: 'pollo', 'sopa', 'postre', 'ensalada')",
    "contexto": ["lista", "de", "etiquetas", "si", "aplica"]
}}
    Reglas para el JSON:
    1. Si el usuario pide algo 'ligero' o 'fresco', el termino debe ser 'ensalada y contexto ['ligero'].
    2. Si pide 'caliente' o 'caldo', termino debe de ser 'sopa' y contexto ['caliente'].
    3. Si pide 'dulce' o 'postre', termino debe ser 'postre' y contexto ['dulce'].
    4. SI menciona un ingrediente directo (ej: 'quiero huevo'), el termino es 'huevo'
    5. No devuelva texto explicativo, solo el JSON.

    """

# el try es para evitar que si falla la llamada a ollama, el sistema siga funcionando con una interpretacion basica del deseo.

python
# filepath: c:\Users\Usuario\Documents\IA_BigDATA\MIA\TrabajoFinal_SistemasExpertos\chef_experto.py
def obtener_macros_ollama(nombre_plato):
    """
    Llama a Ollama para obtener macros reales si no están en la base de conocimiento.
    """
    base_datos = {
        "Pollo al horno con especias": {"calorias": 450, "proteinas": 35, "carbos": 15, "grasas": 20},
        "Ensalada Cesar": {"calorias": 320, "proteinas": 18, "carbos": 10, "grasas": 22},
        "Sopa de tomate": {"calorias": 150, "proteinas": 5, "carbos": 25, "grasas": 4},
        "Tacos de carnitas": {"calorias": 600, "proteinas": 30, "carbos": 45, "grasas": 30},
        "Pastel de chocolate": {"calorias": 400, "proteinas": 6, "carbos": 60, "grasas": 12},
        "Revuelto de champinones": {"calorias": 220, "proteinas": 14, "carbos": 4, "grasas": 16},
        "Ceviche de pescado": {"calorias": 280, "proteinas": 28, "carbos": 10, "grasas": 8},
        "Ensalada de frutas": {"calorias": 100, "proteinas": 2, "carbos": 15, "grasas": 0},
        "Ensalada de coliflor": {"calorias": 80, "proteinas": 2, "carbos": 10, "grasas": 0},
        "Ensalada de lechuga": {"calorias": 50, "proteinas": 1, "carbos": 5, "grasas": 0},
        "Pastel de manzana": {"calorias": 350, "proteinas": 4, "carbos": 50, "grasas": 10},
        "Ensalada de tomate": {"calorias": 100, "proteinas": 2, "carbos": 15, "grasas": 0},
        "Ensalada de aguacate": {"calorias": 80, "proteinas": 2, "carbos": 10, "grasas": 0},
        "Ensalada de lechuga y tomate": {"calorias": 50, "proteinas": 1, "carbos": 5, "grasas": 0},
        "Brownie de chocolate": {"calorias": 450, "proteinas": 5, "carbos": 60, "grasas": 20},
        "Patata asada con romero": {"calorias": 200, "proteinas": 3, "carbos": 30, "grasas": 5},
        "Sopa de verduras": {"calorias": 120, "proteinas": 4, "carbos": 20, "grasas": 3},
        "Macarrones con queso": {"calorias": 500, "proteinas": 15, "carbos": 70, "grasas": 20},
        "Pollo al ajillo": {"calorias": 400, "proteinas": 30, "carbos": 10, "grasas": 15},
        "Natillas caseras": {"calorias": 250, "proteinas": 6, "carbos": 30, "grasas": 8},
    }

    return base_datos.get(nombre_plato, {"calorias": 0, "proteinas": 0, "carbos": 0, "grasas": 0})



# 2. MOTOR DE INFERENCIA
class ChefExperto(KnowledgeEngine):
    @Rule(
        Deseo(termino=MATCH.t),
        Plato(nombre=MATCH.n, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda t, n: t.lower() in n.lower()),
        salience=10
    )
    def coincidir_nombre(self, t, n, i, m):
        self.declare(RecetaSugerida(plato=n, instrucciones=i, macros=m))

    @Rule(
        Deseo(termino=MATCH.t),
        Ingrediente(plato=MATCH.p, ingrediente=MATCH.ing),
        Plato(nombre=MATCH.p, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda t, ing: t.lower() == ing.lower()),
        salience=5
    )
    def coincidir_ingrediente(self, t, p, i, m):
        self.declare(RecetaSugerida(plato=p, instrucciones=i, macros=m))

    @Rule(
        Deseo(contexto=MATCH.ctx),
        Plato(nombre=MATCH.n, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda ctx, n: ("ligero" in ctx and "ensalada" in n.lower()) or
                            ("caliente" in ctx and "sopa" in n.lower()) or
                            ("dulce" in ctx and "chocolate" in n.lower())),
        salience=8
    )
    def coincidencia_semantica(self, ctx, n, i, m):
        self.declare(RecetaSugerida(plato=n, instrucciones=i, macros=m))

# 3. BASE DE CONOCIMIENTO (RECETAS)
def cargar_conocimiento(engine):
    """Declara todos los hechos estaticos: platos e ingredientes."""
    engine.declare(
        Plato(nombre="Pollo al horno con especias",
              instrucciones="1. Adobar el pollo con sal, pimienta, romero y ajo. 2. Hornear a 180°C por 45 min. 3. Servir con papas."),
        Plato(nombre="Ensalada Cesar",
              instrucciones="1. Lavar la lechuga. 2. Agregar pollo desmenuzado. 3. Anadir aderezo Cesar y crutones."),
        Plato(nombre="Sopa de tomate",
              instrucciones="1. Sofreir cebolla y ajo. 2. Agregar tomates pelados y caldo. 3. Cocinar 20 min y licuar."),
        Plato(nombre="Tacos de carnitas",
              instrucciones="1. Dorar la carne de cerdo en su grasa. 2. Calentar tortillas. 3. Servir con cebolla, cilantro y salsa."),
        Plato(nombre="Pastel de chocolate",
              instrucciones="1. Batir huevos con azucar. 2. Agregar harina, cacao y levadura. 3. Hornear 30 min a 180°C."),
        Plato(nombre="Revuelto de champinones",
              instrucciones="1. Saltear champinones laminados con ajo. 2. Incorporar huevo batido. 3. Cocinar hasta cuajar."),
        Plato(nombre="Ceviche de pescado",
              instrucciones="1. Cortar pescado en cubos. 2. Marinar con jugo de limon, cebolla morada, cilantro y aji. 3. Reposar 20 min."),

        Ingrediente(plato="Pollo al horno con especias", ingrediente="pollo"),
        Ingrediente(plato="Pollo al horno con especias", ingrediente="romero"),
        Ingrediente(plato="Ensalada Cesar", ingrediente="lechuga"),
        Ingrediente(plato="Ensalada Cesar", ingrediente="pollo"),
        Ingrediente(plato="Ensalada Cesar", ingrediente="aderezo cesar"),
        Ingrediente(plato="Sopa de tomate", ingrediente="tomate"),
        Ingrediente(plato="Sopa de tomate", ingrediente="cebolla"),
        Ingrediente(plato="Tacos de carnitas", ingrediente="cerdo"),
        Ingrediente(plato="Tacos de carnitas", ingrediente="tortilla"),
        Ingrediente(plato="Tacos de carnitas", ingrediente="cilantro"),
        Ingrediente(plato="Pastel de chocolate", ingrediente="chocolate"),
        Ingrediente(plato="Pastel de chocolate", ingrediente="harina"),
        Ingrediente(plato="Revuelto de champinones", ingrediente="champinones"),
        Ingrediente(plato="Revuelto de champinones", ingrediente="huevo"),
        Ingrediente(plato="Ceviche de pescado", ingrediente="pescado"),
        Ingrediente(plato="Ceviche de pescado", ingrediente="limon"),
    )


# 4. FUNCIONES DE BUSQUEDA E INTERFAZ
def buscar_recetas_por_deseo(termino):
    engine = ChefExperto()
    engine.reset()
    cargar_conocimiento(engine)
    engine.declare(Deseo(termino=termino))
    engine.run()
    sugerencias = [(f['plato'], f['instrucciones']) 
                   for f in engine.facts.values() 
                   if isinstance(f, RecetaSugerida)]
    return sugerencias


def mostrar_receta(plato, instrucciones):
    """Imprime una receta formateada."""
    print(f"\n>>> {plato.upper()} <<<")
    print("Preparacion:")
    for paso in instrucciones.split(". "):
        if paso.strip():
            print(f"   - {paso.strip()}")
    print()


def main():
    print("\n" + "=" * 55)
    print("SISTEMA EXPERTO: CHEF PRIVADO")
    print("=" * 55)
    print("Dime que quieres comer (ingrediente o nombre del plato)")
    print("y te sugerire una receta.")
    print("-" * 55)

    while True:
        print("\nMENU PRINCIPAL")
        print("1. Buscar receta por lo que deseo comer")
        print("2. Ver todas las recetas disponibles")
        print("3. Salir")

        opcion = input("\nSelecciona una opcion: ").strip()

        if opcion == "1":
            deseo = input("\n¿Que te apetece comer? (ej: 'pollo', 'chocolate', 'sopa'): ").strip().lower()
            if not deseo:
                print("No has escrito nada.")
                continue

            sugerencias = buscar_recetas_por_deseo(deseo)

            if sugerencias:
                print(f"\nEncontradas {len(sugerencias)} receta(s) para '{deseo}':")
                for i, (nombre, _) in enumerate(sugerencias, 1):
                    print(f"{i}. {nombre}")
                ver = input("\n¿Quieres ver la preparacion de alguna? (numero o 'no'): ").strip()
                if ver.isdigit() and 1 <= int(ver) <= len(sugerencias):
                    idx = int(ver) - 1
                    mostrar_receta(sugerencias[idx][0], sugerencias[idx][1])
                elif ver.lower() != 'no':
                    print("Opcion no valida.")
            else:
                print(f"\nNo tengo ninguna receta con '{deseo}'. Prueba con otro ingrediente o nombre.")

        elif opcion == "2":
            temp_engine = ChefExperto()
            temp_engine.reset()
            cargar_conocimiento(temp_engine)
            platos = [f for f in temp_engine.facts.values() if isinstance(f, Plato)]
            if not platos:
                print("No hay recetas cargadas.")
            else:
                print("\nRECETARIO COMPLETO:")
                for i, plato in enumerate(platos, 1):
                    print(f"{i}. {plato['nombre']}")
            ver = input("\n¿Ver detalles de alguna receta? (numero o 'no'): ").strip()
            if ver.isdigit() and 1 <= int(ver) <= len(platos):
                idx = int(ver) - 1
                plato = platos[idx]
                mostrar_receta(plato['nombre'], plato['instrucciones'])

        elif opcion == "3":
            print("\nBuen provecho. Hasta pronto.")
            break
        else:
            print("Opcion invalida. Elige 1, 2 o 3.")


if __name__ == "__main__":
    main()