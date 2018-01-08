# -*- coding: utf-8 -*-
from odoo import fields,api,models
from odoo.exceptions import ValidationError

class boletin(models.Model):
    _name = 'control_seccion.boletin'
    _order = "seccion desc"

    seccion = fields.Many2one(comodel_name="control_seccion.seccion",
        string="Seccion",required=True,readonly=True,)
    full_lapsos = fields.Boolean(default=False,store=True,compute='_complete_lapso')
    lineas_lapsos = fields.One2many(comodel_name="control_seccion.lapso",
        inverse_name="boletin_id")

    @api.depends('lineas_lapsos')
    def _complete_lapso(self):
        for x in self:
            if(len(x.lineas_lapsos) == x.seccion.max_lapso):
                x.full_lapsos = True

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id,str(values.seccion.grado.grado) + ' ' +
             values.seccion.grado.nivel) + ' Seccion ' + 
            values.seccion.seccion + ' Periodo '+ values.seccion.periodo)
        return res

class tipo_eval(models.Model):
    _name = "control_seccion.tipo_eval"

    name = fields.Char(string="Tipo de Evaluacion",required=True,)

class planificacion(models.Model):
    _name = "control_seccion.planificacion"
    _rec_name="materia"

    lapso = fields.Many2one(comodel_name="control_seccion.lapso",readonly=True)    
    materia = fields.Many2one(comodel_name="control_seccion.materias",string="Materia")
    lineas_plan = fields.One2many(comodel_name="control_seccion.planificacion_line",
        inverse_name="plan_id",string="Planificacion")
    indicador = fields.One2many(comodel_name="control_seccion.ind_template",
        inverse_name="plan_id",string="indicadores")
    state = fields.Selection(selection=[('draft','Por planificar'),
            ('ending','Materia planificada')],default="draft",string="Estado",readonly=True)
    min_logro = fields.Integer(string="Min. Logro",
        help="Indica el valor minimo para asumir que es un logro",default=15)

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id, values.materia.materia + ' ' + 
                str(values.materia.grado) + ' ' + str(values.lapso.nro_lapso)))
        return res

    @api.multi
    def write(self,vals):
        if('lineas_plan' in vals):
            lineas = 0
            for x in vals['lineas_plan']:
                if(x[0] != 2):
                    lineas += 1
            if(lineas > 0):
                vals['state'] = 'ending'
            else:
                vals['state'] = 'draft'
        res = super(planificacion,self).write(vals)
        return res

class planificacion_lineas(models.Model):
    _name = "control_seccion.planificacion_line"

    plan_id = fields.Many2one(comodel_name="control_seccion.planificacion")
    tipo_eval_id = fields.Many2one(comodel_name="control_seccion.tipo_eval",
        string="Tipo de Evaluacion",required=True,)
    porcentaje = fields.Integer(string="Porcentaje",required=True)
    check = fields.Boolean(string="Realizado",default=False,readonly=True)
    fecha = fields.Date(string="Fecha",required=True)
    contenido = fields.Many2one(comodel_name="control_seccion.contenido",
        string="Contenido")

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id,str(values.contenido.name) + ' ' + str(values.porcentaje) + '%'))
        return res

    @api.onchange('porcentaje')
    def onchange_porcentaje(self):
        context = self._context.copy()
        porcentaje_total = 0 
        if('plan' in context):
            for planes in context['plan']:
                if(len(planes)==3):
                    continue
                if(type(planes[2]) == bool):
                    if(planes[0]==4):
                        porcentaje_total += self.env['control_seccion.planificacion_line'].search([('id','=',planes[1])]).porcentaje
                    continue
                if('porcentaje' in planes[2]):
                    porcentaje_total += planes[2]['porcentaje']
            if(porcentaje_total == 100):
                raise ValidationError('Disculpe, ya ha superado el 100 % posible para las evaluaciones')
            elif(self.porcentaje + porcentaje_total > 100):
                self.porcentaje = 100 - porcentaje_total

class tema (models.Model):
    _name = 'control_seccion.contenido'

    lapso = fields.Many2one(comodel_name="control_seccion.lapso")
    name = fields.Char(string="Contenido",required=True)

class indicador_template(models.Model):
    _name = "control_seccion.ind_template"

    tema = fields.Many2one(comodel_name="control_seccion.contenido",string="Tema")
    logros = fields.Char(string="Logros",required=True,)
    debilidades = fields.Char(string='Debilidades',required=True)
    plan_id = fields.Many2one(comodel_name="control_seccion.planificacion")

    @api.onchange('tema','plan_id')
    def onchange_tema(self):
        context = self._context.copy()
        list_contents = []
        list_no_contents = []
        if('plan' in context):
            if('ind' in context):
                for indicadores in context['ind']:
                    if(len(indicadores)==3):
                        continue
                    if(type(indicadores[2]) == bool):
                        if(indicadores[0] == 4):
                            indi = self.env['control_seccion.ind_template'].search([('id','=',indicadores[1])]).tema.id
                            if(indi not in list_no_contents):
                                list_no_contents.append(indi)    
                        continue
                    if('tema' in indicadores[2]):
                        if(indicadores[2]['tema'] not in list_no_contents):
                            list_no_contents.append(indicadores[2]['tema'])

            for planes in context['plan']:
                if(len(planes)==3):
                    continue
                if(type(planes[2]) == bool):
                    if(planes[0]==4):
                        plans = self.env['control_seccion.planificacion_line'].search([('id','=',planes[1])]).contenido.id
                        if(plans not in list_contents and plans not in list_no_contents):
                            list_contents.append(plans)                    
                    continue
                if('contenido' in planes[2]):
                    if(planes[2]['contenido'] not in list_contents and planes[2]['contenido'] not in list_no_contents):
                        list_contents.append(planes[2]['contenido'])

        return {'domain':{'tema':[('id', 'in', list_contents)]}}

class indicador_principal(models.Model):
    _name = "control_seccion.ind_main"

    materia_alumno_id = fields.Many2one(comodel_name="control_seccion.materia_alumno")
    tema = fields.Many2one(comodel_name="control_seccion.contenido",string="Tema")
    logros = fields.Char(string="Logros",required=True,readonly=True)
    debilidades = fields.Char(string='Debilidades',required=True,readonly=True)
    check = fields.Boolean(default=False)
    check2 = fields.Boolean(default=False)

    @api.constrains('check','check2')
    def _msg_checks(self):
        for x in self:
            if(x.check and x.check2):
                raise ValidationError('Solo debe selecionar una opcion')

class materias_lapso(models.Model):
    _name = "control_seccion.materia_alumno"

    materia = fields.Many2one(comodel_name="control_seccion.materias",
        string="Materia",readonly=True, )
    alumno_id = fields.Many2one(comodel_name="control_seccion.alumnos_lapso",
        readonly=True,string="Alumno")
    indicadores = fields.One2many(comodel_name="control_seccion.ind_main",
        inverse_name="materia_alumno_id")
    notas = fields.One2many(comodel_name="control_seccion.notas_main",
        inverse_name="materia",string="Notas")

    @api.multi
    def asignar_indicador(self):
        if(len(self.notas)>0):
            porcent = 0
            temas ={}
            secci = self.notas[0].seccion.max_exam
            for x in self.notas:        
                pocent += x.porcentaje
                if(x.contenido.id not in temas):
                    temas[x.contenido.id] = (x.nota,1)
                else:
                    temas[x.contenido.id][0] += x.nota
                    temas[x.contenido.id][1] += 1 

            if(porcent == 100):
                min_lograr = self.env['control_seccion.planificacion'].search(
                    [('materia','=',self.materia.materia.id),('lapso','=',self.alumno_id.lapso.id)],limit=1).min_logro
                for values in self.indicadores:            
                    if(temas[values.tema.id][0]/temas[values.tema.id][1] >= min_lograr 
                        and temas[values.tema.id][0]/temas[values.tema.id][1] <= secci):
                        values.write({'check':True})
                    else:
                        values.write({'check2':True})

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id, values.materia.materia + ' ' + 
                str(values.materia.grado.grado) + ' ' + values.materia.grado.nivel))
        return res

    @api.multi
    def crear_indicadores(self):
        for x in self:
            lapso = x.alumno_id.lapso.id
            indicadores_base = self.env['control_seccion.planificacion'].search([('lapso','=',lapso),('materia','=',x.materia)]).indicador
            for y in indicadores_base:
                x.indicadores += x.indicadores.new({
                    'tema': y.tema.id,
                    'logros': y.logros,
                    'debilidades': y.debilidades,
                    'materia_alumno_id': x.id
                })

class alumnos_lapsos(models.Model):
    _name = "control_seccion.alumnos_lapso"
    _rec_name = "alumnos_ids"

    boletin_id = fields.Many2one(comodel_name="control_seccion.boletin")
    alumnos_ids = fields.Many2one(comodel_name="control_seccion.estudiantes",
        required=True,readonly=True)
    lapso = fields.Many2one(comodel_name="control_seccion.lapso",required=True)
    materia = fields.One2many(comodel_name="control_seccion.materia_alumno",
        inverse_name="alumno_id")

    @api.multi
    def crear_materias(self):
        for x in self:
            for y in x.boletin_id.seccion.materia:
                x.materia += x.materia.new({
                    'materia':y.id,
                    'alumno_id':x.id
                })

class lapsos(models.Model):
    _name = 'control_seccion.lapso'
    _rec_name = "nro_lapso"

    nro_lapso = fields.Integer(string="Nro de Lapso",required=True,)
    boletin_id = fields.Many2one(comodel_name="control_seccion.boletin")
    alumnos_ids = fields.One2many(comodel_name="control_seccion.alumnos_lapso",
        inverse_name="lapso")
    plan_ids = fields.One2many(comodel_name="control_seccion.planificacion",
        inverse_name="lapso")
    state= fields.Selection(selection=[('begin','Lapso iniciado'),('ending','Lapso finalizado')])

    @api.onchange('nro_lapso')
    def onchange_plan_ids(self):
        for x in self:
            if(len(x.plan_ids) == 0):
                for y in x.boletin_id.seccion.materia:
                    x.plan_ids += x.plan_ids.new({
                        'lapso': x.id,
                        'materia': y.id
                    })

            if(len(x.alumnos_ids) == 0):
                for y in x.boletin_id.seccion.alumnos:
                    nuevo_alumno = x.alumnos_ids.new({
                        'boletin_id': x.boletin_id.id,
                        'alumnos_ids': y.id,
                        'lapso': x.id
                    })
                    x.alumnos_ids += nuevo_alumno
                    nuevo_alumno.crear_materias()

class notas_template(models.TransientModel):
    _name = 'control_seccion.notas_template'

    seccion = fields.Many2one(comodel_name="control_seccion.seccion",
        string="Seccion",domain=[('state','=','begin'), ],required=True,)
    materia = fields.Many2one(comodel_name="control_seccion.materias",
        string="Materia",required=True,)  
    lapso = fields.Many2one(comodel_name="control_seccion.lapso",
        string="Lapso",required=True,)
    plan_id = fields.Many2one(comodel_name="control_seccion.planificacion_line",
        string="Contenido",required=True,)
    notas = fields.Many2many(comodel_name="control_seccion.notas_main",string='Notas',required=True,)

    @api.onchange('seccion')
    def onchange_seccion(self):
        list_mate = []
        list_lapso = []
        if(self.seccion.id):
            for x in self.seccion.materia:
                list_mate.append(x.id)
            boletin = self.env['control_seccion.lapso'].search([('id','=',self.env['control_seccion.boletin'].search([('seccion','=',self.seccion.id)]).id),('state','=','begin')])
            for x in boletin:
                list_lapso.append(x.id)
        return {'domain':{'materia':[('id','=',list_mate)],'lapso':[('id','=',list_lapso)]}}

    @api.onchange('materia','lapso')
    def onchange_matelap(self):
        list_plan = []
        if(self.materia.id and self.lapso.id):
            plan_for = self.env['control_seccion.planificacion'].search([('materia','=',self.materia.id),('lapso','=',self.lapso.id)]).lineas_plan
            if(type(plan_for) != bool and len(plan_for) > 0):
                for planes in plan_for:
                    list_plan.append(planes.id)
        return {'domain':{'plan_id':[('id','=',list_plan)]}}

    @api.onchange('plan_id')
    def onchange_plan_id(self):
        alumnos = self.env['control_seccion.alumnos_lapso'].search(
            [('lapso','=',self.lapso.id)])
        self.plan_id = self.env["control_seccion.planificacion_line"]                 
        for x in alumnos:
            vals = {
               'alumno':x.id,
               'seccion':self.seccion.id,
               'plan_id':self.plan_id.id,
               'materia':self.env['control_seccion.materia_alumno'].search(
                [('materia','=',self.materia.id),('alumnos_ids','=',x.id)],limit=1).id     
            }
            nota_alum = self.plan_id.new(vals)
            plan_id += nota_alum

    @api.model
    def create(self,vals):
        res = super(notas_template,self).create(vals)
        lapso = self.env['control_seccion.lapsos'].search([('id','=',vals['lapso'])]).alumnos_ids
            for x in lapso:
                for m in x.materia:
                    if(len(self.search([('seccion','=',vals['seccion'])])) == 1):
                        m.crear_indicadores()
                    m.asignar_indicador()
        self.env['control_seccion.planificacion_line'].search([('id','=',vals['plan_id'])],limit=1).write({'check':True})       
        return res

class notas_main(models.Model):
    _name = "control_seccion.notas_main"

    plan_id = fields.Many2one(comodel_name="control_seccion.planificacion_line",
        string="Planificacion")
    contenido = fields.Many2one(comodel_name="control_seccion.contenido",
        string="Contenido",store=True,compute="get_percent",readonly=True)
    porcentaje = fields.Integer(string="Porcentaje",store=True,compute="get_percent",readonly=True)
    alumno = fields.Many2one(comodel_name="control_seccion.alumnos_lapso",readonly=True,required=True)
    materia = fields.Many2one(comodel_name="control_seccion.materia_alumno",
        string="Materia",readonly=True,required=True,)
    seccion = fields.Many2one(comodel_name="control_seccion.seccion",
        string="Seccion",domain=[('state','=','begin'), ],required=True,readonly=True,)
    nota = fields.Integer(string="Nota",)
    nota_total = fields.Integer(string="Nota total",store=True,compute="get_nota",default=0)

    @api.onchange('nota')
    def onchange_nota(self):
        if not (self.nota >= 0 and self.nota <= self.seccion.max_exam):
            self.nota = 0

    @api.depends('porcentaje','nota')
    def get_nota(self):
        for x in self:
            if(x.nota >= 0 and x.nota <= x.seccion.max_exam):
                x.nota_total = x.nota * (x.porcentaje/100)
            else:
                x.nota_total = 0

    @api.depends('plan_id')
    def get_percent(self):
        for x in self:
            x.contenido = x.plan_id.contenido.id
            x.porcentaje = x.plan_id.porcentaje
