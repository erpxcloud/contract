# -*- coding: utf-8 -*-
from . import models

def post_init_hook(cr, registry):
    from odoo.exceptions import Warning
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    if env.ref('base.module_gl_forign_currency') and env.ref('base.module_gl_forign_currency').state == 'installed':
            if env.ref('gl_forign_currency.search_template_analytic') and env.ref('gl_forign_currency.search_template_analytic').active:
                env.ref('tb_forign_currency.search_template_analytic').active = False