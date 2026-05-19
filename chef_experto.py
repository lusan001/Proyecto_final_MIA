import collections
if not hasattr(collections, 'Mapping'):
    import collections.abc
    collections.Mapping = collections.abc.Mapping # type: ignore
    collections.MutableMapping = collections.abc.MutableMapping # type: ignore

from experta import Fact, KnowledgeEngine, Rule, TEST, MATCH
import json
import os
import ollama
from fpdf import FPDF

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
    @Rule(  # Coincidencia por nombre del plato (si el deseo es parte del nombre)
        Deseo(termino=MATCH.t),
        Plato(nombre=MATCH.n, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda t, n: t.lower() in n.lower()),
        salience=10
    )
    def coincidir_nombre(self, t, n, i, m):
        self.declare(RecetaSugerida(plato=n, instrucciones=i, macros=m))

    @Rule(  # Coincidencia por ingrediente (si el deseo es parte del ingrediente)
        Deseo(termino=MATCH.t),
        Ingrediente(plato=MATCH.p, ingrediente=MATCH.ing),
        Plato(nombre=MATCH.p, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda t, ing: t.lower() == ing.lower()),
        salience=5
    )
    def coincidir_ingrediente(self, t, p, i, m):
        self.declare(RecetaSugerida(plato=p, instrucciones=i, macros=m))

    @Rule(  # Coincidencia semantica avanzada usando contexto y nombre del plato
        Deseo(contexto=MATCH.ctx),
        Plato(nombre=MATCH.n, instrucciones=MATCH.i, macros=MATCH.m),
        TEST(lambda ctx, n: ("ligero" in ctx and "ensalada" in n.lower()) or
                            ("caliente" in ctx and "sopa" in n.lower()) or
                            ("dulce" in ctx and "chocolate" in n.lower())),
        salience=8
    )
    def coincidencia_semantica(self, ctx, n, i, m):  # coincidencia semantica avanzada usando contexto y nombre del plato
        self.declare(RecetaSugerida(plato=n, instrucciones=i, macros=m))

# 3. BASE DE CONOCIMIENTO (RECETAS)
def cargar_conocimiento(engine):
    recetas = [
        ("Pollo al horno con especias", "1. Adobar el pollo con sal, pimienta, romero y ajo. 2. Hornear a 180°C por 45 min. 3. Servir con papas.", {"calorias": 450, "proteinas": 35, "carbos": 15, "grasas": 20}),
        ("Ensalada Cesar", "1. Lavar la lechuga. 2. Agregar pollo desmenuzado. 3. Añadir aderezo Cesar y crutones.", {"calorias": 320, "proteinas": 18, "carbos": 10, "grasas": 22}),
        ("Sopa de tomate", "1. Sofreir cebolla y ajo. 2. Agregar tomates pelados y caldo. 3. Cocinar 20 min y licuar.", {"calorias": 150, "proteinas": 5, "carbos": 25, "grasas": 4}),
        ("Tacos de carnitas", "1. Dorar la carne de cerdo en su grasa. 2. Calentar tortillas. 3. Servir con cebolla, cilantro y salsa.", {"calorias": 600, "proteinas": 30, "carbos": 45, "grasas": 30}),
        ("Pastel de chocolate", "1. Batir huevos con azucar. 2. Agregar harina, cacao y levadura. 3. Hornear 30 min a 180°C.", {"calorias": 400, "proteinas": 6, "carbos": 60, "grasas": 12}),
        ("Revuelto de champinones", "1. Saltear champinones laminados con ajo. 2. Incorporar huevo batido. 3. Cocinar hasta cuajar.", {"calorias": 220, "proteinas": 14, "carbos": 4, "grasas": 16}),
        ("Ceviche de pescado", "1. Cortar pescado en cubos. 2. Marinar con jugo de limon, cebolla morada, cilantro y aji. 3. Reposar 20 min.", {"calorias": 280, "proteinas": 28, "carbos": 10, "grasas": 8}),
        ("Ensalada de frutas", "1. Cortar frutas. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 150, "proteinas": 3, "carbos": 25, "grasas": 4}),
        ("Ensalada de verduras", "1. Cortar verduras. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 100, "proteinas": 2, "carbos": 15, "grasas": 0}),
        ("Ensalada de aguacate", "1. Cortar aguacate. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 80, "proteinas": 2, "carbos": 10, "grasas": 0}),
        ("Ensalada de lechuga y tomate", "1. Cortar lechuga y tomate. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 50, "proteinas": 1, "carbos": 5, "grasas": 0}),
        ("Ensalada de zanahorias", "1. Cortar zanahorias. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 40, "proteinas": 1, "carbos": 5, "grasas": 0}),
        ("Natillas caseras", "1. Calentar leche con azucar y vainilla. 2. Batir huevos y agregar a la leche. 3. Cocinar a fuego bajo hasta espesar.", {"calorias": 250, "proteinas": 6, "carbos": 30, "grasas": 8}),
        ("Pastel de manzana", "1. Preparar masa con harina, mantequilla y azucar. 2. Rellenar con manzanas cortadas y canela. 3. Hornear 40 min a 180°C.", {"calorias": 350, "proteinas": 4, "carbos": 50, "grasas": 10}),
        ("Brownie de chocolate", "1. Derretir chocolate con mantequilla. 2. Batir huevos con azucar. 3. Agregar harina y mezclar. 4. Hornear 25 min a 180°C.", {"calorias": 450, "proteinas": 5, "carbos": 60, "grasas": 20}),
        ("Patata asada con romero", "1. Lavar patatas y pintar. 2. Hornear a 180°C por 20 min. 3. Servir con salsa de romero.", {"calorias": 200, "proteinas": 6, "carbos": 20, "grasas": 10}),
        ("Sopa de verduras", "1. Sofreir cebolla y ajo. 2. Agregar verduras picadas y caldo. 3. Cocinar 30 min y servir.", {"calorias": 120, "proteinas": 4, "carbos": 20, "grasas": 3}),
        ("Macarrones con queso", "1. Cocer macarrones. 2. Preparar salsa con queso y leche. 3. Mezclar todo y gratinar.", {"calorias": 500, "proteinas": 15, "carbos": 70, "grasas": 20}),
        ("Pollo al ajillo", "1. Dorar pollo con ajo en aceite de oliva. 2. Agregar vino blanco y cocinar hasta reducir.", {"calorias": 400, "proteinas": 30, "carbos": 10, "grasas": 15}),
        ("Tacos de pollo", "1. Dorar pollo en su grasa. 2. Calentar tortillas. 3. Servir con cebolla, cilantro y salsa.", {"calorias": 500, "proteinas": 30, "carbos": 45, "grasas": 30}),
        ("Ensalada de aguacate y tomate", "1. Cortar aguacate y tomate. 2. Incorporar jugo de limon. 3. Servir con yogur natural.", {"calorias": 80, "proteinas": 2, "carbos": 10, "grasas": 0}),
    ]
    return recetas

def obtener_ingredientes(nombre_plato):
    """Devuelve la lista de ingredientes para un plato dado.
    Si no se encuentra el plato, devuelve lista vacía.
    """
    mapping = {
        "Pollo al horno con especias": ["pollo", "romero", "sal", "pimienta", "ajo", "papas"],
        "Ensalada Cesar": ["lechuga", "pollo", "aderezo cesar", "crutones"],
        "Sopa de tomate": ["tomate", "cebolla", "ajo", "caldo"],
        "Tacos de carnitas": ["cerdo", "tortilla", "cilantro", "cebolla"],
        "Pastel de chocolate": ["huevo", "azucar", "harina", "cacao"],
        "Revuelto de champinones": ["champinones", "huevo", "ajo"],
        "Ceviche de pescado": ["pescado", "limon", "cebolla morada", "cilantro", "aji"],
        "Ensalada de frutas": ["frutas mixtas", "limon", "yogur"],
        "Ensalada de verduras": ["verduras mixtas", "limon", "yogur"],
        "Ensalada de aguacate": ["aguacate", "limon", "yogur"],
        "Ensalada de lechuga y tomate": ["lechuga", "tomate", "limon"],
        "Ensalada de zanahorias": ["zanahorias", "limon", "yogur"],
        "Natillas caseras": ["leche", "azucar", "huevo", "vainilla"],
        "Pastel de manzana": ["harina", "mantequilla", "azucar", "manzana", "canela"],
        "Brownie de chocolate": ["chocolate", "mantequilla", "huevo", "harina"],
        "Patata asada con romero": ["patatas", "romero", "aceite"],
        "Sopa de verduras": ["verduras mixtas", "caldo", "cebolla", "ajo"],
        "Macarrones con queso": ["macarrones", "queso", "leche"],
        "Pollo al ajillo": ["pollo", "ajo", "vino blanco", "aceite"],
        "Tacos de pollo": ["pollo", "tortilla", "cilantro", "cebolla"],
        "Ensalada de aguacate y tomate": ["aguacate", "tomate", "limon"],
    }

    return mapping.get(nombre_plato, [])


# 4. Generacion de PDF

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Chef Privado - Tu Receta', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf(receta_sugerida):
    if FPDF is None:
        print("\n❌ ERROR: No se puede generar el PDF. Instala 'fpdf' con: pip install fpdf")
        return

    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 12, receta_sugerida['plato'], 0, 1)
    pdf.ln(2)

    pdf.set_fill_color(230, 230, 230)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Información Nutricional:', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 11)

    macros = receta_sugerida['macros']
    linea = f"Calorías: {macros['calorias']} kcal | Proteínas: {macros['proteinas']}g | Carbs: {macros['carbos']}g | Grasas: {macros['grasas']}g"
    pdf.cell(0, 8, linea, 0, 1)
    pdf.ln(2)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Ingredientes:', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 11)

    ingredientes = obtener_ingredientes(receta_sugerida['plato'])
    for ing in ingredientes:
        pdf.cell(0, 6, f"• {ing}", 0, 1)
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Instrucciones:', 0, 1, 'L', True)
    pdf.set_font('Arial', '', 11)

    pasos = receta_sugerida['instrucciones'].split('. ')
    for paso in pasos:
        if paso.strip():
            pdf.multi_cell(0, 6, f"   {paso.strip()}.")

    nombre_archivo = f"receta_{receta_sugerida['plato'].lower().replace(' ', '_')}.pdf"
    pdf.output(nombre_archivo)
    print(f"\n✅ ¡PDF Generado! Guardado como: {nombre_archivo}")

# 5. INTERFAZ DE USUARIO | MAIN
def buscar_recetas_por_deseo(texto_usuario):
    engine = ChefExperto()
    engine.reset()
    cargar_conocimiento(engine)

    print("🤖 Consultando a Ollama (LLM local)...")
    # Aquí ocurre la magia real
    deseo_fact = llm_interpretar_deseo(texto_usuario)
    engine.declare(deseo_fact)

    engine.run()

    sugerencias = []
    for f in engine.facts.values():
        if isinstance(f, RecetaSugerida):
            sugerencias.append({
                'plato': f['plato'],
                'instrucciones': f['instrucciones'],
                'macros': f['macros']
            })
    return sugerencias

def main():
    print("\n" + "=" * 55)
    print("👨‍🍳 CHEF PRIVADO (CON OLLAMA LOCAL)")
    print("=" * 55)
    print("Prueba: 'quiero algo ligero', 'tengo ganas de pollo', 'quiero sopa caliente'")

    # Verificar si Ollama está corriendo
    if ollama:
        try:
            ollama.list()
            print("✅ Ollama detectado y listo.")
        except:
            print("⚠️  Advertencia: No se pudo conectar con Ollama. Asegúrate de que esté corriendo (ollama serve).")

    while True:
        print("\n1. Buscar receta (IA Local)")
        print("2. Generar PDF")