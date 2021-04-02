# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
{
    'name': 'CLX Task Management',
    'version': '13.3.0.1.11',
    'summary': 'CLX Task Management',
    'sequence': 1,
    'description': """ CLX Task Management """,
    'category': '',
    'author': 'CLx Media',
    'website': 'https://conversionlogix.com/',
    'depends': ['sale',
                'project',
                'sale_management',
                'portal',
                'sale_crm',
                'contact_modification',
                'product'
                ],
    'data': [
        'security/task_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/task_stages.xml',
        'data/team_data.xml',
        'data/main_task.xml',
        'data/mail_template.xml',
        'views/request_form_template.xml',
        'views/request_form_portal_views.xml',
        'views/res_config_settings_views.xml',
        'views/main_task_views.xml',
        'views/team_views.xml',
        'views/sub_task_views.xml',
        'views/request_form_views.xml',
        'views/project_views.xml',
        'views/sale_order_views.xml',
        'views/product_product_views.xml',
        'views/task_proof_return_views.xml',
        # 'views/product_category_views.xml',
        'views/sale_subscription_line_views.xml',
        'wizard/task_cancel_warning_wizard_views.xml',
        'wizard/project_excel_report_views.xml',
        'views/assets.xml'
    ],
    'demo': [
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
