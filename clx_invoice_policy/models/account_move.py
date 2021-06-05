# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _
from dateutil import parser
from collections import OrderedDict
from datetime import timedelta
import calendar


class AccountMove(models.Model):
    _inherit = "account.move"

    mgmt_company = fields.Many2one(related="partner_id.management_company_type_id", store=True)
    subscription_line_ids = fields.Many2many("sale.subscription.line", "account_id", string="Subscription Lines")
    invoice_month_year = fields.Char(string="Invoicing Period")
    invoice_period_verbal = fields.Char(
        compute="compute_invoice_period_verbal", string="Invoice Period Verbal", store=False
    )

    related_contact_ids = fields.One2many(
        related="partner_id.contact_child_ids",
        string="Billing Contacts",
        store=False,
    )

    related_billing_contact_ids = fields.Many2many(
        "res.partner.clx.child", compute="compute_billing_contacts", string="Billing Contacts2", store=False
    )

    def compute_billing_contacts(self):
        billing_list = map(
            lambda item: item.id,
            filter(
                lambda contact: "Billing Contact" in contact.contact_type_ids.mapped("name"), self.related_contact_ids
            ),
        )
        self.related_contact_ids2 = [(6, 0, list(billing_list))]

    def post(self):
        res = super(AccountMove, self).post()
        sequence = self.env.ref("clx_invoice_policy.sequence_greystar_sequence")
        if (
            res
            and self.partner_id
            and self.partner_id.management_company_type_id
            and "Greystar" in self.partner_id.management_company_type_id.name
            and sequence
        ):
            self.name = sequence.next_by_code("greystar.sequence")
        return res

    @staticmethod
    def invoices_date_signature(date):
        return date.strftime("%Y-%m")

    def compute_invoice_period_verbal(self):
        for invoice in self:
            if invoice.invoice_month_year:
                year, day = invoice.invoice_month_year.split("-")
                # check for correct data
                if len(year) == 4 and len(day) == 2:
                    invoice.invoice_period_verbal = "%s %s" % (calendar.month_name[int(day)], year)
                else:
                    invoice.invoice_period_verbal = "-"
            else:
                invoice.invoice_period_verbal = "-"

    def unlink(self):
        for record in self:
            if record.invoice_origin:
                for inv_line in record.invoice_line_ids:
                    if inv_line.subscription_lines_ids:
                        name = inv_line.name.split(":")
                        name = name[-1].split("-")
                        start_date = parser.parse(name[0])
                        end_date = parser.parse(name[-1])
                        if start_date and end_date:
                            for sub in inv_line.subscription_lines_ids:
                                if not sub.end_date:
                                    sub.invoice_start_date = start_date.date()
                                    sub.invoice_end_date = end_date.date()
                                elif sub.end_date:
                                    month_count = len(
                                        OrderedDict(
                                            ((sub.end_date + timedelta(_)).strftime("%B-%Y"), 0)
                                            for _ in range((start_date.date() - sub.end_date).days)
                                        )
                                    )
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
                    name = inv_line.name.split(":")
                    name = name[-1].split("-")
                    start_date = parser.parse(name[0])
                    end_date = parser.parse(name[-1])
                    if start_date and end_date:
                        for sub in inv_line.subscription_lines_ids:
                            if not sub.end_date:
                                sub.invoice_start_date = start_date.date()
                                sub.invoice_end_date = end_date.date()
                            elif sub.end_date:
                                month_count = len(
                                    OrderedDict(
                                        ((sub.end_date + timedelta(_)).strftime("%B-%Y"), 0)
                                        for _ in range((start_date.date() - sub.end_date).days)
                                    )
                                )
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

    # rewriting the eamil sending function
    def action_invoice_sent(self, reminder=False):
        self.ensure_one()
        # template = self.env["mail.template"].sudo().search([("name", "=", "Invoice: Send by email")])

        template = self.env["mail.template"].sudo().search([("name", "=", "Invoice: CLX email template")])
        template_id = template.id
        contacts_billing = []
        for contact in self.partner_id.contact_child_ids:
            contacts_billing.append(contact.child_id.id)
        account_manager = self.partner_id.account_user_id.partner_id
        contacts_billing.append(account_manager.id)
        if template.lang:
            lang = template._render_template(template.lang, "account.move", self.ids[0])

        url = self.get_portal_url()

        access_action = self.with_context(force_website=True).get_access_action()
        is_online = access_action and access_action["type"] == "ir.actions.act_url"
        base_url = self.get_base_url()

        secure_url = self._get_share_url(redirect=True, signup_partner=True)
        if reminder:
            email_text = """ Attached is your recent invoice. Please review for dates of service and terms specific to your account.</p><p>To avoid interruption of your campaign(s) and/or other services such as Live Chat or The Conversion Cloud, we need to receive payment prior to the service date"""

        else:
            email_text = " To ensure your campaign runs as planned, please be reminded to ensure we receive payment by May 31, 2021. Payment in full is required to start or continue service. Attached is the invoice for your reference."

        ctx = {
            "tpl_partners_only": True,
            "default_model": "account.move",
            "default_res_id": self.ids[0],
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "default_partner_ids": [account_manager.id],
            "default_email_to": "",
            "default_reply_to": "",
            "mark_so_as_sent": True,
            "custom_layout": "mail.mail_notification_paynow",
            "proforma": self.env.context.get("proforma", False),
            "force_email": True,
            "model_description": self.with_context(lang=lang).type_name,
            "report_name": (self.name or "").replace("/", "_") + "_000",
            "default_allowed_partner_ids": contacts_billing,
            "secure_url": secure_url,
            "email_text": email_text,
        }
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": ctx,
        }

    def action_reminder_sent(self):
        return self.action_invoice_sent(True)

    # no status for mail sending
    def email_send_postprocess(self):
        return


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    category_id = fields.Many2one("product.category", string="Category")
    subscription_ids = fields.Many2many("sale.subscription", string="Subscription(s)")
    subscription_lines_ids = fields.Many2many("sale.subscription.line", string="Subscriptions Lines")

    management_fees = fields.Float(string="Management Fees")
    retail_price = fields.Float(string="Retails Price")
    wholesale = fields.Float(string="Wholsesale")
    description = fields.Char(string="Description")
