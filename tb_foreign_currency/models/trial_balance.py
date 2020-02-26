# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, _, fields
from datetime import datetime, timedelta
from odoo.tools.misc import format_date

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    # TODO saas-17: remove the try/except to directly import from misc
    import xlsxwriter
import io
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, pycompat



class report_account_coa(models.AbstractModel):
    _inherit = "account.coa.report"
    
    filter_currencys = True
        
    def _build_options(self, previous_options=None):
        res = super(report_account_coa, self)._build_options(previous_options)
        if self.filter_currencys :
            currencies = self.env['res.currency'].search([])
            res['currenciess'] = [{'id': c.id, 'name': c.name, 'selected': False} for c in currencies]
            if 'curr' in self._context:
                for c in res['currenciess']:
                    if c['id'] == self._context.get('curr'):
                        c['selected'] = True
            else:
                for c in res['currenciess']:
                    if c['id'] == self.env.user.company_id.currency_id.id:
                        c['selected'] = True
            res['currencys'] = True
        return res
    
    @api.model
    def create_hierarchy(self, lines):
        """This method is called when the option 'hiearchy' is enabled on a report.
        It receives the lines (as computed by get_lines()) in argument, and will add
        a hiearchy in those lines by using the account.group of accounts. If not set,
        it will fallback on creating a hierarchy based on the account's code first 3
        digits.
        """
        # Avoid redundant browsing.
        if 'curr' in self._context:
            cur = self.env['res.currency'].browse(self._context.get('curr'))
            if cur != self.env.user.company_id.currency_id:
                accounts_cache = {}
        
                MOST_SORT_PRIO = 0
                LEAST_SORT_PRIO = 99
        
                # Retrieve account either from cache, either by browsing.
                def get_account(id):
                    if id not in accounts_cache:
                        accounts_cache[id] = self.env['account.account'].browse(id)
                    return accounts_cache[id]
        
                # Create codes path in the hierarchy based on account.
                def get_account_codes(account):
                    # A code is tuple(sort priority, actual code)
                    codes = []
                    if account.group_id:
                        group = account.group_id
                        while group:
                            code = '%s %s' % (group.code_prefix or '', group.name)
                            codes.append((MOST_SORT_PRIO, code))
                            group = group.parent_id
                    else:
                        # Limit to 3 levels.
                        code = account.code[:3]
                        while code:
                            codes.append((MOST_SORT_PRIO, code))
                            code = code[:-1]
                    return list(reversed(codes))
        
                # Add the report line to the hierarchy recursively.
                def add_line_to_hierarchy(line, codes, level_dict, depth=None):
                    # Recursively build a dict where:
                    # 'children' contains only subcodes
                    # 'lines' contains the lines at this level
                    # This > lines [optional, i.e. not for topmost level]
                    #      > children > [codes] "That" > lines
                    #                                  > metadata
                    #                                  > children
                    #      > metadata(depth, parent ...)
        
                    if not codes:
                        return
                    if not depth:
                        depth = line.get('level', 1)
                    level_dict.setdefault('depth', depth)
                    level_dict.setdefault('parent_id', line.get('parent_id'))
                    level_dict.setdefault('children', {})
                    code = codes[0]
                    codes = codes[1:]
                    level_dict['children'].setdefault(code, {})
        
                    if codes:
                        add_line_to_hierarchy(line, codes, level_dict['children'][code], depth=depth + 1)
                    else:
                        level_dict['children'][code].setdefault('lines', [])
                        level_dict['children'][code]['lines'].append(line)
        
                # Merge a list of columns together and take care about str values.
                def merge_columns(columns):
                    return ['n/a' if any(isinstance(i, str) for i in x) else sum(x) for x in pycompat.izip(*columns)]
        
                # Get_lines for the newly computed hierarchy.
                def get_hierarchy_lines(values, depth=1):
                    lines = []
                    sum_sum_columns = []
                    for base_line in values.get('lines', []):
                        lines.append(base_line)
                        sum_sum_columns.append([c.get('no_format_name', c['name']) for c in base_line['columns']])
        
                    # For the last iteration, there might not be the children key (see add_line_to_hierarchy)
                    for key in sorted(values.get('children', {}).keys()):
                        sum_columns, sub_lines = get_hierarchy_lines(values['children'][key], depth=values['depth'])
                        header_line = {
                            'id': 'hierarchy',
                            'name': key[1],  # second member of the tuple
                            'unfoldable': False,
                            'unfolded': True,
                            'level': values['depth'],
                            'parent_id': values['parent_id'],
                            'columns': [{'name': self.format_value(c,cur) if not isinstance(c, str) else c} for c in sum_columns],
                        }
                        if key[0] == LEAST_SORT_PRIO:
                            header_line['style'] = 'font-style:italic;'
                        lines += [header_line] + sub_lines
                        sum_sum_columns.append(sum_columns)
                    return merge_columns(sum_sum_columns), lines
        
                def deep_merge_dict(source, destination):
                    for key, value in source.items():
                        if isinstance(value, dict):
                            # get node or create one
                            node = destination.setdefault(key, {})
                            deep_merge_dict(value, node)
                        else:
                            destination[key] = value
        
                    return destination
        
                # Hierarchy of codes.
                accounts_hierarchy = {}
        
                new_lines = []
                no_group_lines = []
                # If no account.group at all, we need to pass once again in the loop to dispatch
                # all the lines across their account prefix, hence the None
                for line in lines + [None]:
                    # Only deal with lines grouped by accounts.
                    # And discriminating sections defined by account.financial.html.report.line
                    is_grouped_by_account = line and line.get('caret_options') == 'account.account'
                    if not is_grouped_by_account or not line:
        
                        # No group code found in any lines, compute it automatically.
                        no_group_hierarchy = {}
                        for no_group_line in no_group_lines:
                            codes = [(LEAST_SORT_PRIO, _('(No Group)'))]
                            if not accounts_hierarchy:
                                account = get_account(no_group_line.get('id'))
                                codes = get_account_codes(account)
                            add_line_to_hierarchy(no_group_line, codes, no_group_hierarchy)
                        no_group_lines = []
        
                        deep_merge_dict(no_group_hierarchy, accounts_hierarchy)
        
                        # Merge the newly created hierarchy with existing lines.
                        if accounts_hierarchy:
                            new_lines += get_hierarchy_lines(accounts_hierarchy)[1]
                            accounts_hierarchy = {}
        
                        if line:
                            new_lines.append(line)
                        continue
        
                    # Exclude lines having no group.
                    account = get_account(line.get('id'))
                    if not account.group_id:
                        no_group_lines.append(line)
                        continue
        
                    codes = get_account_codes(account)
                    add_line_to_hierarchy(line, codes, accounts_hierarchy)
        
                return new_lines
        return super(report_account_coa, self).create_hierarchy(lines)
    def _post_process(self, grouped_accounts, initial_balances, options, comparison_table):
        res = super(report_account_coa, self)._post_process(grouped_accounts, initial_balances, options, comparison_table)
        if 'curr' in self._context:
            cur = self.env['res.currency'].browse(self._context.get('curr'))
            if cur != self.env.user.company_id.currency_id:
                lines = []
                context = self.env.context
                company_id = context.get('company_id') or self.env.user.company_id
                title_index = ''
                sorted_accounts = sorted(grouped_accounts, key=lambda a: a.code)
                zero_value = ''
                sum_columns = [0,0,0,0]
                for period in range(len(comparison_table)):
                    sum_columns += [0, 0]
                for account in sorted_accounts:
                    #skip accounts with all periods = 0 and no initial balance
                    non_zero = False
                    for p in range(len(comparison_table)):
                        if (grouped_accounts[account][p]['debit'] or grouped_accounts[account][p]['credit']) or\
                            not company_id.currency_id.is_zero(initial_balances.get(account, 0)):
                            non_zero = True
                    if not non_zero:
                        continue
        
                    initial_balance = initial_balances.get(account, 0.0)
                    
                    initial_balance = cur._compute(self.env.user.company_id.currency_id,cur,initial_balance)
                    
                    sum_columns[0] += initial_balance if initial_balance > 0 else 0
                    sum_columns[1] += -initial_balance if initial_balance < 0 else 0
                    cols = [
                        {'name': initial_balance > 0 and self.format_value(initial_balance,cur) or zero_value, 'no_format_name': initial_balance > 0 and initial_balance or 0},
                        {'name': initial_balance < 0 and self.format_value(-initial_balance,cur) or zero_value, 'no_format_name': initial_balance < 0 and abs(initial_balance) or 0},
                    ]
                    total_periods = 0
                    for period in range(len(comparison_table)):
                        amount = grouped_accounts[account][period]['balance']
                        debit = grouped_accounts[account][period]['debit']
                        credit = grouped_accounts[account][period]['credit']
                        
                        amount = cur._compute(self.env.user.company_id.currency_id,cur,amount)
                        debit = cur._compute(self.env.user.company_id.currency_id,cur,debit)
                        credit = cur._compute(self.env.user.company_id.currency_id,cur,credit)
                        
                        total_periods += amount
                        cols += [{'name': debit > 0 and self.format_value(debit,cur) or zero_value, 'no_format_name': debit > 0 and debit or 0},
                                 {'name': credit > 0 and self.format_value(credit,cur) or zero_value, 'no_format_name': credit > 0 and abs(credit) or 0}]
                        # In sum_columns, the first 2 elements are the initial balance's Debit and Credit
                        # index of the credit of previous column generally is:
                        p_indice = period * 2 + 1
                        sum_columns[(p_indice) + 1] += debit if debit > 0 else 0
                        sum_columns[(p_indice) + 2] += credit if credit > 0 else 0
        
                    total_amount = initial_balance + total_periods
                    sum_columns[-2] += total_amount if total_amount > 0 else 0
                    sum_columns[-1] += -total_amount if total_amount < 0 else 0
                    cols += [
                        {'name': total_amount > 0 and self.format_value(total_amount,cur) or zero_value, 'no_format_name': total_amount > 0 and total_amount or 0},
                        {'name': total_amount < 0 and self.format_value(-total_amount,cur) or zero_value, 'no_format_name': total_amount < 0 and abs(total_amount) or 0},
                        ]
                    lines.append({
                        'id': account.id,
                        'name': account.code + " " + account.name,
                        'columns': cols,
                        'unfoldable': False,
                        'caret_options': 'account.account',
                    })
                lines.append({
                     'id': 'grouped_accounts_total',
                     'name': _('Total'),
                     'class': 'o_account_reports_domain_total',
                     'columns': [{'name': self.format_value(v,cur)} for v in sum_columns],
                     'level': 0,
                })
                return lines
        return res
    
    def get_pdf(self, options, minimal_layout=True):
        for opt in options['currenciess']:
            if opt['selected'] and self.env['res.currency'].browse(opt['id']) != self.env.user.company_id.currency_id:
                return super(report_account_coa, self.with_context(curr = opt['id'])).get_pdf(options,minimal_layout)
        return super(report_account_coa, self).get_pdf(options,minimal_layout)
    
    def get_xlsx(self, options, response):
        for opt in options['currenciess']:
            if opt['selected'] and self.env['res.currency'].browse(opt['id']) != self.env.user.company_id.currency_id:
                return super(report_account_coa, self.with_context(curr = opt['id'])).get_xlsx(options,response)
        return super(report_account_coa, self).get_xlsx(options,response)

   