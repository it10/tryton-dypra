# -*- coding: utf-8 -*-

from trytond.pool import Pool
from decimal import Decimal
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from trytond.wizard import Wizard, StateView, StateTransition, Button
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval, Bool, Or, And, Not, Equal
from trytond.transaction import Transaction

tyc_cat_diario_efec =[
                    ('Aviso Comun', '1- Aviso Comun'),
                    ('Aviso Especial', '2- Aviso Especial'),
                    ('Clasificado', '3- Clasificado'),
                    ('Funebre', '4- Funebre'),
                    ('Edicto', '5- Edicto'),
                    ('Insert', '6- Insert'),
                    ('Suplemento', '7- Suplemento'),
                ]
tyc_cat_digital_efec=[('Costo Provincial', '1- Costo Provincial'),('Costo Nacional', '2- Costo Nacional'),('Costo Oficial', '3- Costo Oficial')]
tyc_cat_radio_efec=[('Costo Provincial', '1- Costo Provincial'),('Costo Nacional', '2- Costo Nacional'),('Costo Oficial', '3- Costo Oficial')]

tyc_cat_diario_corriente =[
                            ('Aviso Comun', '1- Aviso Comun'),
                            ('Aviso Especial', '2- Aviso Especial'),
                            ('Clasificado', '3- Clasificado'),
                            ('Funebre', '4- Funebre'),
                            ('Edicto', '5- Edicto'),
                            ('Centimetros', '6- Centimetros'),
                          ]

lista_origen = [
                ('Ninguno','Ninguno'),
                ('Composicion','Composicion'),
                ('E-mail','E-mail'),
                ('Scanner','Scanner'),
                ('Sigue','Sigue'),
                ('Sin cargo','Sin cargo'),
                ]

aviso_ubicacion= [
                    ('Libre', '1- Libre (+0%)'),
                    ('Par', '2- Pagina Par (+25%)'),
                    ('Impar', '3- Pagina Impar (+25%)'),
                    ('Tapa', '4- Tapa (+50%)'),
                    ('Central', '5- Central (+50%)'),
                    ('Contratapa', '6- Contratapa (+50%)'),
                    ('Suplemento', '7- Suplemento (+0%)'),
                 ]

select_apariciones=    [
                           ('1', '1- Dia/s especifico/s'),
                           ('7', '2- Semana/s(7 dias)'),
                           ('30', '3- Mes/es (30 dias)'),
                           ('365', '4- ANUAL(365 dias)'),
                       ]

tipo_bonificacion= [
                       ('$', '$- Fijo'),
                       ('p', '%- Porcentual'),
                   ]


insert_tipo_impresion= [
                            ('0', '1- Si'),
                            ('1', '2- No'),
                       ]

horarios= [
                ('Rotativas', '1- Rotativas'),
                ('c/30 minutos', '2- c/30 minutos'),
                ('Cierre de la Programacion', '3- Cierre de la Programacion'),
                ('Programas Centrales', '4- Programas Centrales'),
                ('Manual', '5- Horario'),
          ]


class TipoYCategoria(ModelSQL,ModelView):
    'Tipo y Categoria'
    __name__ = 'asistente_venta.tipo_y_categoria.start'
    efectivo = fields.Boolean("Efectivo",states={'readonly':Bool(Eval('cc'))})
    cliente_efec= fields.Many2One('party.party', 'Cliente',domain=[('categories.parent','like','Cliente'),('categories','not like','Cuenta Corriente')],
                                                           states={'required':Bool(Eval('efectivo')),
                                                                   'readonly':Not(Bool(Eval('efectivo')))
                                                                   })
    term_pago_efec = fields.Many2One('account.invoice.payment_term','FORMA DE PAGO', domain=[('name','=','Efectivo')],
                                                                                     states={'required':Bool(Eval('efectivo')),
                                                                                             'readonly':Not(Bool(Eval('efectivo')))
                                                                                            })

    diario_efec = fields.Boolean('Diario',select=False,states={'readonly':Or(Or(Eval('digital_efec',True),Eval('radio_efec',True)),Not(Bool(Eval('efectivo'))))
                                                               })
    digital_efec = fields.Boolean('Digital', select=False,states={'readonly': Or(Or(Eval('diario_efec',True),Eval('radio_efec',True)),Not(Bool(Eval('efectivo'))))
                                                                  })
    radio_efec = fields.Boolean('Radio', select=False,states={'readonly': Or(Or(Eval('digital_efec',True),Eval('diario_efec',True)),Not(Bool(Eval('efectivo'))))
                                                              })
    cat_diario_efec = fields.Selection(tyc_cat_diario_efec, 'Categoria',required=True, states={'readonly':Or(Not(Bool(Eval('diario_efec'))),Not(Bool(Eval('efectivo'))))})
    cat_digital_efec = fields.Selection(tyc_cat_digital_efec, 'Categoria', required=True,states={'readonly':Or(Not(Bool(Eval('digital_efec'))),Not(Bool(Eval('efectivo'))))})
    cat_radio_efec = fields.Selection(tyc_cat_radio_efec, 'Categoria', required=True,states={'readonly':Or(Not(Bool(Eval('radio_efec'))),Not(Bool(Eval('efectivo'))))})
    
    cc = fields.Boolean("Cuenta Corriente",states={'readonly':Bool(Eval('efectivo'))})
    cliente_cc= fields.Many2One('party.party', 'Cliente',domain=[ 'OR',[('categories','like','Cuenta Corriente')],[('categories.parent','like','Cuenta Corriente')]],
                                                         states={'required':Bool(Eval('cc')),
                                                                  'readonly':Not(Bool(Eval('cc')))
                                                                })
    term_pago_cc = fields.Many2One('account.invoice.payment_term', 'FORMA DE PAGO',domain=[('name','=','Cuenta Corriente')],
                                                                                   states={'required':Bool(Eval('cc')),
                                                                                            'readonly':Not(Bool(Eval('cc')))
                                                                                           })
    diario_cc = fields.Boolean('Diario',select=False,states={'readonly':Not(Bool(Eval('cc')))})
    cat_diario_cc = fields.Selection(tyc_cat_diario_corriente, 'Categoria',required=True, states={'readonly':Or(Not(Bool(Eval('diario_cc'))),Not(Bool(Eval('cc'))))})
  
    # @staticmethod
    # def default_term_pago_cc():
    #     PaymentTerm = Pool().get('account.invoice.payment_term')
    #     term_pago = PaymentTerm.search([('name','=','Cuenta Corriente')])[0]
    #     #term_pago=(PaymentTerm.search([('name', '=','Cuenta Corriente')])[0])
    #     return term_pago
    #     #return 'Cuenta Corriente'




class Producto(ModelSQL,ModelView):
    'Producto'
    __name__ = 'asistente_venta.producto'
    cat = fields.Char('Categoria Seleccionada', readonly=True)
    producto = fields.Many2One('product.template', 'Producto',domain=[('category', '=', Eval('cat'))], required=True)
    origen = fields.Selection(lista_origen,'Origen', states={'required':Eval('cat')!='Diario / Centimetros',
                                                             'readonly':Eval('cat')=='Diario / Centimetros',
                                                            }
                                                            )

    @staticmethod
    def default_origen():
        return 'Ninguno'


class AvisoComun(ModelSQL,ModelView):
    'AvisoComun'
    __name__ = 'asistente_venta.aviso_comun'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=False, required=True)
    nro_pag = fields.Char('Pagina Nro.', states={'readonly': And(Not(Equal(Eval('ubicacion'),'Par')),Not(Equal(Eval('ubicacion'),'Impar')))})
    suplemento = fields.Char('Suplemento', states={'readonly': (Eval('ubicacion') != 'Suplemento')})
    cant_centimetros = fields.Numeric('Centimetros', required=True)
    cant_columnas = fields.Numeric('Columnas', required=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    descripcion = fields.Text('Descripcion',readonly=False)


    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_nro_pag():
        return '-1'

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}



class AvisoEspecial(ModelSQL,ModelView):
    'AvisoEspecial'
    __name__ = 'asistente_venta.aviso_especial'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=True, required=True)
    cant_centimetros = fields.Char('Centimetros', size=8, readonly=True)
    cant_columnas = fields.Char('Columnas', size=8, readonly=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    descripcion = fields.Text('Descripcion',readonly=False)


    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}

class FunebreComun(ModelSQL,ModelView):
    'FunebreComun'
    __name__ = 'asistente_venta.funebre_comun'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=True, required=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('Bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    descripcion = fields.Text('Descripcion',readonly=False)

    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}

class FunebreDestacado(ModelSQL,ModelView):
    'FunebreDestacado'
    __name__ = 'asistente_venta.funebre_destacado'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=True, required=True)
    cant_centimetros = fields.Numeric('Centimetros', readonly=False, required=True)
    cant_columnas = fields.Numeric('Columnas', readonly=False, required=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('Bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    descripcion = fields.Text('Descripcion',readonly=False)

    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}

class ClasificadoComun(ModelSQL,ModelView):
    'ClasificadoComun'
    __name__ = 'asistente_venta.clasificado_comun'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=True, required=True)
    tipo = fields.Char('Tipo', readonly=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('Bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    descripcion = fields.Text('Descripcion',readonly=False)

    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}

class ClasificadoDestacado(ModelSQL,ModelView):
    'ClasificadoDestacado'
    __name__ = 'asistente_venta.clasificado_destacado'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=True, required=True)
    tipo = fields.Char('Tipo', readonly=True)
    cant_centimetros = fields.Numeric('Centimetros', readonly=False, required=True)
    cant_columnas = fields.Numeric('Columnas',  readonly=False, required=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('Bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    descripcion = fields.Text('Descripcion',readonly=False)

    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}

class EdictoJudicial(ModelSQL,ModelView):
    'EdictoJudcial'
    __name__ = 'asistente_venta.edicto_judicial'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=True, required=True)
    cant_lineas = fields.Numeric('Cantidad de lineas', required=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('Bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    descripcion = fields.Text('Descripcion',readonly=False)

    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}

class Insert(ModelSQL,ModelView):
    'Insert'
    __name__ = 'asistente_venta.insert'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=True, required=True)
    impresion = fields.Selection(insert_tipo_impresion, 'Impresion propia', readonly=False, required=True)
    monto = fields.Numeric('Precio adhoc $', required=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('Bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    descripcion = fields.Text('Descripcion',readonly=False)

    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    @staticmethod
    def default_impresion():
        return '0'


    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}

class Suplemento(ModelSQL,ModelView):
    'Suplemento'
    __name__ = 'asistente_venta.suplemento'
    ubicacion = fields.Selection(aviso_ubicacion, 'Ubicacion', readonly=True, required=True)
    cant_paginas = fields.Numeric('Cantidad de paginas', required=True)
    precio_edicion = fields.Numeric('Precio de edicion', required=True)
    apariciones = fields.Selection(select_apariciones, 'Apariciones',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('Nro.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('Inicio', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('Bonificacion', select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('Valor', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('Motivo',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)

    @staticmethod
    def default_bonificacion():
        return False

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}

#caso especial de venta en cuenta corriente
class Centimetros(ModelSQL,ModelView):
    'Centimetros'
    __name__ = 'asistente_venta.centimetros'
    cant_centimetros = fields.Numeric('Centimetros', readonly=False, required=True)
    cant_columnas = fields.Numeric('Columnas', readonly=False, required=True)
    precio_cm = fields.Numeric('Precio x cm.', readonly=False, required=True)


class Radio(ModelSQL,ModelView):
    'Radio'
    __name__ = 'asistente_venta.radio'
    nombre = fields.Char('nombre', states={'invisible': True})
    precio_mencion = fields.Numeric('PRECIO', states={'invisible': (Eval('nombre') != 'Columnistas'),
                                                      'required': (Eval('nombre') == 'Columnistas')})
    cantidad_menciones = fields.Numeric('NRO. MENCIONES', states={'invisible': (Eval('nombre') != 'Columnistas'),
                                                                  'required': (Eval('nombre') == 'Columnistas')})
    horario_programacion = fields.Selection(horarios, 'HS. PROGRAMACION', required=True)
    desde = fields.Char("DE", states={'readonly': (Eval('horario_programacion') != 'Manual')},required=True )
    hasta = fields.Char("A", states={'readonly': (Eval('horario_programacion') != 'Manual')},required=True )
    apariciones = fields.Selection(select_apariciones, 'APARICIONES',  on_change=['apariciones'], required=True)
    cant_apariciones = fields.Numeric('NRO.', states={'readonly': (Eval('apariciones') == '365')}, required=True)
    inicio = fields.Date('INICIO', states={'readonly': (Eval('apariciones') == '1')}, required=True)
    bonificacion = fields.Boolean('bonificacion',select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('VALOR', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('MOTIVO',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)
    mencion = fields.Text('MENCION',readonly=False)

    @staticmethod
    def default_bonificacion():
        return False

    def on_change_apariciones(self):
        if self.apariciones == '365':
            v = 1
            return {'cant_apariciones': v}
        return{}


class Digital(ModelSQL,ModelView):
    'Digital'
    __name__ = 'asistente_venta.digital'
    expandible = fields.Boolean('expandible',select=False)
    de = fields.Char("DE",readonly=True)
    a = fields.Char("A",states={'readonly': (Bool(Eval('expandible')) == False)},required=True)
    recargo = fields.Numeric('RECARGO', states={'readonly': (Bool(Eval('expandible')) == False)}, required=True)
    cant_meses = fields.Numeric('MESES', required=True)
    inicio = fields.Date('INICIO', required=True)
    bonificacion = fields.Boolean('bonificacion',select=False)
    tipo_bonif = fields.Selection(tipo_bonificacion, 'tipo_bonif' , states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    valor = fields.Numeric('VALOR', states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=True)
    motivo = fields.Char('MOTIVO',states={'readonly': (Bool(Eval('bonificacion')) == False)}, required=False)

    @staticmethod
    def default_bonificacion():
        return False



class SeleccionFechas(ModelSQL,ModelView):
    'SeleccionFechas'
    __name__ = 'asistente_venta.seleccion_fechas'
    cant_apariciones = fields.Numeric('Cantidad de apariciones ya seleccionadas', readonly=True)
    fecha = fields.Date('Fecha de la aparicion', required=True)
    venta = fields.Many2One('sale.sale','Venta')



class AsistenteWizard(Wizard):
    'AsistenteWizard'
    __name__ = 'asistente_venta.asistente_wizard'

    #-----------------------------------------INICIO-----------------------------------------#
    start = StateView('asistente_venta.tipo_y_categoria.start',
                      'asistente_venta.tipo_y_categoria_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Siguiente', 'eleccion_producto', 'tryton-go-next', default=True)])

    #-----------------------------------------PRODUCTO-----------------------------------------#
    producto = StateView('asistente_venta.producto',
                      'asistente_venta.producto_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'volver_start', 'tryton-go-previous'),
                      Button('Siguiente', 'datos_categoria', 'tryton-go-next', default=True)])

    #-----------------------------------------DIARIO-----------------------------------------#
    aviso_comun = StateView('asistente_venta.aviso_comun',
                      'asistente_venta.aviso_comun_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_aviso_comun', 'tryton-go-next', default=True)])

    aviso_especial = StateView('asistente_venta.aviso_especial',
                      'asistente_venta.aviso_especial_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_aviso_especial', 'tryton-go-next', default=True)])

    funebre_comun = StateView('asistente_venta.funebre_comun',
                      'asistente_venta.funebre_comun_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_funebre_comun', 'tryton-go-next', default=True)])

    funebre_destacado = StateView('asistente_venta.funebre_destacado',
                      'asistente_venta.funebre_destacado_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_funebre_destacado', 'tryton-go-next', default=True)])

    clasif_comun = StateView('asistente_venta.clasificado_comun',
                      'asistente_venta.clasificado_comun_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_clasif_comun', 'tryton-go-next', default=True)])

    clasif_destacado = StateView('asistente_venta.clasificado_destacado',
                      'asistente_venta.clasificado_destacado_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_clasif_destacado', 'tryton-go-next', default=True)])

    edicto = StateView('asistente_venta.edicto_judicial',
                      'asistente_venta.edicto_judicial_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_edicto', 'tryton-go-next', default=True)])

    insert = StateView('asistente_venta.insert',
                      'asistente_venta.insert_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_insert', 'tryton-go-next', default=True)])

    suplemento = StateView('asistente_venta.suplemento',
                      'asistente_venta.suplemento_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_suplemento', 'tryton-go-next', default=True)])

    centimetros = StateView('asistente_venta.centimetros',
                      'asistente_venta.centimetros_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_centimetros', 'tryton-go-next', default=True)])

    fechas_aviso_comun = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_aviso_comun', 'tryton-go-next', default=True)])

    fechas_aviso_especial = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_aviso_especial', 'tryton-go-next', default=True)])

    fechas_funebre_comun = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_funebre_comun', 'tryton-go-next', default=True)])

    fechas_funebre_destacado = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_funebre_destacado', 'tryton-go-next', default=True)])

    fechas_clasif_comun = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_clasif_comun', 'tryton-go-next', default=True)])

    fechas_clasif_destacado = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_clasif_destacado', 'tryton-go-next', default=True)])

    fechas_edicto = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_edicto', 'tryton-go-next', default=True)])

    fechas_insert = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_insert', 'tryton-go-next', default=True)])

    fechas_suplemento = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_suplemento', 'tryton-go-next', default=True)])

    #-----------------------------------------RADIO-----------------------------------------#
    radio = StateView('asistente_venta.radio',
                      'asistente_venta.radio_form',
                      [Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_radio', 'tryton-go-next', default=True)])

    fechas_radio = StateView('asistente_venta.seleccion_fechas',
                      'asistente_venta.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_radio', 'tryton-go-next', default=True)])

    #-----------------------------------------DIGITAL-----------------------------------------#
    digital = StateView('asistente_venta.digital',
                  'asistente_venta.digital_form',
                  [Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                   Button('Siguiente', 'terminar_digital', 'tryton-go-next', default=True)])


    volver_start = StateTransition()
    eleccion_producto = StateTransition()
    datos_categoria = StateTransition()
    #--------------------------------------------------
    terminar_aviso_comun = StateTransition()
    terminar_fechas_aviso_comun = StateTransition()
    #--------------------------------------------------
    terminar_aviso_especial = StateTransition()
    terminar_fechas_aviso_especial = StateTransition()
    #--------------------------------------------------
    terminar_funebre_comun = StateTransition()
    terminar_fechas_funebre_comun = StateTransition()
    #--------------------------------------------------
    terminar_funebre_destacado = StateTransition()
    terminar_fechas_funebre_destacado = StateTransition()
    #--------------------------------------------------
    terminar_clasif_comun = StateTransition()
    terminar_fechas_clasif_comun = StateTransition()
    #--------------------------------------------------
    terminar_clasif_destacado = StateTransition()
    terminar_fechas_clasif_destacado = StateTransition()
    #--------------------------------------------------
    terminar_edicto = StateTransition()
    terminar_fechas_edicto = StateTransition()
    #--------------------------------------------------
    terminar_insert = StateTransition()
    terminar_fechas_insert = StateTransition()
    #--------------------------------------------------
    terminar_suplemento = StateTransition()
    terminar_fechas_suplemento = StateTransition()
    #--------------------------------------------------
    terminar_centimetros = StateTransition()
    #--------------------------------------------------
    terminar_radio = StateTransition()
    terminar_fechas_radio = StateTransition()
    #--------------------------------------------------
    terminar_digital = StateTransition()
    #--------------------------------------------------

    def crear_venta(self,term_pago,cliente):
        date = Pool().get('ir.date')
        sale = Pool().get('sale.sale')

        #calculo del invoice address
        invoice_address = cliente.address_get(type='invoice')
        shipment_address = cliente.address_get(type='delivery')
        venta = sale.create([{
                    'party':cliente,
                    'payment_term': term_pago,
                    'invoice_address' : invoice_address,
                    'shipment_address' : shipment_address,
                    'sale_date' : date.today(),
                    'state' : 'quotation',
                    }])[0]
        venta.save()
        return venta

    def crear_linea_comentario_texto_aviso(self,venta,texto):
        linea = Pool().get('sale.line')
        nueva = linea.create([{
                    'sale':venta,
                    'type':'comment',
                    'description':'TEXTO DEL AVISO:\n' + texto,
                    }])[0]
        nueva.save()
       
    def crear_linea_producto_diario(self,venta,producto,precio_unitario,cantidad,pub):
        linea = Pool().get('sale.line')
        tax = Pool().get('sale.line-account.tax')
        nueva = linea.create([{
                    'sale':venta,
                    'product': producto,
                    'description':' ',
                    'sequence':'0',
                    'type':'line',
                    'unit': producto.default_uom,
                    'unit_price':precio_unitario,
                    'quantity':cantidad,
                    'categoria_diario':True,
                    'pub_presup_diario':pub,
                    }])[0]
        nueva.save()
        try:
            impuestos_prod = producto.category.parent.customer_taxes
            for impuesto_cliente in impuestos_prod:
                impuesto_linea = tax.create([{
                    'line' : linea(nueva),
                    'tax' : impuesto_cliente
                    }])[0]
                impuesto_linea.save()
        except:
            pass
        return nueva

    # LUCHO
    def crear_linea_producto_radio(self,venta,producto,precio_unitario,pub):
        linea = Pool().get('sale.line')
        tax = Pool().get('sale.line-account.tax')
        nueva = linea.create([{
                    'sale':venta,
                    'product': producto,
                    'description':' ',
                    'sequence':'0',
                    'type':'line',
                    'unit': producto.default_uom,
                    'unit_price':precio_unitario,
                    'quantity':'1',
                    'categoria_radio':True,
                    'pub_presup_radio':pub,
                    }])[0]
        nueva.save()
        try:
            impuestos_prod = producto.category.parent.customer_taxes
            for impuesto_cliente in impuestos_prod:
                impuesto_linea = tax.create([{
                    'line' : linea(nueva),
                    'tax' : impuesto_cliente
                    }])[0]
                impuesto_linea.save()
        except:
            pass
        return nueva

    def crear_linea_producto_digital(self,venta,producto,precio_unitario,pub):
        linea = Pool().get('sale.line')
        tax = Pool().get('sale.line-account.tax')
        nueva = linea.create([{
                    'sale':venta,
                    'product': producto,
                    'description':' ',
                    'sequence':'0',
                    'type':'line',
                    'unit': producto.default_uom,
                    'unit_price':precio_unitario,
                    'quantity':'1',
                    'categoria_dig':True,
                    'pub_presup_digital':pub,
                    }])[0]
        nueva.save()
        try:
            impuestos_prod = producto.category.parent.customer_taxes
            for impuesto_cliente in impuestos_prod:
                impuesto_linea = tax.create([{
                    'line' : linea(nueva),
                    'tax' : impuesto_cliente
                    }])[0]
                impuesto_linea.save()
        except:
            pass
        return nueva

    def crear_linea_recargo_expansion(self,venta,producto,precio_unitario,expansion):
        linea = Pool().get('sale.line')
        rec = linea.create([{
                    'sale':venta,
                    'sequence':'0',
                    'product' : producto,
                    'type':'line',
                    'unit': producto.default_uom,
                    'unit_price': precio_unitario,
                    'quantity':'1',
                    'description':'Recargo por expansion a:' + str(expansion) + '.'
                    }])[0]
        rec.save()

    def crear_linea_bonificacion(self,venta,producto,precio_unitario,motivo):
        linea = Pool().get('sale.line')
        bonif = linea.create([{
                    'sale':venta,
                    'sequence':'0',
                    'type':'line',
                    'product' : producto,
                    'unit': producto.default_uom,
                    'unit_price': precio_unitario,
                    'quantity':'1',
                    'description':'Bonificacion por ventas. \nMOTIVO:\n'+motivo
                    }])[0]
        bonif.save()



    def crear_linea_publicacion_diario(self,ubicacion,fecha,origen):
        sale = Pool().get('sale.sale')
        publicacion = Pool().get('edicion.publicacion_presupuestada_diario')
        pub = publicacion.create([{
            'fecha':fecha,
            'ubicacion':ubicacion,
            'origen': origen,
            'venta_cm' : 'no',
            }])[0]
        pub.save()
        return pub


    def crear_linea_publicacion_diario_centimetros(self,fecha):
        edicion = Pool().get('edicion.edicion')
        publicacion = Pool().get('edicion.publicacion_presupuestada_diario')
        pub = publicacion.create([{
            'fecha':fecha,
            'ubicacion':'Libre',
            'origen':'Ninguno',
            'venta_cm' : 'si',
            }])[0]
        pub.save()
        return pub

        

    def crear_linea_publicacion_radio(self,fecha,horario,desde,hasta):
        sale = Pool().get('sale.sale')
        publicacion = Pool().get('edicion.publicacion_presupuestada_radio')
        if horario != 'Manual':
            pub = publicacion.create([{
                'fecha':fecha,
                'horario_programacion' : horario,
                }])[0]
        else:
            pub = publicacion.create([{
                'fecha':fecha,
                'horario_programacion' : horario,
                'desde' : desde,
                'hasta' : hasta,
                }])[0]
        pub.save()
        return pub

    def crear_linea_publicacion_digital(self,fecha,expandible,a,recargo):
        sale = Pool().get('sale.sale')
        publicacion = Pool().get('edicion.publicacion_presupuestada_digital')
        if expandible:
            pub = publicacion.create([{
                'fecha':fecha,
                'expandible' : expandible,
                'a' : a,
                'recargo' : recargo,
                }])[0]
        else:
            pub = publicacion.create([{
                'fecha':fecha,
                'expandible' : expandible,
                }])[0]
        pub.save()
        return pub


#valores por defecto de los estados de vista

    def default_producto(self,fields):
        default = {}
        if (self.start.diario_efec):
            default['cat']=str('Diario') + ' / ' + str(self.start.cat_diario_efec)
        if (self.start.diario_cc):
            default['cat']=str('Diario') + ' / ' + str(self.start.cat_diario_cc)
        if self.start.digital_efec:
            default['cat']=str('Digital') + ' / ' + str(self.start.cat_digital_efec)
        if self.start.radio_efec:
            default['cat']=str('Radio') + ' / ' + str(self.start.cat_radio_efec)
        return default

    def default_aviso_comun(self,fields):
        default = {}
        default['cant_centimetros']=3
        default['cant_columnas']=1
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['tipo_bonif']='p'
        return default

    def default_aviso_especial(self,fields):
        default = {}
        cm=str(self.producto.producto.name).split('x')[-1]
        col=(str(self.producto.producto.name).split('x')[0]).split(' ')[-1]
        default['cant_centimetros']=cm
        default['cant_columnas']=col
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['tipo_bonif']='p'
        return default

    def default_funebre_comun(self,fields):
        default = {}
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['tipo_bonif']='p'
        return default

    def default_funebre_destacado(self,fields):
        default = {}
        default['cant_centimetros']=3
        default['cant_columnas']=1
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['tipo_bonif']='p'
        return default

    def default_clasif_comun(self,fields):
        default = {}
        default['tipo']=self.producto.producto.name.split(' x ')[0]
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['tipo_bonif']='p'
        return default


    def default_clasif_destacado(self,fields):
        default = {}
        default['tipo']=self.producto.producto.name.split(' x ')[0]
        default['cant_centimetros']=3
        default['cant_columnas']=1
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['tipo_bonif']='p'
        return default

    def default_edicto(self,fields):
        default = {}
        default['cant_lineas']=1
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['tipo_bonif']='p'
        return default

    def default_insert(self,fields):
        default = {}
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['tipo_bonif']='p'
        return default

    def default_suplemento(self,fields):
        default = {}
        default['cant_paginas']=1
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['precio_edicion']=1
        default['tipo_bonif']='p'
        return default

    def default_centimetros(self,fields):
        default = {}
        default['cant_centimetros']=1
        default['cant_columnas']=1
        default['precio_cm']=1
        return default

    def default_radio(self,fields):
        default = {}
        if self.producto.producto.name=='Columnistas':
            default['nombre']=self.producto.producto.name
        default['apariciones']='1'
        default['cant_apariciones']=1
        default['horario_programacion']='Rotativas'
        default['tipo_bonif']='p'
        return default

    def default_digital(self,fields):
        default = {}
        de=str(self.producto.producto.name).split(' ')[1]
        default['de']=de
        default['cant_meses']=1
        default['tipo_bonif']='p'
        return default

    def default_fechas_aviso_comun(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_aviso_comun.cant_apariciones) +1
            default['venta'] = self.fechas_aviso_comun.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    def default_fechas_aviso_especial(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_aviso_especial.cant_apariciones) +1
            default['venta'] = self.fechas_aviso_especial.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    def default_fechas_funebre_comun(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_funebre_comun.cant_apariciones) +1
            default['venta'] = self.fechas_funebre_comun.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    def default_fechas_funebre_destacado(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_funebre_destacado.cant_apariciones) +1
            default['venta'] = self.fechas_funebre_destacado.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    def default_fechas_clasif_comun(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_clasif_comun.cant_apariciones) +1
            default['venta'] = self.fechas_clasif_comun.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    def default_fechas_clasif_destacado(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_clasif_destacado.cant_apariciones) +1
            default['venta'] = self.fechas_clasif_destacado.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    def default_fechas_edicto(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_edicto.cant_apariciones) +1
            default['venta'] = self.fechas_edicto.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default


    def default_fechas_insert(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_insert.cant_apariciones) +1
            default['venta'] = self.fechas_insert.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    def default_fechas_suplemento(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_suplemento.cant_apariciones) +1
            default['venta'] = self.fechas_suplemento.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    def default_fechas_radio(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_radio.cant_apariciones) +1
            default['venta'] = self.fechas_radio.venta.id
        except:
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            term_pago = payment_term.search([('name','=','Efectivo')])[0]
            cliente = self.start.cliente_efec
            v = sale(self.crear_venta(term_pago,cliente))
            default['venta']=v.id
            default['cant_apariciones']=1
        return default

    @classmethod
    def __setup__(cls):
        super(AsistenteWizard, cls).__setup__()
        cls._error_messages.update({
            'error_wizard': 'Termino de pago o cliente no pertenecen a Efectivo',
            'error_wizard_dos': 'Venta Procesada'
            })
    # def transition_start(self):
    #     sale = Pool().get('sale.sale')
    #     party_cat = Pool().get('party.party-party.category')
    #     entidad = (sale(Transaction().context.get('active_id'))).party
    #     res_cat = party_cat.search([('party', '=',entidad)])[0].category
    #     term_pago = (sale(Transaction().context.get('active_id'))).payment_term
    #     if ((res_cat.parent.name == 'Cuenta Corriente') or (term_pago.name == 'Cuenta Corriente')):
    #         self.raise_user_error('error_wizard')
    #     if (sale(Transaction().context.get('active_id')).state=='processing'):
    #         self.raise_user_error('error_wizard_dos')
    #     return 'start_view'


#ACCION DE LAS TRANSICIONES

    def transition_volver_start(self):
        return 'start'

    def transition_eleccion_producto(self):
        return 'producto'

    def transition_datos_categoria(self):
        if self.start.diario_efec:
            if self.start.cat_diario_efec == 'Aviso Comun':
                return 'aviso_comun'
            elif self.start.cat_diario_efec == 'Aviso Especial':
                return 'aviso_especial'
            elif self.start.cat_diario_efec == 'Funebre':
                if(self.producto.producto.default_uom.symbol != 'cm'):
                    return 'funebre_comun'
                else:
                    return 'funebre_destacado'
            elif self.start.cat_diario_efec == 'Clasificado':
                if(self.producto.producto.default_uom.symbol != 'cm'):
                    return 'clasif_comun'
                else:
                    return 'clasif_destacado'
            elif self.start.cat_diario_efec == 'Edicto':
                return 'edicto'
            elif self.start.cat_diario_efec == 'Insert':
                return 'insert'
            elif self.start.cat_diario_efec == 'Suplemento':
                return 'suplemento'
        if self.start.diario_cc:
            if self.start.cat_diario_cc == 'Aviso Comun':
                return 'aviso_comun'
            elif self.start.cat_diario_cc == 'Aviso Especial':
                return 'aviso_especial'
            elif self.start.cat_diario_cc == 'Funebre':
                if(self.producto.producto.default_uom.symbol != 'cm'):
                    return 'funebre_comun'
                else:
                    return 'funebre_destacado'
            elif self.start.cat_diario_cc == 'Clasificado':
                if(self.producto.producto.default_uom.symbol != 'cm'):
                    return 'clasif_comun'
                else:
                    return 'clasif_destacado'
            elif self.start.cat_diario_cc == 'Edicto':
                return 'edicto'
            elif self.start.cat_diario_cc == 'Centimetros':
                return 'centimetros'
        if self.start.cat_radio_efec:
            return 'radio'
        if self.start_view.cat_digital_efec:
            return 'digital'



    def transition_terminar_aviso_comun(self):
        if self.aviso_comun.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.aviso_comun.cant_apariciones*Decimal(self.aviso_comun.apariciones)
            texto = self.aviso_comun.descripcion.encode('utf-8')

            #creacion linea de venta comentario (Texto del aviso)
            self.crear_linea_comentario_texto_aviso(venta,texto)
            
            precio_unitario=prod.list_price
            cant=self.aviso_comun.cant_centimetros * self.aviso_comun.cant_columnas
            fecha = self.aviso_comun.inicio
            ubicacion = self.aviso_comun.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
                pub.cm=Decimal(self.aviso_comun.cant_centimetros)
                pub.col=Decimal(self.aviso_comun.cant_columnas)
                if (self.aviso_comun.ubicacion == 'Libre'):
                    pass
                elif (self.aviso_comun.ubicacion == 'Suplemento'):
                    pub.nombre_sup=self.aviso_comun.suplemento
                elif (self.aviso_comun.ubicacion == 'Par'):
                    pub.nro_pag=self.aviso_comun.nro_pag
                    nueva.unit_price=nueva.product.template.list_price * Decimal('1.25')
                elif (self.aviso_comun.ubicacion == 'Impar'):
                    pub.nro_pag=self.aviso_comun.nro_pag
                    nueva.unit_price=nueva.product.template.list_price * Decimal('1.30')
                else:
                    nueva.unit_price=nueva.product.template.list_price * Decimal('1.50')
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.aviso_comun.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.aviso_comun.motivo
                if(self.aviso_comun.tipo_bonif=='p'):
                    porcent = (self.aviso_comun.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.aviso_comun.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_aviso_comun'


    def transition_terminar_fechas_aviso_comun(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_unitario=prod.list_price
        cant=self.aviso_comun.cant_centimetros * self.aviso_comun.cant_columnas
        ubicacion = self.aviso_comun.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_aviso_comun.fecha

        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_aviso_comun.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
        pub.cm=Decimal(self.aviso_comun.cant_centimetros)
        pub.col=Decimal(self.aviso_comun.cant_columnas)
        if (self.aviso_comun.ubicacion == 'Libre'):
            pass
        elif (self.aviso_comun.ubicacion == 'Suplemento'):
            pub.nombre_sup=self.aviso_comun.suplemento
        elif (self.aviso_comun.ubicacion == 'Par'):
            pub.nro_pag=self.aviso_comun.nro_pag
            nueva.unit_price=nueva.product.template.list_price * Decimal('1.25')
        elif (self.aviso_comun.ubicacion == 'Impar'):
            pub.nro_pag=self.aviso_comun.nro_pag
            nueva.unit_price=nueva.product.template.list_price * Decimal('1.30')
        else:
            nueva.unit_price=nueva.product.template.list_price * Decimal('1.50')
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()

        #creacion linea de venta final de bonificacion
        if self.fechas_aviso_comun.cant_apariciones==self.aviso_comun.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            texto = self.aviso_comun.descripcion.encode('utf-8')
            self.crear_linea_comentario_texto_aviso(venta,texto)
            if (self.aviso_comun.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.aviso_comun.motivo
                if(self.aviso_comun.tipo_bonif=='p'):
                    porcent = (self.aviso_comun.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.aviso_comun.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_aviso_comun'


    def transition_terminar_aviso_especial(self):
        if self.aviso_especial.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.aviso_especial.cant_apariciones*Decimal(self.aviso_especial.apariciones)
            texto = self.aviso_especial.descripcion.encode('utf-8')

            #creacion linea de venta comentario (Texto del aviso)
            self.crear_linea_comentario_texto_aviso(venta,texto)
            
            precio_unitario=prod.list_price
            #cant=self.aviso_especial.cant_centimetros * self.aviso_especial.cant_columnas
            fecha = self.aviso_especial.inicio
            ubicacion = self.aviso_especial.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,'1',pub)
                pub.unidad=1
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.aviso_especial.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.aviso_especial.motivo
                if(self.aviso_especial.tipo_bonif=='p'):
                    porcent = (self.aviso_especial.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.aviso_especial.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_aviso_especial'


    def transition_terminar_fechas_aviso_especial(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_unitario=prod.list_price
        ubicacion = self.aviso_especial.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_aviso_especial.fecha

        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_aviso_especial.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,'1',pub)
        pub.unidad=1
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()
        if self.fechas_aviso_especial.cant_apariciones==self.aviso_especial.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            texto = self.aviso_especial.descripcion.encode('utf-8')
            self.crear_linea_comentario_texto_aviso(venta,texto)
            #creacion linea de venta final de bonificacion
            if (self.aviso_especial.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.aviso_especial.motivo
                if(self.aviso_especial.tipo_bonif=='p'):
                    porcent = (self.aviso_especial.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.aviso_especial.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_aviso_especial'






    def transition_terminar_funebre_comun(self):
        if self.funebre_comun.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.funebre_comun.cant_apariciones*Decimal(self.funebre_comun.apariciones)
            texto = self.funebre_comun.descripcion.encode('utf-8')

            #creacion linea de venta comentario (Texto del aviso)
            self.crear_linea_comentario_texto_aviso(venta,texto)
            
            precio_unitario=prod.list_price
            fecha = self.funebre_comun.inicio
            ubicacion = self.funebre_comun.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,'1',pub)
                pub.unidad=1
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.funebre_comun.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.funebre_comun.motivo
                if(self.funebre_comun.tipo_bonif=='p'):
                    porcent = (self.funebre_comun.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.funebre_comun.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_funebre_comun'


    def transition_terminar_fechas_funebre_comun(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_unitario=prod.list_price
        ubicacion = self.funebre_comun.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_funebre_comun.fecha

        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_funebre_comun.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,'1',pub)
        pub.unidad=1
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()
        if self.fechas_funebre_comun.cant_apariciones==self.funebre_comun.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            texto = self.funebre_comun.descripcion.encode('utf-8')
            self.crear_linea_comentario_texto_aviso(venta,texto)
            #creacion linea de venta final de bonificacion
            if (self.funebre_comun.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.funebre_comun.motivo
                if(self.funebre_comun.tipo_bonif=='p'):
                    porcent = (self.funebre_comun.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.funebre_comun.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_funebre_comun'


    def transition_terminar_funebre_destacado(self):
        if self.funebre_destacado.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.funebre_destacado.cant_apariciones*Decimal(self.funebre_destacado.apariciones)
            texto = self.funebre_destacado.descripcion.encode('utf-8')

            #creacion linea de venta comentario (Texto del aviso)
            self.crear_linea_comentario_texto_aviso(venta,texto)
            
            precio_unitario=prod.list_price
            cant=self.funebre_destacado.cant_centimetros * self.funebre_destacado.cant_columnas
            fecha = self.funebre_destacado.inicio
            ubicacion = self.funebre_destacado.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
                pub.cm=Decimal(self.funebre_destacado.cant_centimetros)
                pub.col=Decimal(self.funebre_destacado.cant_columnas)
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.funebre_destacado.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.funebre_destacado.motivo
                if(self.funebre_destacado.tipo_bonif=='p'):
                    porcent = (self.funebre_destacado.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.funebre_destacado.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_funebre_destacado'

    def transition_terminar_fechas_funebre_destacado(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_unitario=prod.list_price
        cant=self.funebre_destacado.cant_centimetros * self.funebre_destacado.cant_columnas
        ubicacion = self.funebre_destacado.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_funebre_destacado.fecha

        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_funebre_destacado.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
        pub.cm=Decimal(self.funebre_destacado.cant_centimetros)
        pub.col=Decimal(self.funebre_destacado.cant_columnas)
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()

        #creacion linea de venta final de bonificacion
        if self.fechas_funebre_destacado.cant_apariciones==self.funebre_destacado.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            texto = self.funebre_destacado.descripcion.encode('utf-8')
            self.crear_linea_comentario_texto_aviso(venta,texto)
            if (self.funebre_destacado.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.funebre_destacado.motivo
                if(self.funebre_destacado.tipo_bonif=='p'):
                    porcent = (self.funebre_destacado.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.funebre_destacado.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_funebre_destacado'

    def transition_terminar_clasif_comun(self):
        if self.clasif_comun.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.clasif_comun.cant_apariciones*Decimal(self.clasif_comun.apariciones)
            texto = self.clasif_comun.descripcion.encode('utf-8')
            cant = 1
            index = 0
            for c in texto:
                index+=1
                if (index>35 or c=='\n'):
                    cant+=1
                    index=0
            #creacion linea de venta comentario (Texto del aviso)
            self.crear_linea_comentario_texto_aviso(venta,texto)
            
            precio_unitario=prod.list_price
            fecha = self.clasif_comun.inicio
            ubicacion = self.clasif_comun.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
                pub.lin=cant
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.clasif_comun.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.clasif_comun.motivo
                if(self.clasif_comun.tipo_bonif=='p'):
                    porcent = (self.clasif_comun.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.clasif_comun.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_clasif_comun'


    def transition_terminar_fechas_clasif_comun(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_unitario=prod.list_price
        ubicacion = self.clasif_comun.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_clasif_comun.fecha
        texto = self.clasif_comun.descripcion.encode('utf-8')
        cant = 1
        index = 0
        for c in texto:
            index+=1
            if (index>35 or c=='\n'):
                cant+=1
                index=0

        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_clasif_comun.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
        pub.lin=cant
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()
        if self.fechas_clasif_comun.cant_apariciones==self.clasif_comun.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            
            self.crear_linea_comentario_texto_aviso(venta,texto)
            #creacion linea de venta final de bonificacion
            if (self.clasif_comun.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.clasif_comun.motivo
                if(self.clasif_comun.tipo_bonif=='p'):
                    porcent = (self.clasif_comun.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.clasif_comun.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_clasif_comun'


    def transition_terminar_clasif_destacado(self):
        if self.clasif_destacado.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.clasif_destacado.cant_apariciones*Decimal(self.clasif_destacado.apariciones)
            texto = self.clasif_destacado.descripcion.encode('utf-8')

            #creacion linea de venta comentario (Texto del aviso)
            self.crear_linea_comentario_texto_aviso(venta,texto)
            
            precio_unitario=prod.list_price
            cant=self.clasif_destacado.cant_centimetros * self.clasif_destacado.cant_columnas
            fecha = self.clasif_destacado.inicio
            ubicacion = self.clasif_destacado.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
                pub.cm=Decimal(self.clasif_destacado.cant_centimetros)
                pub.col=Decimal(self.clasif_destacado.cant_columnas)
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.clasif_destacado.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.clasif_destacado.motivo
                if(self.clasif_destacado.tipo_bonif=='p'):
                    porcent = (self.clasif_destacado.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.clasif_destacado.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_clasif_destacado'



    def transition_terminar_fechas_clasif_destacado(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_unitario=prod.list_price
        cant=self.clasif_destacado.cant_centimetros * self.clasif_destacado.cant_columnas
        ubicacion = self.clasif_destacado.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_clasif_destacado.fecha

        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_clasif_destacado.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
        pub.cm=Decimal(self.clasif_destacado.cant_centimetros)
        pub.col=Decimal(self.clasif_destacado.cant_columnas)
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()

        #creacion linea de venta final de bonificacion
        if self.fechas_clasif_destacado.cant_apariciones==self.clasif_destacado.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            texto = self.clasif_destacado.descripcion.encode('utf-8')
            self.crear_linea_comentario_texto_aviso(venta,texto)
            if (self.clasif_destacado.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.clasif_destacado.motivo
                if(self.clasif_destacado.tipo_bonif=='p'):
                    porcent = (self.clasif_destacado.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.clasif_destacado.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_clasif_destacado'



    def transition_terminar_edicto(self):
        if self.edicto.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.edicto.cant_apariciones*Decimal(self.edicto.apariciones)
            texto = self.edicto.descripcion.encode('utf-8')
            cant = self.edicto.cant_lineas
            
            #creacion linea de venta comentario (Texto del aviso)
            self.crear_linea_comentario_texto_aviso(venta,texto)
            
            precio_unitario=prod.list_price
            fecha = self.edicto.inicio
            ubicacion = self.edicto.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
                pub.unidad=cant
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.edicto.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.edicto.motivo
                if(self.edicto.tipo_bonif=='p'):
                    porcent = (self.edicto.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.edicto.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_edicto'



    def transition_terminar_fechas_edicto(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_unitario=prod.list_price
        ubicacion = self.edicto.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_edicto.fecha
        texto = self.edicto.descripcion.encode('utf-8')
        cant = self.edicto.cant_lineas
        
        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_edicto.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
        pub.unidad=cant
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()
        if self.fechas_edicto.cant_apariciones==self.edicto.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            
            self.crear_linea_comentario_texto_aviso(venta,texto)
            #creacion linea de venta final de bonificacion
            if (self.edicto.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.edicto.motivo
                if(self.edicto.tipo_bonif=='p'):
                    porcent = (self.edicto.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.edicto.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_edicto'

    def transition_terminar_insert(self):
        if self.insert.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.insert.cant_apariciones*Decimal(self.insert.apariciones)

            impresion = '(Impresion propia: '
            if (self.insert.impresion == '0'):
                impresion = impresion + 'SI)'
            else:
                impresion = impresion + 'NO)'
            texto = impresion+'\n'+self.insert.descripcion.encode('utf-8')
            #creacion linea de venta comentario (Texto del aviso)
            self.crear_linea_comentario_texto_aviso(venta,texto)
            
            precio_unitario = self.insert.monto
            fecha = self.insert.inicio
            ubicacion = self.insert.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,'1',pub)
                pub.unidad=1
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.insert.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.insert.motivo
                if(self.insert.tipo_bonif=='p'):
                    porcent = (self.insert.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.insert.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_insert'


    def transition_terminar_fechas_insert(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_unitario = self.insert.monto
        ubicacion = self.insert.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_insert.fecha

        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_insert.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,'1',pub)
        pub.unidad=1
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()
        if self.fechas_insert.cant_apariciones==self.insert.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            impresion = '(Impresion propia: '
            if (self.insert.impresion == '0'):
                impresion = impresion + 'SI)'
            else:
                impresion = impresion + 'NO)'
            texto = impresion+'\n'+self.insert.descripcion.encode('utf-8')
            self.crear_linea_comentario_texto_aviso(venta,texto)
            #creacion linea de venta final de bonificacion
            if (self.insert.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.insert.motivo
                if(self.insert.tipo_bonif=='p'):
                    porcent = (self.insert.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.insert.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_insert'


    def transition_terminar_suplemento(self):
        if self.suplemento.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            if self.start.efectivo:
                term_pago = payment_term.search([('name','=','Efectivo')])[0]
                cliente = self.start.cliente_efec
            else:
                term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
                cliente = self.start.cliente_cc

            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.suplemento.cant_apariciones*Decimal(self.suplemento.apariciones)
            cant = self.suplemento.cant_paginas
            precio_edicion = str(self.suplemento.precio_edicion)
            precio_unitario = prod.list_price * Decimal(precio_edicion)
            fecha = self.suplemento.inicio
            ubicacion = self.suplemento.ubicacion
            origen = self.producto.origen

            #creacion de lineas de venta de producto y publicaciones presupuestadas
            for i in range(repeticion):
                pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
                nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
                pub.pag=cant
                pub.save()
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)

            #creacion linea de venta final de bonificacion
            if (self.suplemento.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.suplemento.motivo
                if(self.suplemento.tipo_bonif=='p'):
                    porcent = (self.suplemento.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.suplemento.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_suplemento'



    def transition_terminar_fechas_suplemento(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        precio_edicion = str(self.suplemento.precio_edicion)
        precio_unitario = prod.list_price * Decimal(precio_edicion)
        ubicacion = self.suplemento.ubicacion
        origen = self.producto.origen
        fecha = self.fechas_suplemento.fecha
        cant = self.suplemento.cant_paginas
        
        #creacion de lineas de venta de producto y publicaciones presupuestadas
        venta=self.fechas_suplemento.venta
        pub = self.crear_linea_publicacion_diario(ubicacion,fecha,origen)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cant,pub)
        pub.pag=cant
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()
        if self.fechas_suplemento.cant_apariciones==self.suplemento.cant_apariciones:
            #creacion linea de venta final de bonificacion
            if (self.suplemento.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.suplemento.motivo
                if(self.suplemento.tipo_bonif=='p'):
                    porcent = (self.suplemento.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.suplemento.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_suplemento'



    def transition_terminar_centimetros(self):
        payment_term = Pool().get('account.invoice.payment_term')
        sale = Pool().get('sale.sale')
        if self.start.efectivo:
            term_pago = payment_term.search([('name','=','Efectivo')])[0]
            cliente = self.start.cliente_efec
        else:
            term_pago = term_pago = payment_term.search([('name','=','Cuenta Corriente')])[0]
            cliente = self.start.cliente_cc

        #creacion de la venta
        venta = sale(self.crear_venta(term_pago,cliente))

        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        cantidad = Decimal(self.centimetros.cant_centimetros) * Decimal(self.centimetros.cant_columnas)
        precio_unitario = Decimal(self.centimetros.precio_cm)
        Date = Pool().get('ir.date')
        fecha = Date.today()
        pub = self.crear_linea_publicacion_diario_centimetros(fecha)
        nueva = self.crear_linea_producto_diario(venta,prod,precio_unitario,cantidad,pub)
        pub.cm=Decimal(self.centimetros.cant_centimetros)
        pub.col=Decimal(self.centimetros.cant_columnas)
        pub.save()
        nueva.description=pub.get_rec_name(None)
        nueva.save()
        return 'end'


    def transition_terminar_radio(self):
        if self.radio.apariciones!='1':
            payment_term = Pool().get('account.invoice.payment_term')
            sale = Pool().get('sale.sale')
            term_pago = payment_term.search([('name','=','Efectivo')])[0]
            cliente = self.start.cliente_efec
            #creacion de la venta
            venta = sale(self.crear_venta(term_pago,cliente))

            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            repeticion = self.radio.cant_apariciones*Decimal(self.radio.apariciones)
            horario = self.radio.horario_programacion
            texto = self.radio.mencion.encode('utf-8')
            if prod.name=='Columnistas':
                precio = Decimal(self.radio.precio_mencion)
                menciones = Decimal(self.cantidad_menciones)
                precio_unitario = precio * menciones
            else:
                precio_unitario = prod.list_price
            nueva = 0
            fecha = self.radio.inicio
            self.crear_linea_comentario_texto_aviso(venta,texto)
            for i in range(repeticion):
                if horario != 'Manual':
                    pub = self.crear_linea_publicacion_radio(fecha,horario,None,None)
                else:
                    pub = self.crear_linea_publicacion_radio(fecha,horario,self.radio.desde,self.radio.hasta)
                nueva = self.crear_linea_producto_radio(venta,prod,precio_unitario,pub)
                nueva.description=pub.get_rec_name(None)
                nueva.save()
                fecha = fecha +timedelta(days=1)
            #creacion linea de venta final de bonificacion
            if (self.radio.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.radio.motivo
                if(self.radio.tipo_bonif=='p'):
                    porcent = (self.radio.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.radio.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_radio'

    def transition_terminar_fechas_radio(self):
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        horario = self.radio.horario_programacion
        texto = self.radio.mencion.encode('utf-8')
        precio_unitario = prod.list_price
        fecha = self.fechas_radio.fecha
        venta = self.fechas_radio.venta
        if horario != 'Manual':
            pub = self.crear_linea_publicacion_radio(fecha,horario,None,None)
        else:
            pub = self.crear_linea_publicacion_radio(fecha,horario,self.radio.desde,self.radio.hasta)
        nueva = self.crear_linea_producto_radio(venta,prod,precio_unitario,pub)
        nueva.description=pub.get_rec_name(None)
        nueva.save()
        if self.fechas_radio.cant_apariciones==self.radio.cant_apariciones:
            #creacion linea de venta comentario (Texto del aviso)
            texto = self.radio.mencion.encode('utf-8')
            self.crear_linea_comentario_texto_aviso(venta,texto)
            #se calcula el precio
            if (self.radio.bonificacion):
                prod_bonif = productos(productos.search([('name', '=', 'Bonificacion')])[0])
                monto = 0
                motivo = self.radio.motivo
                if(self.radio.tipo_bonif=='p'):
                    porcent = (self.radio.valor)/Decimal('100')
                    monto = Decimal('-1')*(Decimal(venta.total_amount) * Decimal(porcent))
                else:
                    monto = Decimal('-1')*self.radio.valor
                self.crear_linea_bonificacion(venta,prod_bonif,monto,motivo)
            return 'end'
        else:
            return 'fechas_radio'


    def transition_terminar_digital(self):
        payment_term = Pool().get('account.invoice.payment_term')
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        sale = Pool().get('sale.sale')
        term_pago = payment_term.search([('name','=','Efectivo')])[0]
        cliente = self.start.cliente_efec
        #creacion de la venta
        venta = sale(self.crear_venta(term_pago,cliente))
        fecha = self.digital.inicio
        meses = Decimal(self.digital.cant_meses)
        nueva = 0
        for i in range(meses):
            precio_unitario = prod.list_price
            if(self.digital.expandible):
                pub = self.crear_linea_publicacion_digital(fecha,True,self.digital.a,self.digital.recargo)
                porcent = Decimal(1+(Decimal(self.digital.recargo)/Decimal('100')))
                precio_unitario = (Decimal(precio_unitario) * Decimal(porcent))
            else:
                pub = self.crear_linea_publicacion_digital(fecha,False,None,None)
            nueva = self.crear_linea_producto_digital(venta,prod,precio_unitario,pub)
            nueva.description=pub.get_rec_name(None)
            nueva.save()
            fecha += relativedelta(months=+1)
        #se calcula el precio
        cant = Decimal(nueva.quantity) * meses
        precio = cant * Decimal(nueva.unit_price)

        #bonificacion
        if (self.digital.bonificacion):
            pr = productos(productos.search([('name', '=', 'Bonificacion')])[0])
            monto = 0
            motivo = self.digital.motivo.encode('utf-8')
            if(self.digital.tipo_bonif=='p'):
                porcent = (self.digital.valor)/Decimal('100')
                monto = Decimal('-1')*(Decimal(precio) * Decimal(porcent))
            else:
                monto = Decimal('-1')*self.digital.valor
            self.crear_linea_bonificacion(pr,monto,motivo)
        return 'end'


