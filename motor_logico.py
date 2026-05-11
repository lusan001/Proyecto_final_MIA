from experta import *  # noqa: PLC0414  # pyright: ignore[reportWildcardImportFromLibrary]

class Sintoma(Fact):
    pass

class EntrenadorExperto(KnowledgeEngine):
    
    # REGLA 1: Problema en Banda
    @Rule(Sintoma(nombre='lateral_ofensivo'), Sintoma(nombre='contraataque_rival'))
    def regla_banda(self):
        self.declare(Fact(
            diag="Falta de Equilibrio Defensivo en Banda",
            accion="Bajar al lateral inmediatamente o pedir ayuda al extremo defensivo.",
            severidad="ALTA",
            tipo="TÁCTICA"
        ))

    # REGLA 2: Medio Campo Perdido
    @Rule(Sintoma(nombre='pérdidas_centro'), Sintoma(nombre='presion_baja'))
    def regla_medio(self):
        self.declare(Fact(
            diag="Pérdida de Control del Medio Campo",
            accion="Cambiar a 4-4-2 rombo o aumentar la presión desde el frente.",
            severidad="MEDIA",
            tipo="TÁCTICA"
        ))

    # REGLA 3: Agotamiento
    @Rule(Sintoma(nombre='cansancio'), Sintoma(nombre='velocidad_baja'))
    def regla_cansancio(self):
        self.declare(Fact(
            diag="Agotamiento Físico Colectivo",
            accion="Realizar dobles cambios tácticos y bajar la intensidad del pressing.",
            severidad="CRÍTICA",
            tipo="FÍSICA"
        ))

    # REGLA 4: Lesión de Rodilla
    @Rule(Sintoma(nombre='dolor_rodilla'), Sintoma(nombre='cojera'))
    def regla_lesion_rodilla(self):
        self.declare(Fact(
            diag="Sospecha de Lesión de LCA/Menisco",
            accion="Sustitución inmediata. No forzar. Protocolo RICE (Hielo, Reposo).",
            severidad="URGENTE",
            tipo="MÉDICA"
        ))

    # REGLA 5: Calambre
    @Rule(Sintoma(nombre='calambre'), Sintoma(nombre='dolor_localizado'))
    def regla_calambre(self):
        self.declare(Fact(
            diag="Calambre Muscular Agudo",
            accion="Estiramiento suave, hidratación con electrolitos, masaje local.",
            severidad="LEVE",
            tipo="MÉDICA"
        ))

    # REGLA 6: Golpe en la Cabeza
    @Rule(Sintoma(nombre='golpe_cabeza'), Sintoma(nombre='confusion'))
    def regla_conmocion(self):
        self.declare(Fact(
            diag="Posible Conmoción Cerebral",
            accion="Sustitución obligatoria inmediata. Protocolo de conmoción.",
            severidad="URGENTE",
            tipo="MÉDICA"
        ))

    def obtener_resultados(self):
        resultados = []
        for f in self.facts.values():
            if 'diag' in f:
                resultados.append({
                    "diagnostico": f['diag'],
                    "accion": f['accion'],
                    "severidad": f['severidad'],
                    "tipo": f['tipo']
                })
        return resultados