# -*- coding: utf-8 -*-
{
    'name': "control_seccion",

    'summary': """
Permite realizar secciones, con sus respectivas materias""",

    'description': """
        Modulo para llevar control de notas indicativos de los alumnos
    """,

    'author': "Miguel Villamizar",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Estudiantil',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    
}
