import collections
if not hasattr(collections, 'Mapping'):
    import collections.abc
    collections.Mapping = collections.abc.Mapping
    collections.MutableMapping = collections.abc.MutableMapping

from experta import Fact, KnowledgeEngine, Rule, TEST, MATCH


# 1. DEFINICION DE HECHOS
class Plato(Fact):
    """Nombre del plato y sus instrucciones de preparacion."""
    pass

class Ingrediente(Fact):
    """Relacion plato -> ingrediente necesario."""
    pass

class Deseo(Fact):
    """Lo que el usuario expresa que quiere comer (termino de busqueda)."""
    pass

class RecetaSugerida(Fact):
    """Resultado de la inferencia: plato que satisface el deseo."""
    pass


# 2. MOTOR DE INFERENCIA
class ChefExperto(KnowledgeEngine):

    @Rule(
        Deseo(termino=MATCH.t),
        Plato(nombre=MATCH.n, instrucciones=MATCH.i),
        TEST(lambda t, n: t.lower() in n.lower()),
        salience=10
    )
    def coincidir_nombre(self, t, n, i):
        """Si el termino aparece en el nombre del plato, sugerirlo."""
        self.declare(RecetaSugerida(plato=n, instrucciones=i))

    @Rule(
        Deseo(termino=MATCH.t),
        Ingrediente(plato=MATCH.p, ingrediente=MATCH.ing),
        Plato(nombre=MATCH.p, instrucciones=MATCH.i),
        TEST(lambda t, ing: t.lower() == ing.lower()),
        salience=5
    )
    def coincidir_ingrediente(self, t, p, i):
        """Si el termino es exactamente un ingrediente, sugerir el plato."""
        self.declare(RecetaSugerida(plato=p, instrucciones=i))


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