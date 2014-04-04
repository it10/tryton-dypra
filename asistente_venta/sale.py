# -*- coding: utf-8 -*-
from trytond.wizard import Wizard, StateView, StateTransition, StateAction, Button
from trytond.pool import Pool
from trytond.modules.company import CompanyReport
from trytond.model import Workflow,ModelSQL, ModelView, fields
from datetime import timedelta
from trytond.pyson import If, Eval, Bool, Id, Or,Equal, Not, And
from trytond.transaction import Transaction
from decimal import Decimal





#se modifico: 
#'readonly': (Eval('state') != 'draft'  por  'readonly': (Eval('state') != 'quotation'
# y sale_date a reanonly y required para setearlo nosotros
class Sale(Workflow, ModelSQL, ModelView):
    'Sale'
    __name__ = 'sale.sale'
    _rec_name = 'reference'
    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': (Eval('state') != 'quotation') | Eval('lines', [0]),
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ],
        depends=['state'], select=True)
    reference = fields.Char('Reference', readonly=True, select=True)
    description = fields.Char('Description',
        states={
            'readonly': Eval('state') != 'quotation',
            },
        depends=['state'])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('cancel', 'Canceled'),
    ], 'State', readonly=True, required=True)
    sale_date = fields.Date('Sale Date',
        states={
            'readonly': Eval('state').in_(['processing']),
            'required': Eval('state').in_(['processing']),
            },
        depends=['state'])
    payment_term = fields.Many2One('account.invoice.payment_term',
        'Payment Term', required=True, states={
            'readonly': Eval('state') != 'quotation',
            },
        depends=['state'])
    party = fields.Many2One('party.party', 'Party', required=True, select=True,
        states={
            'readonly': Eval('state') != 'quotation',
            }, on_change=['party', 'payment_term'],
        depends=['state'])
    party_lang = fields.Function(fields.Char('Party Language',
            on_change_with=['party']), 'on_change_with_party_lang')
    invoice_address = fields.Many2One('party.address', 'Invoice Address',
        domain=[('party', '=', Eval('party'))], states={
            'readonly': Eval('state') != 'quotation',
            }, depends=['state', 'party'])
    shipment_address = fields.Many2One('party.address', 'Shipment Address',
        domain=[('party', '=', Eval('party'))], states={
            'readonly': Eval('state') != 'quotation',
            },
        depends=['party', 'state'])
    warehouse = fields.Many2One('stock.location', 'Warehouse',
        domain=[('type', '=', 'warehouse')], states={
            'readonly': Eval('state') != 'quotation',
            },
        depends=['state'])
    currency = fields.Many2One('currency.currency', 'Currency', required=True,
        states={
            'readonly': (Eval('state') != 'quotation') |
                (Eval('lines', [0]) & Eval('currency', 0)),
            },
        depends=['state'])
    currency_digits = fields.Function(fields.Integer('Currency Digits',
            on_change_with=['currency']), 'on_change_with_currency_digits')
    lines = fields.One2Many('sale.line', 'sale', 'Lines', states={
            'readonly': Eval('state') != 'quotation',
            }, on_change=['lines', 'currency', 'party'],
        depends=['party', 'state'])
    comment = fields.Text('Comment')
    untaxed_amount = fields.Function(fields.Numeric('Untaxed',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']), 'get_amount')
    untaxed_amount_cache = fields.Numeric('Untaxed Cache',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    tax_amount = fields.Function(fields.Numeric('Tax',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']), 'get_amount')
    tax_amount_cache = fields.Numeric('Tax Cache',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    total_amount = fields.Function(fields.Numeric('Total',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']), 'get_amount')
    total_amount_cache = fields.Numeric('Total Tax',
        digits=(16, Eval('currency_digits', 2)),
        readonly=True,
        depends=['currency_digits'])
    invoice_method = fields.Selection([
            ('manual', 'Manual'),
            ('order', 'On Order Processed'),
            ('shipment', 'On Shipment Sent'),
            ],
        'Invoice Method', required=True, states={
            'readonly': Eval('state') != 'quotation',
            },
        depends=['state'])
    invoice_state = fields.Selection([
            ('none', 'None'),
            ('waiting', 'Waiting'),
            ('paid', 'Paid'),
            ('exception', 'Exception'),
            ], 'Invoice State', readonly=True, required=True)
    invoices = fields.Many2Many('sale.sale-account.invoice',
            'sale', 'invoice', 'Invoices', readonly=True)
    invoices_ignored = fields.Many2Many('sale.sale-ignored-account.invoice',
            'sale', 'invoice', 'Ignored Invoices', readonly=True)
    invoices_recreated = fields.Many2Many(
        'sale.sale-recreated-account.invoice', 'sale', 'invoice',
        'Recreated Invoices', readonly=True)
    shipment_method = fields.Selection([
            ('manual', 'Manual'),
            ('order', 'On Order Processed'),
            ('invoice', 'On Invoice Paid'),
            ], 'Shipment Method', required=True,
        states={
            'readonly': Eval('state') != 'quotation',
            },
        depends=['state'])
    shipment_state = fields.Selection([
            ('none', 'None'),
            ('waiting', 'Waiting'),
            ('sent', 'Sent'),
            ('exception', 'Exception'),
            ], 'Shipment State', readonly=True, required=True)
    shipments = fields.Function(fields.One2Many('stock.shipment.out', None,
        'Shipments'), 'get_shipments', searcher='search_shipments')
    shipment_returns = fields.Function(
        fields.One2Many('stock.shipment.out.return', None, 'Shipment Returns'),
        'get_shipment_returns', searcher='search_shipment_returns')
    moves = fields.Function(fields.One2Many('stock.move', None, 'Moves'),
        'get_moves')

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()

        cls._order.insert(0, ('sale_date', 'DESC'))
        cls._order.insert(1, ('id', 'DESC'))
        cls._error_messages.update({
                'invalid_method': ('Invalid combination of shipment and '
                    'invoicing methods on sale "%s".'),
                'addresses_required': (
                    'Invoice and Shipment addresses must be '
                    'defined for the quotation of sale "%s".'),
                'warehouse_required': ('Warehouse must be defined for the '
                    'quotation of sale "%s".'),
                'missing_account_receivable': ('It misses '
                        'an "Account Receivable" on the party "%s".'),
                'delete_cancel': ('Sale "%s" must be cancelled before '
                    'deletion.'),
                'error_sale': 'Excepcion en confirmacion de venta o creacion de publicaciones',
                })
        cls._transitions |= set((
                ('draft', 'quotation'),
                ('quotation', 'confirmed'),
                ('confirmed', 'processing'),
                ('processing', 'processing'),
                ('draft', 'cancel'),
                ('quotation', 'cancel'),
                ('quotation', 'draft'),
                ('cancel', 'draft'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft', 'quotation']),
                    },
                'draft': {
                    'invisible': Eval('state').in_(['cancel', 'quotation', 'confirmed', 'processing']),
                    'icon': If(Eval('state') == 'cancel', 'tryton-clear',
                        'tryton-go-previous'),
                    },
                'quote': {
                    'invisible': Eval('state') != 'draft',
                    'readonly': ~Eval('lines', []),
                    },
                'confirm': {
                    'invisible': Eval('state') != 'quotation',
                    },
                'process': {
                    'invisible': Eval('state') != 'confirmed',
                    },
                'handle_invoice_exception': {
                    'invisible': ((Eval('invoice_state') != 'exception')
                        | (Eval('state') == 'cancel')),
                    'readonly': ~Eval('groups', []).contains(
                        Id('sale', 'group_sale')),
                    },
                'handle_shipment_exception': {
                    'invisible': ((Eval('shipment_state') != 'exception')
                        | (Eval('state') == 'cancel')),
                    'readonly': ~Eval('groups', []).contains(
                        Id('sale', 'group_sale')),
                    },
                })
        # The states where amounts are cached
        cls._states_cached = ['confirmed', 'processing', 'done', 'cancel']


    @staticmethod
    def default_state():
        return 'quotation'


    @classmethod
    def copy(cls, sales, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['state'] = 'quotation'
        default['reference'] = None
        default['invoice_state'] = 'none'
        default['invoices'] = None
        default['invoices_ignored'] = None
        default['shipment_state'] = 'none'
        default.setdefault('sale_date', None)
        return super(Sale, cls).copy(sales, default=default)



    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, sales):       
        edicion = Pool().get('edicion.edicion')
        super(Sale, cls).confirm(sales)
        for s in sales:
            if (s.payment_term.name == 'Efectivo'):
                super(Sale, cls).process(sales)
            else:
                #super(Sale, cls).process(sales)
                s.invoice_method='manual'
                s.state='processing'
                s.save()
            try:
                text = ''
                for line in s.lines:
                    if line.type == 'comment':
                        text= line.description
                for line in s.lines:
                    if line.type == 'line':
                        if line.categoria_diario:
                            try:
                            
                                publicacion_diario = Pool().get('edicion.publicacion_diario')
                                pub_pres_diario = Pool().get('edicion.publicacion_presupuestada_diario')                                
                                presupuestada = pub_pres_diario(line.pub_presup_diario)
                                try:
                                    edic= edicion(edicion.search([('fecha', '=', presupuestada.fecha)])[0])
                                except:
                                    edic=edicion.create([{'fecha':presupuestada.fecha}])[0]
                                    edic.save()
                                pub_diario=""
                                Date = Pool().get('ir.date')
                                hoy = Date.today()
                                if(presupuestada.fecha>=hoy):
                                    pub_diario = publicacion_diario.create([{
                                        'termino_pago':s.payment_term,
                                        'linea':line,
                                        'cliente':s.party,
                                        'producto' : line.product,
                                        'descrip' : text,
                                        'cm':presupuestada.cm,
                                        'col':presupuestada.col,
                                        'lin':presupuestada.lin,
                                        'pag':presupuestada.pag,
                                        'unidad':presupuestada.unidad,
                                        'origen':presupuestada.origen,
                                        'ubicacion': presupuestada.ubicacion,
                                        'nro_pag':presupuestada.nro_pag,
                                        'nombre_sup':presupuestada.nombre_sup,
                                        'venta_cm':presupuestada.venta_cm,
                                        'edicion' : edic,
                                        }])[0]
                                else:
                                    pub_diario = publicacion_diario.create([{
                                        'termino_pago':s.payment_term,
                                        'linea':line,
                                        'cliente': s.party,
                                        'producto' : line.product,
                                        'descrip' : text,
                                        'cm':presupuestada.cm,
                                        'col':presupuestada.col,
                                        'lin':presupuestada.lin,
                                        'pag':presupuestada.pag,
                                        'unidad':presupuestada.unidad,
                                        'origen':presupuestada.origen,
                                        'ubicacion': presupuestada.ubicacion,
                                        'nro_pag':presupuestada.nro_pag,
                                        'nombre_sup':presupuestada.nombre_sup,
                                        'venta_cm':presupuestada.venta_cm,
                                        'edicion' : edic,
                                        'state':'reprogramar',
                                        }])[0]
                                pub_diario.save()
                            except:
                                cls.raise_user_error('error_sale')
                        elif line.categoria_radio:
                            try:
                                pub_pres_radio = Pool().get('edicion.publicacion_presupuestada_radio')
                                publicacion_radio = Pool().get('edicion.publicacion_radio')                                
                                presupuestada = pub_pres_radio(line.pub_presup_radio)
                                try:
                                    edic= edicion(edicion.search([('fecha', '=', presupuestada.fecha)])[0])
                                except:
                                    edic=edicion.create([{'fecha':presupuestada.fecha}])[0]
                                    edic.save()
                                if presupuestada.horario_programacion != 'Manual':
                                    pub_radio = publicacion_radio.create([{
                                        'linea':line,
                                        'cliente':line.sale.party,
                                        'producto' : line.product,
                                        'descrip' : text,
                                        'edicion' : edic,
                                        'categoria':str(line.product.category.name),
                                        'horario_programacion' : presupuestada.horario_programacion,
                                        }])[0]
                                else:
                                    pass
                                pub_radio.save()
                            except:
                                cls.raise_user_error('error_sale')
                        elif line.categoria_dig:
                            try:
                                edicion_publicacion_digital = Pool().get('edicion.edicion_publicacion_digital')
                                pub_pres_digital = Pool().get('edicion.publicacion_presupuestada_digital')
                                publicacion_digital = Pool().get('edicion.publicacion_digital')                                
                                presupuestada = pub_pres_digital(line.pub_presup_digital)
                                if presupuestada.expandible:
                                    pub_dig = publicacion_digital.create([{
                                        'linea':line,
                                        'cliente':line.sale.party,
                                        'producto' : line.product,
                                        'descrip' : text,
                                        'categoria':str(line.product.category.name),
                                        'expandible':presupuestada.expandible,
                                        'a':presupuestada.a,
                                        }])[0]
                                else:
                                    pub_dig = publicacion_digital.create([{
                                        'linea':line,
                                        'cliente':line.sale.party,
                                        'producto' : line.product,
                                        'descrip' : text,
                                        'categoria':str(line.product.category.name),
                                        'expandible':presupuestada.expandible,
                                        }])[0]
                                pub_dig.save()
                                inicio = presupuestada.fecha
                                fecha_aux = inicio
                                hasta = inicio
                                hasta += relativedelta(months=+1)
                                cantidad = hasta - inicio
                                rango = cantidad.days+1
                                for j in range(rango):
                                    edic = 0
                                    try:
                                        edic= edicion(edicion.search([('fecha', '=', fecha_aux)])[0])
                                    except:
                                        edic=edicion.create([{'fecha':fecha_aux}])[0]
                                        edic.save()
                                    ed_pub_digital = edicion_publicacion_digital.create([{
                                                    'edicion_id':edic,
                                                    'digital_id':pub_dig,
                                                    }])[0]
                                    ed_pub_digital.save()
                                    fecha_aux = fecha_aux +timedelta(days=1)
                            except:
                                cls.raise_user_error('error_sale')
                        else:
                            pass
                        #cls.raise_user_error('error_sale')
            except:
                cls.raise_user_error('error_sale')
            




class SaleLine(ModelSQL, ModelView):
    'Sale Line'
    __name__ = 'sale.line'
    _rec_name = 'description'
    
    pub_presup_diario = fields.One2One('edicion.publicacion_presupuestada_diario_linea', 'linea_id', 'pub_presup_diario_id','Publicacion',
                                        states={ 
                                                  'readonly':Or(Or(Or(Bool(Eval('categoria_dig')),Bool(Eval('categoria_radio'))),Not(Bool(Eval('categoria_diario')))),Not(Equal(Eval('type'),'line'))),
                                                  'required':Bool(Eval('categoria_diario'))
                                                },
                                        domain=[('linea.id','=',Eval('id'))],
                                        on_change_with=['product'],
                                        )
    pub_presup_radio = fields.One2One('edicion.publicacion_presupuestada_radio_linea', 'linea_id', 'pub_presup_radio_id','Publicacion',
                                        states={ 
                                                  'readonly':Or(Or(Or(Bool(Eval('categoria_diario')),Bool(Eval('categoria_dig'))),Not(Bool(Eval('categoria_radio')))),Not(Equal(Eval('type'),'line'))),
                                                  'required':Bool(Eval('categoria_radio'))
                                                },
                                        domain=[('linea.id','=',Eval('id'))],
                                        )
    pub_presup_digital = fields.One2One('edicion.publicacion_presupuestada_digital_linea', 'linea_id', 'pub_presup_digital_id','Publicacion',
                                        states={ 
                                                  'readonly':Or(Or(Or(Bool(Eval('categoria_diario')),Bool(Eval('categoria_radio'))),Not(Bool(Eval('categoria_dig')))),Not(Equal(Eval('type'),'line'))),
                                                  'required':Bool(Eval('categoria_dig'))
                                                },
                                        domain=[('linea.id','=',Eval('id'))],
                                         )
    categoria_diario = fields.Boolean('Diario',select=False,
                                        states={'readonly':Or(Or(Bool(Eval('categoria_radio')),Bool(Eval('categoria_dig'))),Not(Equal(Eval('type'),'line')))},
                                        on_change_with=['product'],
                                     )
    categoria_radio = fields.Boolean('Radio',select=False,
                                        states={'readonly':Or(Or(Bool(Eval('categoria_diario')),Bool(Eval('categoria_dig'))),Not(Equal(Eval('type'),'line')))},
                                        on_change_with=['product'],
                                    )
    categoria_dig = fields.Boolean('Digital',select=False,
                                        states={'readonly':Or(Or(Bool(Eval('categoria_radio')),Bool(Eval('categoria_diario'))),Not(Equal(Eval('type'),'line')))},
                                        on_change_with=['product'],
                                    )
    
    description = fields.Text('Description', size=None, required=True, on_change_with=['pub_presup_diario','pub_presup_radio','pub_presup_digital','product','categoria_diario','categoria_radio','categoria_dig'])

    quantity = fields.Float('Quantity',
                            digits=(16, Eval('unit_digits', 2)),
                            states={
                                'invisible': Eval('type') != 'line',
                                'required': Eval('type') == 'line',
                                'readonly': ~Eval('_parent_sale', {}),
                                }, on_change=['product', 'quantity', 'unit',
                                '_parent_sale.currency', '_parent_sale.party',
                                '_parent_sale.sale_date'],on_change_with=['pub_presup_diario','unit'],
                            depends=['type', 'unit_digits'])

    unit_price = fields.Numeric('Unit Price', digits=(16, 4),
                                states={
                                    'invisible': Eval('type') != 'line',
                                    'required': Eval('type') == 'line',
                                    }, 
                                    on_change_with=['pub_presup_diario','pub_presup_radio','pub_presup_digital','categoria_diario','categoria_radio','categoria_dig','product','unit_price'],
                                    depends=['type'])

    amount = fields.Function(fields.Numeric('Amount',
                                            digits=(16, Eval('_parent_sale', {}).get('currency_digits', 2)),
                                            states={
                                                'invisible': ~Eval('type').in_(['line', 'subtotal']),
                                                'readonly': ~Eval('_parent_sale'),
                                                }, on_change_with=['type', 'quantity', 'unit_price', 'unit',
                                                '_parent_sale.currency','pub_presup_diario'],
                                            depends=['type']), 'get_amount')


    def on_change_with_quantity(self):
        try:
            if(self.unit.symbol=='cm'):
                res=float(self.pub_presup_diario.cm * self.pub_presup_diario.col)
                return res
            elif(self.unit.symbol=='lin'):
                res=float(self.pub_presup_diario.lin)
                return res
            elif(self.unit.symbol=='pag'):
                res=float(self.pub_presup_diario.pag)
                return res
            elif(self.unit.symbol=='u'):
                res=float(self.pub_presup_diario.unidad)
                return res
            else:
                return self.quantity
        except:
            try:
                return self.quantity
            except:
                return 0

    def on_change_with_unit_price(self):
        try:
            if self.categoria_diario:
                if(self.pub_presup_diario.ubicacion=='Libre') or (self.pub_presup_diario.ubicacion=='Suplemento'):
                    return self.product.template.list_price
                elif(self.pub_presup_diario.ubicacion=='Par'):
                    return self.product.template.list_price * Decimal('1.25')
                elif(self.pub_presup_diario.ubicacion=='Impar'):
                    return self.product.template.list_price * Decimal('1.30')
                elif(self.pub_presup_diario.ubicacion=='Tapa') or (self.pub_presup_diario.ubicacion=='Central') or (self.pub_presup_diario.ubicacion=='Contratapa') :
                    return self.product.template.list_price * Decimal('1.50')
                elif(self.product.template.category.name=='Insert') or (self.product.template.category.name=='Suplemento'):
                    return self.unit_price
                elif self.product.template.category.name=='Centimetros':
                    return self.unit_price
                else:
                    return self.product.template.list_price
            elif self.categoria_radio:
                return self.product.template.list_price
            else:
                if self.pub_presup_digital.expandible:
                    return self.product.template.list_price * Decimal(1+(Decimal(self.pub_presup_digital.recargo)/Decimal('100')))
                else:
                   return self.product.template.list_price 
        except:
            try:
                return self.product.template.list_price
            except:
                return 0

    def on_change_with_description(self):
        try:
            if(self.product):
                if(self.categoria_diario):
                    return self.pub_presup_diario.get_rec_name(None)
                elif(self.categoria_radio):
                    return self.pub_presup_radio.rec_name
                elif(self.categoria_dig):
                    return self.pub_presup_digital.rec_name
                else:
                    return self.product.rec_name
            else:
                return "no hay producto"
        except:
            return "catch description"


    def on_change_with_categoria_diario(self):
        try:
            if (self.product.template.category.parent.name) == 'Diario':
                return True
            else:
                return False
        except:
            return False

    def on_change_with_categoria_radio(self):
        try:
            if (self.product.template.category.parent.name) == 'Radio':
                return True
            else:
                return False
        except:
            return False

    def on_change_with_categoria_dig(self):
        try:
            if (self.product.template.category.parent.name) == 'Digital':
                return True
            else:
                return False
        except:
            return False

    def on_change_with_pub_presup_diario(self):
        return None


class FormaVenta(ModelView):
    'FormaVenta'
    __name__ = 'asistente_venta.forma_venta.start'
    fondo = fields.Text(" ", readonly=True)

    @staticmethod
    def default_fondo():
        var="* Seleccione VENTA para realizar una venta comun. \n* Seleccione ASISTENTE VENTA para realizar una venta con asistencia para avisos de medios."
        return var

class EleccionFormaVenta(Wizard):
    'EleccionFormaVenta'
    __name__ = 'asistente_venta.eleccion_forma_venta'

    #start = StateTransition()

    start = StateView('asistente_venta.forma_venta.start',
                      'asistente_venta.eleccion_forma_venta_form',
                      [Button('Cancelar', 'end', 'tryton-cancel'),
                      Button('VENTA', 'venta_comun', 'tryton-go-next'),
                      Button('ASISTENTE VENTA', 'asistente_venta', 'tryton-go-next'),
                      ])

    venta_comun = StateAction('sale.act_sale_form')

    asistente_venta = StateAction('asistente_venta.act_wizard_asistente')


    def do_venta_comun(self, action):
        data = {}
        return action,data

    def do_asistente_venta(self, action):
        data = {}
        return action,data
 
