# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
from trytond.pool import Pool
from trytond.transaction import Transaction
from trytond.modules.company import CompanyReport
from trytond.model import ModelSQL, ModelView, Workflow, fields
from trytond.wizard import Wizard, StateView, Button, StateAction

def es_pub_bn(pub):
    try:
        color = 'Color'
        return not (color in pub.producto.name)
    except:
        return True

def cant_cm(pub):
    try:
        if pub.producto.category.name == 'Aviso Especial':
            cm=Decimal(str(pub.producto.name).split('x')[-1])
            col=Decimal((str(pub.producto.name).split('x')[0]).split(' ')[-1])
            return cm * col
        else:
            res = pub.cm * pub.col
            if pub.producto.name != 'Centimetros':
                return res
            else:
                return 0
    except:
        return 0

class Sale(Workflow, ModelSQL, ModelView):
    'Sale'
    __name__ = 'sale.sale'

class ReporteSalePresupuestador(CompanyReport):
    __name__ = 'reportes.reporte_sale_presupuestador'

    @classmethod
    def parse(cls,report,objects,data,localcontext):
        datos = []
        for sale in objects:
            lista_datos = []
            try:
                lineas=[]
                for line in sale.lines:
                    lineas.append({'line':line,'process':False})
                i1 = 0
                while i1 < len(lineas):
                    l1 = lineas[i1]
                    if not l1['process']:
                        l1['process']=True
                        lineas[i1] = l1
                        repeticiones=1
                        i2 = 0
                        while i2 < len(lineas):
                            l2 = lineas[i2]
                            if not l2['process']:
                                if (l1['line'].amount == l2['line'].amount) and(l1['line'].product.name == l2['line'].product.name) and (l1['line'].quantity == l2['line'].quantity) and (l1['line'].description == l2['line'].description):
                                    l2['process']=True
                                    lineas[i2] = l2
                                    repeticiones=repeticiones+1
                            i2=i2+1
                        lista_datos.append({'line':l1['line'],'repet':repeticiones,'importe':repeticiones*(l1['line']).amount})
                    i1=i1+1
            except:
                pass
            if lista_datos != []:
                 datos.append({'sale':sale,'lineas':lista_datos})
        if datos != []:
            localcontext['datos'] = datos
        return super(ReporteSalePresupuestador,cls).parse(report,objects,data,localcontext)



class Invoice(Workflow, ModelSQL, ModelView):
    'Invoice'
    __name__ = 'account.invoice'

class ReporteInvoicePresupuestador(CompanyReport):
    __name__ = 'reportes.reporte_invoice_presupuestador'

    @classmethod
    def parse(cls,report,objects,data,localcontext):
        datos = []
        for invoice in objects:
            lista_datos = []
            try:
                lineas=[]
                for line in invoice.lines:
                    lineas.append({'line':line,'process':False})
                i1 = 0
                while i1 < len(lineas):
                    l1 = lineas[i1]
                    if not l1['process']:
                        l1['process']=True
                        lineas[i1] = l1
                        repeticiones=1
                        i2 = 0
                        while i2 < len(lineas):
                            l2 = lineas[i2]
                            if not l2['process']:
                                if (l1['line'].amount == l2['line'].amount) and(l1['line'].product.name == l2['line'].product.name) and (l1['line'].quantity == l2['line'].quantity) and (l1['line'].description == l2['line'].description):
                                    l2['process']=True
                                    lineas[i2] = l2
                                    repeticiones=repeticiones+1
                            i2=i2+1
                        lista_datos.append({'line':l1['line'],'repet':repeticiones,'importe':repeticiones*(l1['line']).amount})
                    i1=i1+1
            except:
                pass
            if lista_datos != []:
                 datos.append({'invoice':invoice,'lineas':lista_datos})
        if datos != []:
            localcontext['datos'] = datos
        return super(ReporteInvoicePresupuestador,cls).parse(report,objects,data,localcontext)



class SeleccionEntidad(ModelView):
    'Seleccion Entidad'
    __name__ = 'reportes.seleccion_entidad.start'
    entidad = fields.Many2One('party.party', 'Entidades', required=True)
    desde = fields.Date('Desde')
    hasta = fields.Date('Hasta')

class OpenEstadoCuentaEntidad(Wizard):
    'Open Estado Cuenta Entidad'
    __name__ = 'reportes.open_estado_cuenta_entidad'
    start = StateView('reportes.seleccion_entidad.start',
        'reportes.seleccion_entidad_start_view_form', [
            Button('Cancelar', 'end', 'tryton-cancel'),
            Button('Abrir', 'print_', 'tryton-ok', default=True),
            ])
    print_ = StateAction('reportes.reporte_cuenta_cliente')

    def do_print_(self, action):
        data = {}
        if self.start.desde == None and self.start.hasta == None:
            data = {
                'entidad': self.start.entidad.id,
                'desde': None,
                'hasta': None,
                }
        elif self.start.desde != None and self.start.hasta == None:
            data = {
                'entidad': self.start.entidad.id,
                'desde': self.start.desde,
                'hasta': None,
                }
        elif self.start.desde == None and self.start.hasta != None:
            data = {
                'entidad': self.start.entidad.id,
                'desde': None,
                'hasta': self.start.hasta,
                }
        else:
            data = {
                'entidad': self.start.entidad.id,
                'desde': self.start.desde,
                'hasta': self.start.hasta,
                }
        return action,data

class ReporteEstadoCuentaEntidad(CompanyReport):
    __name__ = 'reportes.reporte_estado_cuenta_entidad'

    @classmethod
    def parse(cls,report,objects,data,localcontext):
        lista_datos = []
        importe_a_pagar=0
        sale = Pool().get('sale.sale')
        party = Pool().get('party.party')
        publicaciones_diario = Pool().get('edicion.publicacion_diario')
        sales=[]
        periodo=''
        if data['desde'] == None and data['hasta'] == None:
            sales= sale.search([('party', '=', data['entidad']),('state','=','processing')])
        elif data['desde'] != None and data['hasta'] == None:
            sales= sale.search([('party', '=', data['entidad']),('state','=','processing'),('sale_date','>=',data['desde'])])
            periodo={'desde':data['desde'],'hasta':None}
        elif data['desde'] == None and data['hasta'] != None:
            sales= sale.search([('party', '=', data['entidad']),('state','=','processing'),('sale_date','<=',data['hasta'])])
            periodo={'desde':None,'hasta':data['hasta']}
        else:
            sales= sale.search([('party', '=', data['entidad']),('state','=','processing'),('sale_date','>=',data['desde']),('sale_date','<=',data['hasta'])])
            periodo={'desde':data['desde'],'hasta':data['hasta']}
        entidad= party(party.search([('id', '=', data['entidad'])])[0])
        for sale in sales:
            pub_linea = []
            for inv in sale.invoices:
                if(inv.state!='paid') and (inv.state!='cancel'):
                    lineas=[]
                    for line in sale.lines:
                        lineas.append({'line':line,'process':False})
                    i1 = 0
                    while i1 < len(lineas):
                        l1 = lineas[i1]
                        if not l1['process']:
                            l1['process']=True
                            lineas[i1] = l1
                            fechas=''
                            pub=None
                            pub = publicaciones_diario.search([('linea','=',l1['line'].id)])
                            if(pub!=None):
                                try:
                                    if(pub[0]!=None):
                                        fechas = str(pub[0].fecha.strftime('%d/%m/%Y'))
                                except:
                                    pass
                            repeticiones=1
                            i2 = 0
                            while i2 < len(lineas):
                                l2 = lineas[i2]
                                if not l2['process']:
                                    if (l1['line'].product.name == l2['line'].product.name) and (l1['line'].quantity == l2['line'].quantity) and (l1['line'].description == l2['line'].description):
                                        l2['process']=True
                                        lineas[i2] = l2
                                        p=None
                                        p = publicaciones_diario.search([('linea','=',l2['line'].id)])
                                        if(p!=None):
                                            try:
                                                if(p[0]!=None):
                                                    fechas=fechas + ' - ' + str(p[0].fecha.strftime('%d/%m/%Y'))
                                            except:
                                                pass

                                        repeticiones=repeticiones+1
                                i2=i2+1
                            if(pub!=None):
                                try:
                                    if(pub[0]!=None):
                                        if repeticiones!=365:
                                            pub_linea.append({'linea':l1['line'],'pub':pub[0],'repet':repeticiones,'fechas':fechas,'es_pub':'True'})
                                        else:
                                            pub_linea.append({'linea':l1['line'],'pub':pub[0],'repet':repeticiones,'fechas':'anual a partir de '+str(pub[0].fecha.strftime('%d/%m/%Y')),'es_pub':'True'})
                                except:
                                    pub_linea.append({'linea':l1['line'],'es_pub':'False'})
                            else:
                                pub_linea.append({'linea':l1['line'],'es_pub':'False'})
                        i1=i1+1
                    if pub_linea != []:
                        lista_datos.append({'sale':sale,'pub_lineas':pub_linea})
                        if (inv.amount_to_pay_today>0):
                            importe_a_pagar = importe_a_pagar + inv.amount_to_pay_today
                        else:
                            importe_a_pagar = importe_a_pagar + inv.total_amount
                break
        localcontext['datos'] = lista_datos
        localcontext['entidad'] = entidad
        localcontext['importe'] = importe_a_pagar
        localcontext['periodo'] = periodo
        return super(ReporteEstadoCuentaEntidad,cls).parse(report,objects,data,localcontext)



class LanzarReporteComercial(Wizard):
    'Open Estado Cuenta Entidad'
    __name__ = 'reportes.lanzar_reporte_comercial'
    start = StateAction('reportes.reporte_comerciales')

    def do_start(self, action):
        data = {}
        datos =[]
        e = Pool().get('edicion.edicion')
        pd = Pool().get('edicion.publicacion_diario')
        ediciones = Transaction().context.get('active_ids')
        for edicion in ediciones:
            for pub in e(edicion).publicacionesDiario:
                p = pd(pd.search([('id', '=', pub.id)])[0])
                if p.producto.category.name != 'Clasificado':
                    if p.impresion == 'imprimiendo':
                        p.impresion = 'impreso'
                    if not p.en_guia:
                        p.en_guia = True
                        p.impresion = 'imprimiendo'
                    else:
                        p.impresion = 'impreso'
                    p.save()
            datos.append(e(edicion).id)
        data = {'datos' : datos}
        return action,data


class ReporteAvisoComercial(CompanyReport):
    __name__ = 'reportes.reporte_avisos_comerciales'


    @classmethod
    def parse(cls,report,objects,data,localcontext):
        datos =[]
        e = Pool().get('edicion.edicion')
        for ed in data['datos']:
            cmBN = 0
            cmColor = 0
            cantBN = 0
            cantColor = 0
            for p in e(ed).publicacionesDiario:
                if (p.state != 'cancelada') and (p.producto.category.name != 'Clasificado') and (p.producto.category.name != 'Insert') and (p.producto.category.name != 'Suplemento') and (p.producto.category.name != 'Centimetros'):
                    if es_pub_bn(p):
                        cmBN += cant_cm(p)
                        cantBN += 1
                    else:
                        cmColor += cant_cm(p)
                        cantColor += 1
            cmTotales = cmBN + cmColor
            cantTotales = cantBN + cantColor
            datos.append({  'edicion':e(ed),
                            'cm_bn':cmBN,
                            'cm_color':cmColor,
                            'cant_bn':cantBN,
                            'cant_color':cantColor,
                            'cm_totales':cmTotales,
                            'cant_totales':cantTotales,
                        })
        localcontext['datos'] = datos
        return super(ReporteAvisoComercial,cls).parse(report,objects,data,localcontext)

class LanzarReporteClasificado(Wizard):
    'Open Estado Cuenta Entidad'
    __name__ = 'reportes.lanzar_reporte_clasificados'
    start = StateAction('reportes.reporte_clasificado')

    def do_start(self, action):
        data = {}
        datos =[]
        e = Pool().get('edicion.edicion')
        pd = Pool().get('edicion.publicacion_diario')
        ediciones = Transaction().context.get('active_ids')
        for edicion in ediciones:
            for pub in e(edicion).publicacionesDiario:
                if pub.producto.category.name == 'Clasificado':
                    p = pd(pd.search([('id', '=', pub.id)])[0])
                    if p.impresion == 'imprimiendo':
                        p.impresion = 'impreso'
                    if not p.en_guia:
                        p.en_guia = True
                        p.impresion = 'imprimiendo'
                    else:
                        p.impresion = 'impreso'
                    p.save()
            datos.append(e(edicion).id)
        data = {'datos' : datos}
        return action,data


class ReporteClasificado(CompanyReport):
    __name__ = 'reportes.reporte_clasificados'

    @classmethod
    def parse(cls,report,objects,data,localcontext):
        datos =[]
        e = Pool().get('edicion.edicion')
        for ed in data['datos']:
            cmBN = 0
            cmColor = 0
            cantBN = 0
            cantColor = 0
            for p in e(ed).publicacionesDiario:
                if (p.state != 'cancelada') and p.producto.category.name == 'Clasificado':
                    if es_pub_bn(p):
                        cmBN += cant_cm(p)
                        cantBN += 1
                    else:
                        cmColor += cant_cm(p)
                        cantColor += 1
            cmTotales = cmBN + cmColor
            cantTotales = cantBN + cantColor
            datos.append({  'edicion':e(ed),
                            'cm_bn':cmBN,
                            'cm_color':cmColor,
                            'cant_bn':cantBN,
                            'cant_color':cantColor,
                            'cm_totales':cmTotales,
                            'cant_totales':cantTotales,
                        })
        localcontext['datos'] = datos
        return super(ReporteClasificado,cls).parse(report,objects,data,localcontext)

