import collections
import collections.abc

# Parche: Si 'Mapping' no existe en 'collections', lo tomamos de 'collections.abc'
if not hasattr(collections, "Mapping"):
    setattr(collections, "Mapping", collections.abc.Mapping)

print("Parche de compatibilidad aplicado. 'experta' deberia funcionar correctamente.")