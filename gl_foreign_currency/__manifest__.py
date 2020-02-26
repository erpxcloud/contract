# -*- coding: utf-8 -*-
{
    'name': "AA - General Ledger In Foreign Currency",
    'summary': "Add filter currency on GL report. ",
    'description': """
    """,
    'author': "ERP Cloud LLC",
    'website': "https://www.erpxcloud.com",
    'category': 'Accounting',
    'version': '12.0.1.0',
    'depends': ['base','account','account_reports'],
    'installable': True,
    'auto_install': False,
    'data': [
        'view/general_ledger.xml',
        'view/data.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
