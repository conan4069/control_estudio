# -*- coding: utf-8 -*-
from odoo import fields,api,models
from odoo.exceptions import ValidationError

class boletin(models.Model):
    _name = 'control_seccion.boletin'
    _order = "seccion.id desc"

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

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id, values.materia.materia + ' ' + 
                str(values.materia.grado) + ' ' + str(values.lapso.nro_lapso)))
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

class tema (models.Model):
    _name = 'control_seccion.contenido'

    lapso = fields.Many2one(comodel_name="control_seccion.lapso")
    name = fields.Char(string="Contenido",required=True)

class indicador_template(models.Model):
    _name = "control_seccion.ind_template"

    tema = fields.Many2one(comodel_name="control_seccion.contenido",string="Tema")
    logros = fields.Char(string="Logros",required=True,)
    debilidades = fields.Char(string='Debilidades',required=True)
    min_logro = fields.Integer(string="Min. Logro",
        help="Indica el valor minimo para asumir que es un logro",default=15)
    plan_id = fields.Many2one(comodel_name="control_seccion.planificacion")

class indicador_principal(models.Model):
    _name = "control_seccion.ind_main"

    materia_alumno_id = fields.Many2one(comodel_name="control_seccion.materia_alumno")
    tema = fields.Many2one(comodel_name="control_seccion.contenido",string="Tema")
    logros = fields.Char(string="Logros",required=True,)
    debilidades = fields.Char(string='Debilidades',required=True)
    check = fields.Boolean(default=False)
    check2 = fields.Boolean(default=False)

    @api.constrains('check','check2'):
    def _msg_checks(self):
        for x in self:
            if(x.check and x.check2):
                raise ValidationError('Solo debe selecionar una opcion')

class materias_lapso(models.Model):
    _name = "control_seccion.materia_alumno"

    materia = fields.Many2one(comodel_name="control_seccion.materias",
        string="Materia",readonly=True, )
    alumno_id = fields.Many2one(comodel_name="control_seccion.alumnos_lapso",
        readonly=True,string="Alunmo")
    indicadores = fields.One2many(comodel_name="control_seccion.ind_main",
        inverse_name="materia_alumno_id")

    @api.multi
    def crear_indicadores(self):
        for x in self:
            lapso = x.alumno_id.lapso.id
            indicadores_base = self.env['control_seccion.ind_template'].search([('lapso','=',lapso),('materia','=',x.materia)])
            for y in indicadores_base:
                x.indicadores += x.indicadores.new({
                    'tema': y.tema.id,
                    'logros': y.logros,
                    'debilidades': y.debilidades,
                    'materia_alumno_id': x.id
                })

class alumnos_lapso(models.Model):
    _name = "control_seccion.alumnos_lapso"

    boletin_id = fields.Many2one(comodel_name="control_seccion.boletin")
    alumnos_ids = fields.Many2one(comodel_name="control_seccion.estudiantes",
        required=True)
    lapso = fields.Many2one(comodel_name="control_seccion.lapso",required=True)
    materia = fields.One2many(comodel_name="control_seccion.materia_alumno",
        inverse_name="alumno_lapso")

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