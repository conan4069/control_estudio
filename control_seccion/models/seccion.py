#!/usr/bin/env python
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class control_estudiantes(models.Model):
    _name = 'control_seccion.estudiantes'
    _order = "identification asc"

    name = fields.Char(string='Nombre completo',size=256,required=True,)
    last_name = fields.Char(string='Apellido completo',size=256,required=True,)
    identification = fields.Char(string='Cedula/identificador',required=True)
    
    _sql_constraints = [
        ('identification_uniq', 'UNIQUE (identification)',
          'Disculpe, esta cedula o indicador ya ha sido asignado a un estudiante')
    ]

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id,str(values.name) + ' ' + values.last_name))
        return res

class control_grado(models.Model):
    _name = 'control_seccion.grado'

    grado = fields.Integer(string='Grado/ano',required=True,)
    nivel = fields.Selection(selection=[('grado','Grado'),('anio','Ano'),
        ('semestre','Semestre'),('trimestre','Trimestre')],
        string='Nivel',default='grado',required=True)

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id,str(values.grado) + ' ' + values.nivel))
        return res

class control_materias(models.Model):
    _name = 'control_seccion.materias'

    materia = fields.Char(string='Nombre de la materia',required=True,)
    grado = fields.Many2one(comodel_name='control_seccion.grado',string='Grado')

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id, values.materia + ' ' + 
                str(values.grado.grado) + ' ' + values.grado.nivel))
        return res

    @api.multi
    @api.constrains('materia','grado')
    def _check_materia(self):
        if(len(self.search([('materia','=',self.materia),
            ('grado','=',self.grado.id)]))>1):
            raise ValidationError("La materia %s para %s %s ya existe, por favor no repita materias"%(self.materia,str(self.grado.grado),self.grado.nivel))

class control_seccion(models.Model):
    _name = 'control_seccion.seccion'

    seccion = fields.Char(string='Seccion',required=True,)
    grado = fields.Many2one(comodel_name='control_seccion.grado',
        string='Grado',required=True,)
    periodo = fields.Char(string='Periodo',required=True,)
    materia = fields.Many2many(comodel_name='control_seccion.materias',
        string='Materias',required=True)
    alumnos = fields.Many2many(comodel_name='control_seccion.estudiantes',
        string='Alumnos',required=True,)
    max_lapso = fields.Integer(string="Lapsos",
        help="Con esto se indica el maximo de periodos/cortes/lapsos",default=3,required=True,)
    max_exam = fields.Integer(string='Mayor nota',
        help="Esto indica el valor maximo que se puede sacar en una prueba",default=20,required=True,)
    state = fields.Selection(selection=[('draft','Borrador'),
        ('begin','Periodo iniciado'),('ending','Periodo finalizado')],default="draft",string="Estado",readonly=True,)

    @api.multi
    def name_get(self):
        res = []
        for values in self:
            res.append((values.id, str(values.grado.grado) + ' ' +
             values.grado.nivel + ' Seccion ' + 
            values.seccion + ' Periodo '+ values.periodo))
        return res

    @api.multi
    def fin_periodo(self):
        self.write({'state':'ending'})

    @api.model
    def create(self,vals):
        res = super(control_seccion,self).create(vals)
        boletin = self.env['control_seccion.boletin'].create({
            'seccion': res.id,
        })
        res.write({'state':'begin'})
        return res