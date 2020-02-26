# -*- coding: utf-8 -*-
{
    'name': 'aa - Lebanon - Accounting',
    'version': '12.0.1.0',
    'category': 'Localization',
    'description': """
This is the base module to manage the accounting chart for Lebanon in Odoo.
==============================================================================
    """,
    'author': 'ERP Cloud LLC',
    'website': 'https://www.erpxcloud.com',
    'depends': ['account','l10n_multilang',],
    'data': [
        'data/account.group.csv',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/account_jo_coa_data.xml',
        'data/account_data.xml',
        'data/account_tax_template_data.xml',
        'data/res.lang.csv',
        'data/account_chart_template.xml'
    ],
}
