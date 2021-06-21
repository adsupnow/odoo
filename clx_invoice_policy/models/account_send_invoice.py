# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import fields, models, api, _

class AccountSendInvoice(models.TransientModel):
    _inherit = 'account.invoice.send'

    # def send_and_print_action(self):
    #     for rec in self.invoice_ids.filtered(lambda x: x.state not in ['cancel','email_sent'] ):
    #         rec.state = 'email_sent'
    #     res = super(AccountSendInvoice, self).send_and_print_action()
    #     return res

    @api.model
    def default_get(self, fields):
        res = super(AccountSendInvoice, self).default_get(fields)
        if not res.get('allowed_partner_ids'):
            res['allowed_partner_ids'] = self.get_allowed_ids().ids
        if not res.get('partner_ids') and res.get('allowed_partner_ids'):
            res['partner_ids'] = self.with_context(type_name='Billing Contact').get_allowed_ids().ids
        return res

    def get_allowed_ids(self):
        if self._context.get('type_name'):
            contacts = self.env["account.move"].browse(self._context.get('active_ids',self.res_id)).mapped(
                'partner_id')
            return contacts.mapped('account_user_id').mapped('partner_id') + contacts.contacts_to_notify(group_name=self._context.get('type_name'))
        return self.env["account.move"].browse(self._context.get('active_ids',self.res_id)).mapped(
                'partner_id').contacts_to_notify()

    allowed_partner_ids = fields.One2many("res.partner", compute="get_allowed_ids", string="List of contacts")

    def clx_action_send_mail(self):
        prepeared_values = {
            "body_html": self.body,
            "attachment_ids": self.attachment_ids,
            "recipient_ids": False,
            "subject": self.subject,
            "email_from": self.email_from,
            "reply_to": self.reply_to,
        }
        array_of_recipients = []

        if self.partner_ids:
            array_of_recipients += self.partner_ids.mapped("email")

        for recipient in array_of_recipients:
            prepeared_values["email_to"] = recipient.strip()
            Mail = self.env["mail.mail"].create(prepeared_values)
            object_source = self.env[self.model].browse(self.res_id)
            object_source.email_send_postprocess()
            Mail.send()

        return {"type": "ir.actions.act_window_close", "infos": "mail_sent"}