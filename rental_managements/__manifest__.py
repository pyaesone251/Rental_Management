# -*- coding: utf-8 -*-
{
    'name': 'Equipment Rental Management',
    'version': '19.0.1.0.0',
    'category': 'Services/Rental',
    'summary': 'Learn Odoo ORM, Wizards and QWeb Reports by building a rental system',
    'author': 'Your Name',
    'website': 'https://www.example.com',
    'license': 'LGPL-3',

    'depends': ['base', 'mail'],

    'data': [
        # 1. Security
        'security/ir.model.access.csv',

        # 2. Sequence / Base Data
        'data/rental_sequence.xml',

        # 3. Views (Order is critical: Order action must be before Equipment view)
        'views/rental_order_views.xml',
        'views/rental_equipment_views.xml',
        'views/rental_menus.xml',

        # 4. Wizard Views
        'wizard/rental_return_wizard_views.xml',

        # 5. Reports
        'report/rental_order_report.xml',
        'report/rental_order_templates.xml',
    ],

    'demo': [
        'demo/rental_demo.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
}