from trytond.pool import Pool
from .reportes import *

Pool.register(
    Sale,
    Invoice,
    SeleccionEntidad,
    module='reportes', type_='model')

Pool.register(
    ReporteClasificado,
    ReporteAvisoComercial,
    ReporteSalePresupuestador,
    ReporteEstadoCuentaEntidad,
    ReporteInvoicePresupuestador,
    module='reportes', type_='report')

Pool.register(
    LanzarReporteComercial,
    OpenEstadoCuentaEntidad,
    LanzarReporteClasificado,
    module='reportes', type_='wizard')
