# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from dateutil import parser
from collections import OrderedDict
from datetime import timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    mgmt_company = fields.Many2one(related="partner_id.management_company_type_id", store=True)
    subscription_line_ids = fields.Many2many('sale.subscription.line', 'account_id', string="Subscription Lines")
    invoices_month_year = fields.Char(string="Invoicing Period", compute="set_invoices_month", store=False)

    def _move_autocomplete_invoice_lines_values(self):
        ''' This method recomputes dynamic lines on the current journal entry that include taxes, cash rounding
        and payment terms lines.
        Default Behaviour : it's set product name in label field
        changed Behaviour : it's not updating product name in label while updating draft invoice lines for downsell cases

        '''
        self.ensure_one()

        line_currency = self.currency_id if self.currency_id != self.company_id.currency_id else False
        for line in self.line_ids:
            # Do something only on invoice lines.
            if line.exclude_from_invoice_tab:
                continue

            # Shortcut to load the demo data.
            # Doing line.account_id triggers a default_get(['account_id']) that could returns a result.
            # A section / note must not have an account_id set.
            if not line._cache.get('account_id') and not line.display_type and not line._origin:
                line.account_id = line._get_computed_account()
                if not line.account_id:
                    if self.is_sale_document(include_receipts=True):
                        line.account_id = self.journal_id.default_credit_account_id
                    elif self.is_purchase_document(include_receipts=True):
                        line.account_id = self.journal_id.default_debit_account_id
            if line.product_id and not line._cache.get('name') and not self._context.get('name', False):
                line.name = line._get_computed_name()

            # Compute the account before the partner_id
            # In case account_followup is installed
            # Setting the partner will get the account_id in cache
            # If the account_id is not in cache, it will trigger the default value
            # Which is wrong in some case
            # It's better to set the account_id before the partner_id
            # Ensure related fields are well copied.
            line.partner_id = self.partner_id.commercial_partner_id
            line.date = self.date
            line.recompute_tax_line = True
            line.currency_id = line_currency

        self.line_ids._onchange_price_subtotal()
        self._recompute_dynamic_lines(recompute_all_taxes=True)

        values = self._convert_to_write(self._cache)
        values.pop('invoice_line_ids', None)
        return values

    def post(self):
        res = super(AccountMove, self).post()
        sequence = self.env.ref("clx_invoice_policy.sequence_greystar_sequence")
        for recrod in self:
            if res and recrod.partner_id and recrod.partner_id.management_company_type_id and 'Greystar' in recrod.partner_id.management_company_type_id.name and sequence:
                recrod.name = sequence.next_by_code('greystar.sequence')
        return res

    def set_invoices_month(self):
        start_date = False
        for record in self:
            if record.invoice_line_ids:
                for line in record.invoice_line_ids:
                    if "Invoicing period" in line.name:
                        name = line.name.split(':')[-1]
                        name = name.split('-')
                        start_date = parser.parse(name[0])
                if start_date:
                    record.invoices_month_year = start_date.strftime("%b, %Y")
                else:
                    record.invoices_month_year = " "

    def unlink(self):
        for record in self:
            if record.invoice_origin:
                for inv_line in record.invoice_line_ids:
                    if inv_line.subscription_lines_ids:
                        name = inv_line.name.split(':')
                        name = name[-1].split('-')
                        start_date = parser.parse(name[0])
                        end_date = parser.parse(name[-1])
                        if start_date and end_date:
                            for sub in inv_line.subscription_lines_ids:
                                if not sub.end_date:
                                    sub.invoice_start_date = start_date.date()
                                    sub.invoice_end_date = end_date.date()
                                elif sub.end_date:
                                    month_count = len(
                                        OrderedDict(((sub.end_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                                    range((start_date.date() - sub.end_date).days)))
                                    if month_count == 1 and start_date.date() > sub.end_date:
                                        sub.invoice_start_date = sub.start_date
                                        sub.invoice_end_date = sub.end_date
                                    elif sub.start_date > start_date.date():
                                        sub.invoice_start_date = sub.start_date
                                        sub.invoice_end_date = sub.end_date
                                    else:
                                        sub.invoice_start_date = start_date.date()
                                        sub.invoice_end_date = end_date.date()
        return super(AccountMove, self).unlink()

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        if self.invoice_origin:
            for inv_line in self.invoice_line_ids:
                if inv_line.subscription_lines_ids:
                    name = inv_line.name.split(':')
                    name = name[-1].split('-')
                    start_date = parser.parse(name[0])
                    end_date = parser.parse(name[-1])
                    if start_date and end_date:
                        for sub in inv_line.subscription_lines_ids:
                            if not sub.end_date:
                                sub.invoice_start_date = start_date.date()
                                sub.invoice_end_date = end_date.date()
                            elif sub.end_date:
                                month_count = len(
                                    OrderedDict(((sub.end_date + timedelta(_)).strftime("%B-%Y"), 0) for _ in
                                                range((start_date.date() - sub.end_date).days)))
                                if month_count == 1 and start_date.date() > sub.end_date:
                                    sub.invoice_start_date = sub.start_date
                                    sub.invoice_end_date = sub.end_date
                                elif sub.start_date > start_date.date():
                                    sub.invoice_start_date = sub.start_date
                                    sub.invoice_end_date = sub.end_date
                                else:
                                    sub.invoice_start_date = start_date.date()
                                    sub.invoice_end_date = end_date.date()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    category_id = fields.Many2one('product.category', string="Category")
    subscription_ids = fields.Many2many(
        'sale.subscription', string="Subscription(s)")
    subscription_lines_ids = fields.Many2many('sale.subscription.line', string="Subscriptions Lines")

    management_fees = fields.Float(string="Management Fees")
    retail_price = fields.Float(string="Retails Price")
    wholesale = fields.Float(string="Wholsesale")
    description = fields.Char(string="Description")
