# -*- encoding: utf-8 -*-
{
    "name" : "AA - Journal Entry Reports",
    "version" : "12.0.1.0",
    'author' : 'ERP Cloud LLC',
    'website' : 'https://www.erpxcloud.com',
    "category" : "Accounting",
    "description": """
    - Journal Entry Report.
                        """,
    "depends" : ["base",'account'],
    "data" : [
                    "extra_account_reports.xml",
                    'views/journal_entries.xml',
            ],
    "installable": True
}
