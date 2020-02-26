# -*- coding: utf-8 -*-
{
    'name': "AA - Trial Balance In Foreign Currency",
    'summary': " ",
    'description': """
    """,
    'author': "ERP Cloud LLC",
    'website': "https://www.erpxcloud.com",
    'category': 'Accounting',
    'version': '11.0.1.0',
    'depends': ['base','account','account_reports'],
    'installable': True,
    'auto_install': False,
    'data': [
        'view/trial_balance.xml',
        'view/data.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
