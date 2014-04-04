from trytond.pool import Pool
from trytond.pyson import Eval, Or, Bool, Equal, Not, And
from trytond.model import ModelSQL, ModelView, Workflow, fields
from trytond.wizard import Wizard, StateView, StateTransition, Button, StateAction
from decimal import Decimal
from datetime import timedelta
import datetime
from trytond.transaction import Transaction


tyc_cat_diario =[
                    ('Aviso Comun', '1- Aviso Comun'),
                    ('Aviso Especial', '2- Aviso Especial'),
                    ('Clasificado', '3- Clasificado Destacado'),
                    ('Funebre', '4- Funebre Destacado'),
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

lista_origen = [
                ('Ninguno','Ninguno'),
                ('Composicion','Composicion'),
                ('E-mail','E-mail'),
                ('Scanner','Scanner'),
                ('Sigue','Sigue'),
                ('Sin cargo','Sin cargo'),
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

horarios= [
                ('Rotativas', '1- Rotativas'),
                ('c/30 minutos', '2- c/30 minutos'),
                ('Cierre de la Programacion', '3- Cierre de la Programacion'),
                ('Programas Centrales', '4- Programas Centrales'),
                ('Manual', '5- Horario'),
          ]

class Edicion(ModelSQL,ModelView):
    'Edicion'
    __name__ = 'edicion.edicion'
    _rec_name = 'fecha'
    fecha = fields.Date('FECHA', readonly=False, required=True)
    publicacionesDiario = fields.One2Many('edicion.publicacion_diario', 'edicion', 'DIARIO')
    publicacionesRadio = fields.One2Many('edicion.publicacion_radio', 'edicion','RADIO')
    publicacionesDigital = fields.Many2Many('edicion.edicion_publicacion_digital', 'edicion_id', 'digital_id','DIGITAL')

    @classmethod
    def __setup__(cls):
        super(Edicion, cls).__setup__()
        cls._sql_constraints = [
            ('edicion_fecha', 'UNIQUE(fecha)',
                'no se pueden crear 2 ediciones con la misma fecha'),
            ]

    def get_rec_name(self, name):
        return self.fecha.strftime('%d/%m/%Y')

class EdicionPublicacionDigital(ModelSQL):
    'EdicionPublicacionDigital'
    __name__ = 'edicion.edicion_publicacion_digital'

    edicion_id = fields.Many2One('edicion.edicion', 'Edicion')
    digital_id = fields.Many2One('edicion.publicacion_digital', 'Digital')




#PUBLICACIONES
class PublicacionDiario(Workflow,ModelSQL,ModelView):
    'PublicacionDiario'
    __name__ = 'edicion.publicacion_diario'
    termino_pago = fields.Many2One('account.invoice.payment_term','TERMINO PAGO')
    fecha = fields.Function (fields.Date('FECHA'), 'get_fecha')
    linea = fields.Many2One('sale.line', 'LINEA', ondelete='CASCADE')
    cliente = fields.Many2One('party.party', 'CLIENTE',
        states={'readonly': Or(Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),(Eval('state') == 'reprogramar')),Equal(Eval('venta_cm'),'si'))},
                 depends=['state'], required=True)
    categoria = fields.Function(fields.Many2One('product.category', 'CATEGORIA'), 'get_categoria')
    producto = fields.Many2One('product.product', 'PRODUCTO',domain=[('category.parent', '=', 'Diario')],
        states={'readonly': Or(Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),(Eval('state') == 'reprogramar')),Equal(Eval('venta_cm'),'si'))}, depends=['state'], required=True)
    edicion = fields.Many2One('edicion.edicion', 'EDICION',
    states={'readonly': Or(Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada')),Equal(Eval('venta_cm'),'si')),
            'required':And(Equal(Eval('venta_cm'),'no'),(Eval('state') != 'cancelada'))},depends=['state'])
    descrip = fields.Text('DESCRIPCION', depends=['state'],
        states={'readonly': Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),(Eval('state') == 'reprogramar'))})
    state = fields.Selection([  ('reprogramar','reprogramar'),
                                ('pendiente','pendiente'),
                                ('publicada','publicada'),
                                ('cancelada','cancelada')],'State', readonly=True, required=True)
    venta_cm = fields.Char('VENTA POR CM',size = 2,readonly=True)
    viene_de_cm = fields.Boolean("CM")
    
    cm = fields.Numeric('Cant. Cms',states={'readonly': Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),And((Eval('state') == 'reprogramar'),Equal(Eval('venta_cm'),'no')))}, depends=['state'])
    col = fields.Numeric('Cant. Columnas',states={'readonly': Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),And((Eval('state') == 'reprogramar'),Equal(Eval('venta_cm'),'no')))}, depends=['state'])
    lin = fields.Numeric('Cant. Lineas',states={'readonly': Or(Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),(Eval('state') == 'reprogramar')),Equal(Eval('venta_cm'),'si'))}, depends=['state'])
    pag = fields.Numeric('Cant. Pag.',states={'readonly': Or(Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),(Eval('state') == 'reprogramar')),Equal(Eval('venta_cm'),'si'))}, depends=['state'])
    unidad = fields.Numeric('Unidades',states={'readonly': Or(Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),(Eval('state') == 'reprogramar')),Equal(Eval('venta_cm'),'si'))}, depends=['state'])

    ubicacion = fields.Selection(aviso_ubicacion,'Ubicacion',
                                states={'readonly': Or(Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),(Eval('state') == 'reprogramar')),Equal(Eval('venta_cm'),'si'))}, depends=['state'], required=True)
    nro_pag = fields.Char('Nro. Pag.',states={'readonly':And(Not(Equal(Eval('ubicacion'),'Par')),Not(Equal(Eval('ubicacion'),'Impar')))})
    nombre_sup = fields.Char('Nombre Suplemento', states={'readonly':Not(Equal(Eval('ubicacion'),'Suplemento'))})

    origen = fields.Selection(lista_origen,'Origen', states={'readonly': Or(Or((Or((Eval('state') == 'cancelada'),(Eval('state') == 'publicada'))),(Eval('state') == 'reprogramar')),Equal(Eval('venta_cm'),'si'))}, depends=['state'],required=True)
    en_guia = fields.Boolean('IMPRESO EN GUIA ANTERIOR', select=False)
    impresion = fields.Selection([  ('pendiente','Pendiente'),
                                    ('imprimiendo','Imprimiendo'),
                                    ('impreso','Impreso')], 'Esta Impreso', on_change_with=['en_guia'])

    @staticmethod
    def default_ubicacion():
        return 'Libre'

    @classmethod
    def default_state(self):
        return 'pendiente'

    @classmethod
    def default_venta_cm(self):
        return 'no'

    @classmethod
    def default_origen(self):
        return 'Ninguno'
    
    @classmethod
    def default_impresion(self):
        return 'pendiente'

    def on_change_with_impresion(self):
        if self.en_guia:
            return 'impreso'
        else:
            return 'pendiente'


    @classmethod
    def __setup__(cls):
        super(PublicacionDiario, cls).__setup__()
        cls._transitions |= set((
                ('reprogramar', 'pendiente'),
                ('reprogramar', 'cancelada'),
                ('pendiente', 'reprogramar'),
                ('pendiente', 'publicada'),
                ('pendiente', 'cancelada'),
                ))
        cls._buttons.update({
                'reprogramar': {
                    'invisible': Or(Eval('state').in_(['reprogramar','publicada', 'cancelada']),Equal(Eval('venta_cm'),'si')),
                    'icon': 'tryton-clear',
                    },
                'pendiente': {
                    'invisible': Or(~Eval('state').in_(['reprogramar']),Equal(Eval('venta_cm'),'si')),
                    'icon': 'tryton-go-next',
                    },
                'publicada': {
                    'invisible': Or(Eval('state') != 'pendiente',Equal(Eval('venta_cm'),'si')),
                    'icon': 'tryton-ok',
                    },
                'cancelada': {
                    'invisible': Or(Eval('state').in_(['publicada', 'cancelada']),Equal(Eval('venta_cm'),'si')),
                    'icon': 'tryton-cancel',
                    },
                'presupuestar': {
                    'invisible': Equal(Eval('venta_cm'),'no'),
                    'icon': 'tryton-ok',
                    },
                })

        cls._error_messages.update({
            'error_fecha' : 'La fecha es invalida'
            })

    @classmethod
    @ModelView.button
    @Workflow.transition('reprogramar')
    def reprogramar(cls, publ):
        pass


    @classmethod
    @ModelView.button
    @Workflow.transition('pendiente')
    def pendiente(cls, publ):
        date = Pool().get('ir.date')
        for p in publ:
            if (p.edicion.fecha<=date.today()):
                cls.raise_user_error('error_fecha')
            else:
                pass

    @classmethod
    def crear_factura(cls,publ):
        date = Pool().get('ir.date')
        Sale = Pool().get('sale.sale')
        InvoiceLine = Pool().get('account.invoice.line')
        Tax = Pool().get('account.invoice.line-account.tax')
        factura = None
        bonif_ya_cargada = False
        sale = publ.linea.sale
        for f in sale.invoices:
            bonif_ya_cargada = True
            if f.state != 'paid' and f.state != 'cancel':
                factura = f
                break
        if factura == None:
            Invoice = Pool().get('account.invoice')
            Journal = Pool().get('account.journal')
            SaleInvoice = Pool().get('sale.sale-account.invoice')


            #creo factura nueva y guardo en factura
            if (sale.party.facturacion =='a'):
                es_a = True
            else:
                es_a = False
            factura = sale._get_invoice_sale('out_invoice')
            factura.es_a=es_a
            factura.save()
            
            #la asocio a la venta
            relacion = SaleInvoice.create ([{  'sale' : sale,
                                                'invoice' : factura,
                                            }])[0]
            relacion.save()
            text = ''
            for line in sale.lines:
                if line.type == 'comment':
                    text= line.description
                    break
            comment = InvoiceLine.create([{ 'type' : 'comment',
                                            'description' : text, 
                                            'invoice' : factura,
                                            }])[0]
            comment.save()
            if not bonif_ya_cargada:
                b = 0
                for line in sale.lines:
                    if line.type == 'line':
                        if line.product.name == 'Bonificacion':
                            b= line
                            break
            #busco si tiene bonificacion, creo la linea y se la pongo a la factura
                if(b!=0):
                    bonif = InvoiceLine.create([{   'type' : 'line',
                                                    'invoice' : factura.id,
                                                    'product': b.product.id,
                                                    'description':b.description,
                                                    'account':b.product.account_revenue_used,
                                                    'sequence':'0',
                                                    'unit': b.unit,
                                                    'unit_price':b.unit_price,
                                                    'quantity':1,
                                                }])[0]
                    bonif.save()
        #creo la nueva linea y se la pongo a la factura
        nueva = InvoiceLine.create([{   'type' : 'line',
                                        'invoice' : factura,
                                        'product': publ.linea.product,
                                        'description':publ.linea.description,
                                        'account':publ.linea.product.account_revenue_used,
                                        'sequence':'0',
                                        'unit': publ.linea.unit,
                                        'unit_price':publ.linea.unit_price,
                                        'quantity':publ.linea.quantity,
                                    }])[0]
        nueva.save()
        try:
            impuestos_prod = publ.linea.product.category.parent.customer_taxes
            for impuesto_cliente in impuestos_prod:
                impuesto_linea = Tax.create([{
                    'line' : InvoiceLine(nueva),
                    'tax' : impuesto_cliente
                    }])[0]
                impuesto_linea.save()
        except:
            pass



    @classmethod
    @ModelView.button
    @Workflow.transition('publicada')
    def publicada(cls, publ):
        for p in publ:
            if(p.linea != None):
                if(p.viene_de_cm):
                    linea = Pool().get('sale.line')
                    cantidad=0
                    if(p.producto.default_uom.symbol=='cm'):
                        cantidad = p.cm * p.col
                    elif(p.producto.default_uom.symbol=='lin'):
                        cantidad = p.lin
                    elif(p.producto.default_uom.symbol=='pag'):
                        cantidad = p.pag
                    elif(p.producto.default_uom.symbol=='u'):
                        cantidad = p.unidad
                    nueva_linea = linea.create([{
                                'sale':p.linea.sale,
                                'product': p.producto,
                                'sequence':'0',
                                'type':'line',
                                'unit': p.producto.default_uom,
                                'unit_price':0,
                                'quantity':cantidad,
                                'description':'Aviso de cuenta corriente de centimetros\n TEXTO DEL AVISO:\n'+str(p.descrip)
                                }])[0]
                    nueva_linea.save()

                    p.linea = nueva_linea
                    p.linea.save()
                elif(p.termino_pago.name == 'Cuenta Corriente'):
                    cls.crear_factura(p)
                else:
                    pass
            else:
                pass

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelada')
    def cancelada(cls, publ):
        line = Pool().get('sale.line')
        for p in publ:
            try:
                linea = p.linea
                p.linea=None
                p.edicion=None
                p.save()
                line.delete([linea])
            except:
                pass

    @classmethod
    @ModelView.button_action('edicion.presupuestacion_centimetros')
    def presupuestar(cls, publ):
        pass

    def get_fecha(self, name):
        if self.edicion !=None:
            return self.edicion.fecha
        else:
            return None

    def get_categoria(self, name):
        return self.producto.category.id

class PublicacionRadio(ModelSQL,ModelView):
    'PublicacionRadio'
    __name__ = 'edicion.publicacion_radio'
    fecha = fields.Function (fields.Date('FECHA'), 'get_fecha')
    linea = fields.Many2One('sale.line', 'LINEA', ondelete='CASCADE')
    cliente = fields.Many2One('party.party', 'CLIENTE', required=True)
    categoria = fields.Selection([('Costo Provincial','1- Costo Provincial'),('Costo Nacional','2- Costo Nacional'),('Costo Oficial','3- Costo Oficial')],'CATEGORIA',required=True)
    producto = fields.Many2One('product.product', 'PRODUCTO',domain=[('category', '=', Eval('categoria')),('category.parent','=','Radio')], required=True)
    edicion = fields.Many2One('edicion.edicion', 'EDICION', required = True)
    descrip = fields.Text('DESCRIPCION')
    horario_programacion = fields.Selection(horarios, 'HS. PROGRAMACION', required=True)
    desde = fields.Char("DE", states={'readonly': (Eval('horario_programacion') != 'Manual'),
                                    'required': (Eval('horario_programacion') == 'Manual'),
                                    })
    hasta = fields.Char("A", states={'readonly': (Eval('horario_programacion') != 'Manual'),
                                    'required': (Eval('horario_programacion') == 'Manual'),
                                    })
    def get_fecha(self, name):
        return self.edicion.fecha

    @staticmethod
    def default_horario_programacion():
        return 'Rotativas'

class PublicacionDigital(ModelSQL,ModelView):
    'PublicacionDigital'
    __name__ = 'edicion.publicacion_digital'
    fecha = fields.Function (fields.Date('FECHA INICIO'), 'get_fecha')
    linea = fields.Many2One('sale.line', 'LINEA', ondelete='CASCADE')
    cliente = fields.Many2One('party.party', 'CLIENTE', required=True)
    categoria = fields.Selection([('Costo Provincial','1- Costo Provincial'),('Costo Nacional','2- Costo Nacional'),('Costo Oficial','3- Costo Oficial')],'CATEGORIA',required=True)
    producto = fields.Many2One('product.product', 'PRODUCTO',domain=[('category', '=', Eval('categoria')),('category.parent','=','Digital')], required=True)
    edicion = fields.Many2Many('edicion.edicion_publicacion_digital','digital_id','edicion_id','EDICION')
    descrip = fields.Text('DESCRIPCION')
    expandible = fields.Boolean('expandible',select=False)
    a = fields.Char("A",states={'readonly': (Bool(Eval('expandible')) == False),
                                'required': (Bool(Eval('expandible')) == True),
                                })

    def get_fecha(self, name):
        try:
            fecha_inicio = self.edicion[0].fecha
            return fecha_inicio
        except:
            return None



#PUBLICACIONES PRESUPUESTADAS
class PublicacionPresupuestadaDiario(ModelSQL,ModelView):
    'PublicacionPresupuestadaDiario'
    __name__ = 'edicion.publicacion_presupuestada_diario'
    fecha = fields.Date('Aparicion',states={'required':Eval('categoria_producto')!='Centimetros',
                                             'readonly':Eval('categoria_producto')=='Centimetros',
                                            }, 
                                            )
    linea = fields.One2One('edicion.publicacion_presupuestada_diario_linea', 'pub_presup_diario_id', 'linea_id', 'Linea')
    cm = fields.Numeric('Cant. Cms')
    col = fields.Numeric('Cant. Columnas')
    lin = fields.Numeric('Cant. Lineas')
    pag = fields.Numeric('Cant. Pag.')
    unidad = fields.Numeric('Unidades')
    origen = fields.Selection(lista_origen,'Origen', states={'required':Eval('categoria_producto')!='Centimetros',
                                                             'readonly':Eval('categoria_producto')=='Centimetros',
                                                            },
                                                            )

    ubicacion = fields.Selection(aviso_ubicacion,'Ubicacion',states={'readonly': Not(Equal(Eval('categoria_producto'),'Aviso Comun'))})
    nro_pag = fields.Char('Nro. Pag.',states={'readonly':And(Not(Equal(Eval('ubicacion'),'Par')),Not(Equal(Eval('ubicacion'),'Impar')))})
    nombre_sup = fields.Char('Nombre Suplemento', states={'readonly':Not(Equal(Eval('ubicacion'),'Suplemento'))})
    categoria_producto = fields.Function(fields.Char('Categoria Producto'),'get_categoria_producto')
    venta_cm = fields.Char('VENTA POR CM',size = 2,readonly=True)

    def get_categoria_producto(self,name):
        if (self.linea):
            Line = Pool().get('sale.line')
            mi_linea = Line(self.linea)
            return mi_linea.product.template.category.name
        else:
            return " "
        

    @staticmethod
    def default_ubicacion():
        return 'Libre'


    def get_rec_name(self, name):
        try:
            nombre='aparicion '+'['+self.fecha.strftime('%d/%m/%Y')+']'
            if(self.linea):
                if (self.linea.product.default_uom.symbol=='cm'):
                    nombre+=' - medida '+'['+str(self.cm)+'x'+str(self.col)+' cms.]'
                elif(self.linea.product.default_uom.symbol=='lin'):
                    nombre+=' - medida '+'['+str(self.lin)+' linea/s]'
                elif (self.linea.product.default_uom.symbol=='pag'):
                    nombre+=' - medida '+'['+str(self.pag)+' pagina/s]'
                elif (self.linea.product.default_uom.symbol=='u'):
                    nombre+=' - medida '+'['+str(self.unidad)+' unidad/es]'
            nombre+=' - ubicacion '+'['+self.ubicacion+']'
        except:
            nombre=" "
        return nombre

class PublicacionPresupuestadaDiarioLinea(ModelSQL):
    'PublicacionPresupuestadaDiarioLinea'
    __name__ = 'edicion.publicacion_presupuestada_diario_linea'
    linea_id = fields.Many2One('sale.line', 'LINEA', ondelete='CASCADE')
    pub_presup_diario_id = fields.Many2One('edicion.publicacion_presupuestada_diario',"Presupuestada Diario",ondelete='CASCADE')


class PublicacionPresupuestadaRadio(ModelSQL,ModelView):
    'PublicacionPresupuestadaRadio'
    __name__ = 'edicion.publicacion_presupuestada_radio'
    fecha = fields.Date('FECHA')
    linea = fields.One2One('edicion.publicacion_presupuestada_radio_linea', 'pub_presup_radio_id', 'linea_id', 'Linea')
    horario_programacion = fields.Selection(horarios, 'HS. PROGRAMACION', required=True)
    desde = fields.Char("DE", states={'readonly': (Eval('horario_programacion') != 'Manual'),
                                    'required': (Eval('horario_programacion') == 'Manual'),
                                    })
    hasta = fields.Char("A", states={'readonly': (Eval('horario_programacion') != 'Manual'),
                                    'required': (Eval('horario_programacion') == 'Manual'),
                                    })
    descrip = fields.Text('DESCRIPCION', required=False)

    @staticmethod
    def default_horario_programacion():
        return 'Rotativas'

    def get_rec_name(self, name):
        try:
            nombre='aparicion '+'['+self.fecha.strftime('%d/%m/%Y')+']'
        except:
            nombre=" "
        try:
            nombre+=' - '+self.horario_programacion
        except:
            nombre+=""
        return nombre

class PublicacionPresupuestadaRadioLinea(ModelSQL):
    'PublicacionPresupuestadaRadioLinea'
    __name__ = 'edicion.publicacion_presupuestada_radio_linea'
    linea_id = fields.Many2One('sale.line', 'LINEA', ondelete='CASCADE')
    pub_presup_radio_id = fields.Many2One('edicion.publicacion_presupuestada_radio',"Presupuestada Radio",ondelete='CASCADE')

class PublicacionPresupuestadaDigital(ModelSQL,ModelView):
    'PublicacionPresupuestadaDigital'
    __name__ = 'edicion.publicacion_presupuestada_digital'
    fecha = fields.Date('FECHA')
    # cliente = fields.Many2One('party.party', 'CLIENTE', required=True)
    # venta = fields.Many2One('sale.sale', 'VENTA', required=True)
    linea = fields.One2One('edicion.publicacion_presupuestada_digital_linea', 'pub_presup_digital_id', 'linea_id', 'Linea')
    # producto = fields.Many2One('product.product', 'PRODUCTO', required=True)
    descrip = fields.Text('DESCRIPCION', required=False)
    expandible = fields.Boolean('expandible',select=False)
    a = fields.Char("A",states={'readonly': (Bool(Eval('expandible')) == False),
                                'required': (Bool(Eval('expandible')) == True),
                                })
    recargo = fields.Numeric('RECARGO', states={'readonly': (Bool(Eval('expandible')) == False),
                                                'required': (Bool(Eval('expandible')) == True),
                                                })

    def get_rec_name(self, name):
        try:
            nombre='aparicion '+'['+self.fecha.strftime('%d/%m/%Y')+']'
        except:
            nombre=" "
        try:
            if self.expandible:
                nombre+=' - expandible a '+str(self.a) + ' con un recargo del '+ str(self.recargo) + '%'
        except:
            pass
        return nombre

class PublicacionPresupuestadaDigitalLinea(ModelSQL):
    'PublicacionPresupuestadaDigitalLinea'
    __name__ = 'edicion.publicacion_presupuestada_digital_linea'
    linea_id = fields.Many2One('sale.line', 'LINEA', ondelete='CASCADE')
    pub_presup_digital_id = fields.Many2One('edicion.publicacion_presupuestada_digital',"Presupuestada Digital",ondelete='CASCADE')

class TipoYCategoria(ModelSQL,ModelView):
    'Tipo y Categoria'
    __name__ = 'edicion.tipo_y_categoria.start'
    diario = fields.Char('DIARIO',readonly=True)
    categoriaDiario = fields.Selection(tyc_cat_diario, 'CATEGORIA',required=True)

    @staticmethod
    def default_diario():
        return 'DIARIO'

#PRESUPUESTADOR O ASISTENTE PARA LA VENTA DE CMS DE CC


class Producto(ModelSQL,ModelView):
    'Producto'
    __name__ = 'edicion.producto'
    cat = fields.Char('Categoria Seleccionada', readonly=True)
    producto = fields.Many2One('product.template', 'Producto',domain=[('category', '=', Eval('cat'))], required=True)
    origen = fields.Selection(lista_origen,'Origen', states={'required':Eval('cat')!='Centimetros',
                                                             'readonly':Eval('cat')=='Centimetros',
                                                            }
                                                            )

    @staticmethod
    def default_origen():
        return 'Ninguno'


class AvisoComun(ModelSQL,ModelView):
    'AvisoComun'
    __name__ = 'edicion.aviso_comun'
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
    __name__ = 'edicion.aviso_especial'
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



class FunebreDestacado(ModelSQL,ModelView):
    'FunebreDestacado'
    __name__ = 'edicion.funebre_destacado'
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


class ClasificadoDestacado(ModelSQL,ModelView):
    'ClasificadoDestacado'
    __name__ = 'edicion.clasificado_destacado'
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


class SeleccionFechas(ModelSQL,ModelView):
    'SeleccionFechas'
    __name__ = 'edicion.seleccion_fechas'
    cant_apariciones = fields.Numeric('Cantidad de apariciones ya seleccionadas', readonly=True)
    fecha = fields.Date('Fecha de la aparicion', required=True)
    venta = fields.Many2One('sale.sale','Venta')


class PresupuestacionCentimetros(Wizard):
    'PresupuestacionCentimetros'
    __name__ = 'edicion.presupuestacion_centimetros'

    #-----------------------------------------INICIO-----------------------------------------#
    start = StateView('edicion.tipo_y_categoria.start',
                      'edicion.tipo_y_categoria_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Siguiente', 'eleccion_producto', 'tryton-go-next', default=True)])

    ##-----------------------------------------PRODUCTO-----------------------------------------#
    producto = StateView('edicion.producto',
                      'edicion.producto_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'volver_start', 'tryton-go-previous'),
                      Button('Siguiente', 'datos_categoria', 'tryton-go-next', default=True)])

    #-----------------------------------------DIARIO-----------------------------------------#
    aviso_comun = StateView('edicion.aviso_comun',
                      'edicion.aviso_comun_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_aviso_comun', 'tryton-go-next', default=True)])

    aviso_especial = StateView('edicion.aviso_especial',
                      'edicion.aviso_especial_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_aviso_especial', 'tryton-go-next', default=True)])

    funebre_destacado = StateView('edicion.funebre_destacado',
                      'edicion.funebre_destacado_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_funebre_destacado', 'tryton-go-next', default=True)])

    clasif_destacado = StateView('edicion.clasificado_destacado',
                      'edicion.clasificado_destacado_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('Atras', 'eleccion_producto', 'tryton-go-previous'),
                      Button('Siguiente', 'terminar_clasif_destacado', 'tryton-go-next', default=True)])

    fechas_aviso_comun = StateView('edicion.seleccion_fechas',
                      'edicion.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_aviso_comun', 'tryton-go-next', default=True)])

    fechas_aviso_especial = StateView('edicion.seleccion_fechas',
                      'edicion.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_aviso_especial', 'tryton-go-next', default=True)])

    fechas_funebre_destacado = StateView('edicion.seleccion_fechas',
                      'edicion.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_funebre_destacado', 'tryton-go-next', default=True)])

    fechas_clasif_destacado = StateView('edicion.seleccion_fechas',
                      'edicion.seleccion_fechas_form',
                      [Button('Siguiente', 'terminar_fechas_clasif_destacado', 'tryton-go-next', default=True)])



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
    terminar_funebre_destacado = StateTransition()
    terminar_fechas_funebre_destacado = StateTransition()
    #--------------------------------------------------
    terminar_clasif_destacado = StateTransition()
    terminar_fechas_clasif_destacado = StateTransition()
    #--------------------------------------------------



    def crear_linea_publicacion_diario(self,producto,ubicacion,fecha,origen,texto):
        edicion = Pool().get('edicion.edicion')
        publicacion = Pool().get('edicion.publicacion_diario')
        try:
            edic= edicion(edicion.search([('fecha', '=', fecha)])[0])
        except:
            edic=edicion.create([{
            'fecha':fecha
            }])[0]
            edic.save()
        pub = publicacion.create([{
            'termino_pago':publicacion(Transaction().context.get('active_id')).termino_pago,
            'linea':publicacion(Transaction().context.get('active_id')).linea,
            'cliente':publicacion(Transaction().context.get('active_id')).cliente,
            'producto' : producto,
            'descrip' : texto,
            'origen':origen,
            'ubicacion': ubicacion,
            'edicion' : edic,
            'viene_de_cm' : True,
            }])[0]
        pub.save()
        return pub


    #valores por defecto de los estados de vista
    def default_producto(self,fields):
        default = {}
        default['cat']=str('Diario') + ' / ' + str(self.start.categoriaDiario)
        return default

    def default_aviso_comun(self,fields):
        default = {}
        default['cant_centimetros']=3
        default['cant_columnas']=1
        default['apariciones']='1'
        default['cant_apariciones']=1
        return default

    def default_aviso_especial(self,fields):
        default = {}
        cm=str(self.producto.producto.name).split('x')[-1]
        col=(str(self.producto.producto.name).split('x')[0]).split(' ')[-1]
        default['cant_centimetros']=cm
        default['cant_columnas']=col
        default['apariciones']='1'
        default['cant_apariciones']=1
        return default

    def default_funebre_destacado(self,fields):
        default = {}
        default['cant_centimetros']=3
        default['cant_columnas']=1
        default['apariciones']='1'
        default['cant_apariciones']=1
        return default

    def default_clasif_destacado(self,fields):
        default = {}
        default['tipo']=self.producto.producto.name.split(' ')[0]
        default['cant_centimetros']=3
        default['cant_columnas']=1
        default['apariciones']='1'
        default['cant_apariciones']=1
        return default

    def default_fechas_aviso_comun(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_aviso_comun.cant_apariciones) +1
        except:
            default['cant_apariciones']=1
        return default

    def default_fechas_aviso_especial(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_aviso_especial.cant_apariciones) +1
        except:
            default['cant_apariciones']=1
        return default

    def default_fechas_funebre_destacado(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_funebre_destacado.cant_apariciones) +1
        except:
            default['cant_apariciones']=1
        return default

    def default_fechas_clasif_destacado(self,fields):
        default = {}
        try:
            default['cant_apariciones']=Decimal(self.fechas_clasif_destacado.cant_apariciones) +1
        except:
            default['cant_apariciones']=1
        return default


    @classmethod
    def __setup__(cls):
        super(PresupuestacionCentimetros, cls).__setup__()

        cls._error_messages.update({
            'error_centimetros': 'Insuficiente cantidad de centimetros para el aviso',
            'error_producto' : 'Producto no corresponde a cuenta corriente de centimetros',
            })


    def transition_volver_start(self):
        return 'start'

    def transition_eleccion_producto(self):
        return 'producto'

    def transition_datos_categoria(self):
        if self.start.diario:
            if(self.start.categoriaDiario == 'Aviso Comun'):
                return 'aviso_comun'
            elif(self.start.categoriaDiario == 'Aviso Especial'):
                return 'aviso_especial'
            elif(self.start.categoriaDiario == 'Funebre'):
                if(self.producto.producto.default_uom.symbol != 'cm'):
                    self.raise_user_error('error_producto')
                else:
                    return 'funebre_destacado'
            elif(self.start.categoriaDiario == 'Clasificado'):
                if(self.producto.producto.default_uom.symbol != 'cm'):
                    self.raise_user_error('error_producto')
                else:
                    return 'clasif_destacado'

    def transition_terminar_aviso_comun(self):
        if self.aviso_comun.apariciones!='1':
            date = Pool().get('ir.date')
            hoy = date.today()
            publicacion = Pool().get('edicion.publicacion_diario')
            pub_centimetros = publicacion(Transaction().context.get('active_id'))
            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            cant=self.aviso_comun.cant_centimetros * self.aviso_comun.cant_columnas
            repeticion = self.aviso_comun.cant_apariciones*Decimal(self.aviso_comun.apariciones)
            if ((cant*repeticion)<=((Decimal(pub_centimetros.cm))*(Decimal(pub_centimetros.col)))):
                texto = self.aviso_comun.descripcion.encode('utf-8')
                precio_unitario=prod.list_price
                fecha = self.aviso_comun.inicio
                ubicacion = self.aviso_comun.ubicacion
                origen = self.producto.origen

                #creacion de las publicaciones de diario a las qe se destinan los cms
                for i in range(repeticion):
                    pub = self.crear_linea_publicacion_diario(prod,ubicacion,fecha,origen,texto)
                    pub.cm=Decimal(self.aviso_comun.cant_centimetros)
                    pub.col=Decimal(self.aviso_comun.cant_columnas)
                    if (self.aviso_comun.ubicacion == 'Libre'):
                        pass
                    elif (self.aviso_comun.ubicacion == 'Suplemento'):
                        pub.nombre_sup=self.aviso_comun.suplemento
                    elif (self.aviso_comun.ubicacion == 'Par'):
                        pub.nro_pag=self.aviso_comun.nro_pag
                    elif (self.aviso_comun.ubicacion == 'Impar'):
                        pub.nro_pag=self.aviso_comun.nro_pag
                    else:
                        pass
                    if(fecha<=hoy):
                        pub.state='reprogramar'
                    pub.save()
                    #descuenta cms del nuevo aviso de la cantidad de cms
                    pub_centimetros.cm = Decimal(pub_centimetros.cm)-Decimal(self.aviso_comun.cant_centimetros)
                    pub_centimetros.col = Decimal(pub_centimetros.col)-Decimal(self.aviso_comun.cant_columnas)
                    pub_centimetros.save()
                    fecha = fecha +timedelta(days=1)
                return 'end'
            else:
                self.raise_user_error('error_centimetros')
        else:
           return 'fechas_aviso_comun'

    def transition_terminar_fechas_aviso_comun(self):
        date = Pool().get('ir.date')
        hoy = date.today()
        publicacion = Pool().get('edicion.publicacion_diario')
        pub_centimetros = publicacion(Transaction().context.get('active_id'))
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        cant=self.aviso_comun.cant_centimetros * self.aviso_comun.cant_columnas
        repeticion = self.aviso_comun.cant_apariciones*Decimal(self.aviso_comun.apariciones)
        if ((cant*repeticion)<=((Decimal(pub_centimetros.cm))*(Decimal(pub_centimetros.col)))):
            texto = self.aviso_comun.descripcion.encode('utf-8')
            precio_unitario=prod.list_price
            fecha = self.fechas_aviso_comun.fecha
            ubicacion = self.aviso_comun.ubicacion
            origen = self.producto.origen

            #creacion de la publicacion de diario a las qe se destinan los cms
            pub = self.crear_linea_publicacion_diario(prod,ubicacion,fecha,origen,texto)
            pub.cm=Decimal(self.aviso_comun.cant_centimetros)
            pub.col=Decimal(self.aviso_comun.cant_columnas)
            if (self.aviso_comun.ubicacion == 'Libre'):
                pass
            elif (self.aviso_comun.ubicacion == 'Suplemento'):
                pub.nombre_sup=self.aviso_comun.suplemento
            elif (self.aviso_comun.ubicacion == 'Par'):
                pub.nro_pag=self.aviso_comun.nro_pag
            elif (self.aviso_comun.ubicacion == 'Impar'):
                pub.nro_pag=self.aviso_comun.nro_pag
            else:
                pass
            if(fecha<=hoy):
                pub.state='reprogramar'
            pub.save()
            if self.fechas_aviso_comun.cant_apariciones==self.aviso_comun.cant_apariciones:
                #descuenta cms del nuevo aviso de la cantidad de cms
                pub_centimetros.cm = Decimal(pub_centimetros.cm)-Decimal(self.aviso_comun.cant_centimetros)
                pub_centimetros.col = Decimal(pub_centimetros.col)-Decimal(self.aviso_comun.cant_columnas)
                pub_centimetros.save()
                return 'end'
            else:
                return 'fechas_aviso_comun'
        else:
            self.raise_user_error('error_centimetros')
   

    def transition_terminar_aviso_especial(self):
        if self.aviso_especial.apariciones!='1':
            date = Pool().get('ir.date')
            hoy = date.today()
            publicacion = Pool().get('edicion.publicacion_diario')
            pub_centimetros = publicacion(Transaction().context.get('active_id'))
            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            cant=Decimal(self.aviso_especial.cant_centimetros) * Decimal(self.aviso_especial.cant_columnas)
            repeticion = self.aviso_especial.cant_apariciones*Decimal(self.aviso_especial.apariciones)
            if ((cant*repeticion)<=((Decimal(pub_centimetros.cm))*(Decimal(pub_centimetros.col)))):
                texto = self.aviso_especial.descripcion.encode('utf-8')
                precio_unitario=prod.list_price
                fecha = self.aviso_especial.inicio
                ubicacion = self.aviso_especial.ubicacion
                origen = self.producto.origen

                #creacion de las publicaciones de diario a las qe se destinan los cms
                for i in range(repeticion):
                    pub = self.crear_linea_publicacion_diario(prod,ubicacion,fecha,origen,texto)
                    pub.unidad=1
                    if(fecha<=hoy):
                        pub.state='reprogramar'
                    pub.save()

                    #descuenta cms del nuevo aviso de la cantidad de cms
                    pub_centimetros.cm = Decimal(pub_centimetros.cm)-Decimal(self.aviso_especial.cant_centimetros)
                    pub_centimetros.col = Decimal(pub_centimetros.col)-Decimal(self.aviso_especial.cant_columnas)
                    pub_centimetros.save()
                    fecha = fecha +timedelta(days=1)
                return 'end'
            else:
                self.raise_user_error('error_centimetros')
        else:
           return 'fechas_aviso_especial'
   

    def transition_terminar_fechas_aviso_especial(self):
        date = Pool().get('ir.date')
        hoy = date.today()
        publicacion = Pool().get('edicion.publicacion_diario')
        pub_centimetros = publicacion(Transaction().context.get('active_id'))
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        cant=Decimal(self.aviso_especial.cant_centimetros) * Decimal(self.aviso_especial.cant_columnas)
        repeticion = self.aviso_especial.cant_apariciones*Decimal(self.aviso_especial.apariciones)
        if ((cant*repeticion)<=((Decimal(pub_centimetros.cm))*(Decimal(pub_centimetros.col)))):
            texto = self.aviso_especial.descripcion.encode('utf-8')
            precio_unitario=prod.list_price
            fecha = self.fechas_aviso_especial.fecha
            ubicacion = self.aviso_especial.ubicacion
            origen = self.producto.origen

            #creacion de la publicacion de diario a las qe se destinan los cms
            pub = self.crear_linea_publicacion_diario(prod,ubicacion,fecha,origen,texto)
            pub.unidad=1
            if(fecha<=hoy):
                pub.state='reprogramar'
            pub.save()

            if self.fechas_aviso_especial.cant_apariciones==self.aviso_especial.cant_apariciones:
                #descuenta cms del nuevo aviso de la cantidad de cms
                pub_centimetros.cm = Decimal(pub_centimetros.cm)-Decimal(self.aviso_especial.cant_centimetros)
                pub_centimetros.col = Decimal(pub_centimetros.col)-Decimal(self.aviso_especial.cant_columnas)
                pub_centimetros.save()
                return 'end'
            else:
                return 'fechas_aviso_especial'
        else:
            self.raise_user_error('error_centimetros')
   


    def transition_terminar_funebre_destacado(self):
        if self.funebre_destacado.apariciones!='1':
            date = Pool().get('ir.date')
            hoy = date.today()
            publicacion = Pool().get('edicion.publicacion_diario')
            pub_centimetros = publicacion(Transaction().context.get('active_id'))
            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            cant=self.funebre_destacado.cant_centimetros * self.funebre_destacado.cant_columnas
            repeticion = self.funebre_destacado.cant_apariciones*Decimal(self.funebre_destacado.apariciones)
            if ((cant*repeticion)<=((Decimal(pub_centimetros.cm))*(Decimal(pub_centimetros.col)))):
                texto = self.funebre_destacado.descripcion.encode('utf-8')
                precio_unitario=prod.list_price
                fecha = self.funebre_destacado.inicio
                ubicacion = self.funebre_destacado.ubicacion
                origen = self.producto.origen

                #creacion de las publicaciones de diario a las qe se destinan los cms
                for i in range(repeticion):
                    pub = self.crear_linea_publicacion_diario(prod,ubicacion,fecha,origen,texto)
                    pub.cm=Decimal(self.funebre_destacado.cant_centimetros)
                    pub.col=Decimal(self.funebre_destacado.cant_columnas)
                    if(fecha<=hoy):
                        pub.state='reprogramar'
                    pub.save()

                    #descuenta cms del nuevo aviso de la cantidad de cms
                    pub_centimetros.cm = Decimal(pub_centimetros.cm)-Decimal(self.funebre_destacado.cant_centimetros)
                    pub_centimetros.col = Decimal(pub_centimetros.col)-Decimal(self.funebre_destacado.cant_columnas)
                    pub_centimetros.save()
                    fecha = fecha +timedelta(days=1)
                return 'end'
            else:
                self.raise_user_error('error_centimetros')
        else:
           return 'fechas_funebre_destacado'


    def transition_terminar_fechas_funebre_destacado(self):
        date = Pool().get('ir.date')
        hoy = date.today()
        publicacion = Pool().get('edicion.publicacion_diario')
        pub_centimetros = publicacion(Transaction().context.get('active_id'))
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        cant=self.funebre_destacado.cant_centimetros * self.funebre_destacado.cant_columnas
        repeticion = self.funebre_destacado.cant_apariciones*Decimal(self.funebre_destacado.apariciones)
        if ((cant*repeticion)<=((Decimal(pub_centimetros.cm))*(Decimal(pub_centimetros.col)))):
            texto = self.funebre_destacado.descripcion.encode('utf-8')
            precio_unitario=prod.list_price
            fecha = self.fechas_funebre_destacado.fecha
            ubicacion = self.funebre_destacado.ubicacion
            origen = self.producto.origen

            #creacion de la publicacion de diario a las qe se destinan los cms
            pub = self.crear_linea_publicacion_diario(prod,ubicacion,fecha,origen,texto)
            pub.cm=Decimal(self.funebre_destacado.cant_centimetros)
            pub.col=Decimal(self.funebre_destacado.cant_columnas)
            if(fecha<=hoy):
                pub.state='reprogramar'
            pub.save()

            if self.fechas_funebre_destacado.cant_apariciones==self.funebre_destacado.cant_apariciones:
                #descuenta cms del nuevo aviso de la cantidad de cms
                pub_centimetros.cm = Decimal(pub_centimetros.cm)-Decimal(self.funebre_destacado.cant_centimetros)
                pub_centimetros.col = Decimal(pub_centimetros.col)-Decimal(self.funebre_destacado.cant_columnas)
                pub_centimetros.save()
                return 'end'
            else:
                return 'fechas_funebre_destacado'
        else:
            self.raise_user_error('error_centimetros')


    def transition_terminar_clasif_destacado(self):
        if self.clasif_destacado.apariciones!='1':
            date = Pool().get('ir.date')
            hoy = date.today()
            publicacion = Pool().get('edicion.publicacion_diario')
            pub_centimetros = publicacion(Transaction().context.get('active_id'))
            productos = Pool().get('product.product')
            prod = self.producto.producto.products[0]
            cant=self.clasif_destacado.cant_centimetros * self.clasif_destacado.cant_columnas
            repeticion = self.clasif_destacado.cant_apariciones*Decimal(self.clasif_destacado.apariciones)
            if ((cant*repeticion)<=((Decimal(pub_centimetros.cm))*(Decimal(pub_centimetros.col)))):
                
                precio_unitario=prod.list_price
                fecha = self.clasif_destacado.inicio
                ubicacion = self.clasif_destacado.ubicacion
                origen = self.producto.origen
                texto = self.clasif_destacado.descripcion.encode('utf-8')
                #creacion de las publicaciones de diario a las qe se destinan los cms
                for i in range(repeticion):
                    pub = self.crear_linea_publicacion_diario(prod,ubicacion,fecha,origen,texto)
                    pub.cm=Decimal(self.clasif_destacado.cant_centimetros)
                    pub.col=Decimal(self.clasif_destacado.cant_columnas)
                    if(fecha<=hoy):
                        pub.state='reprogramar'
                    pub.save()

                    #descuenta cms del nuevo aviso de la cantidad de cms
                    pub_centimetros.cm = Decimal(pub_centimetros.cm)-Decimal(self.clasif_destacado.cant_centimetros)
                    pub_centimetros.col = Decimal(pub_centimetros.col)-Decimal(self.clasif_destacado.cant_columnas)
                    pub_centimetros.save()
                    fecha = fecha +timedelta(days=1)
                return 'end'
            else:
                self.raise_user_error('error_centimetros')
        else:
           return 'fechas_clasif_destacado'
   

    def transition_terminar_fechas_clasif_destacado(self):
        date = Pool().get('ir.date')
        hoy = date.today()
        publicacion = Pool().get('edicion.publicacion_diario')
        pub_centimetros = publicacion(Transaction().context.get('active_id'))
        productos = Pool().get('product.product')
        prod = self.producto.producto.products[0]
        cant=self.clasif_destacado.cant_centimetros * self.clasif_destacado.cant_columnas
        repeticion = self.clasif_destacado.cant_apariciones*Decimal(self.clasif_destacado.apariciones)
        if ((cant*repeticion)<=((Decimal(pub_centimetros.cm))*(Decimal(pub_centimetros.col)))):
            precio_unitario=prod.list_price
            fecha = self.fechas_clasif_destacado.fecha
            ubicacion = self.clasif_destacado.ubicacion
            origen = self.producto.origen
            texto = self.clasif_destacado.descripcion.encode('utf-8')

            #creacion de la publicacion de diario a las qe se destinan los cms
            pub = self.crear_linea_publicacion_diario(prod,ubicacion,fecha,origen,texto)
            pub.cm=Decimal(self.clasif_destacado.cant_centimetros)
            pub.col=Decimal(self.clasif_destacado.cant_columnas)
            if(fecha<=hoy):
                pub.state='reprogramar'
            pub.save()

            if self.fechas_clasif_destacado.cant_apariciones==self.clasif_destacado.cant_apariciones:
                #descuenta cms del nuevo aviso de la cantidad de cms
                pub_centimetros.cm = Decimal(pub_centimetros.cm)-Decimal(self.clasif_destacado.cant_centimetros)
                pub_centimetros.col = Decimal(pub_centimetros.col)-Decimal(self.clasif_destacado.cant_columnas)
                pub_centimetros.save()
                return 'end'
            else:
                return 'fechas_clasif_destacado'
        else:
            self.raise_user_error('error_centimetros')


 
