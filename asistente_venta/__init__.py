from trytond.pool import Pool
from .asistente_venta import *
from .sale import *


def register():
    Pool.register(
        TipoYCategoria,
        Producto,
        AvisoComun,
        AvisoEspecial,
        FunebreComun,
        FunebreDestacado,
        ClasificadoComun,
        ClasificadoDestacado,
        EdictoJudicial,
        Insert,
        Suplemento,
        Centimetros,
        Radio,
        Digital,
        SeleccionFechas,
        FormaVenta,
        Sale,
        SaleLine,
        module='asistente_venta', type_='model')
    Pool.register(
        AsistenteWizard,
        EleccionFormaVenta,
        module='asistente_venta', type_='wizard')
