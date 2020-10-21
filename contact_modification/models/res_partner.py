# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from ast import literal_eval

from odoo import api, fields, models


class ContactType(models.Model):
    _name = "contact.type"
    _description = "Contact Type"

    name = fields.Char('Name')
    nik = fields.Char('Nik')


class Partner(models.Model):
    _inherit = "res.partner"

    def _dafault_parent(self):
        return [(6, 0, self.parent_id.ids)]

    def _compute_task_count(self):
        fetch_data = self.env['project.task'].read_group([
            ('partner_id', 'in', self.ids),
            ('parent_id', '=', False)
        ], ['partner_id'], ['partner_id'])
        result = dict(
            (
                data['partner_id'][0], data['partner_id_count']
            ) for data in fetch_data)
        for partner in self:
            partner.task_count = result.get(partner.id, 0) + sum(
                c.task_count for c in partner.child_ids)

    company_type = fields.Selection(
        string='Company Type', compute='_compute_company_type', store=True,
        selection_add=[
            ('company', 'Customer Company'),
            ('owner', 'Owner'),
            ('management', 'Management'),
            ('vendor', 'Vendor')
        ], inverse='_write_company_type')
    ownership_company_type_id = fields.Many2one(
        'res.partner', string='Owner Ship Company')
    management_company_type_id = fields.Many2one(
        'res.partner', string='Mgmt. Company')
    is_owner = fields.Boolean(
        string='Is a Owner', default=False,
        help="Check if the contact is a Owner")
    is_management = fields.Boolean(
        string='Is a Management', default=False,
        help="Check if the contact is a Management")
    is_vendor = fields.Boolean(
        string='Is a Vendore', default=False,
        help="Check if the contact is a Vendor")
    account_user_id = fields.Many2one('res.partner',
                                      string='Account Manager')
    secondary_user_id = fields.Many2one('res.partner',
                                        string='Secondary Acct. Manager')
    national_user_id = fields.Many2one('res.partner',
                                       string='National Acct. Manager')
    mangement_company_type = fields.Selection(
        string='Mgmt. Company Type',
        selection=[
            ('greystar', 'Greystar'),
            ('other', 'Other')
        ])
    contact_type_ids = fields.Many2many(
        'contact.type', 'contact_type_rel',
        'con_id', 'type_id', string="Contact Type")
    contact_company_type_id = fields.Many2one('res.partner',
                                              string='Contact Name')
    company_type_rel = fields.Selection(related='company_type',
                                        string='Company Type', )
    contact_display_kanban = fields.Char("Contact Display Name")
    contact_child_ids = fields.One2many(
        'res.partner.clx.child', 'parent_id',
        string="Other Contacts")
    vertical = fields.Selection([('res', 'RES'), ('srl', 'SRL'), ('local', 'Local'), ('auto', 'Auto')],
                                string="Vertical")
    branding_name = fields.Char(string="Branding Name")
    timezone_char = fields.Selection([('atlantic', 'Atlantic'), ('central', 'Central'),
                                      ('cst', 'CST'), ('eastern', 'Eastern'),
                                      ('est', 'EST'), ('hawaii', 'Hawaii'),
                                      ('mountain', 'Mountain'), ('pacific', 'Pacific'),
                                      ('pst', 'PST')
                                      ], string="Timezone2")
    yardi_code = fields.Char(string="Yardi Code")
    master_id = fields.Char(string="Master ID")
    ads_link_ids = fields.One2many('ads.link', 'partner_id',string="Ads Link")
    cs_notes = fields.Text(string="CS Notes")
    ops_notes = fields.Text(string="Ops Notes")
    cat_notes = fields.Text(string="Cat Notes")
    accounting_notes = fields.Text(string="Accounting Notes")
    merchant_number = fields.Char(string="Ops Merchant Number")
    tap_clicks_username = fields.Char(string="TapClicks Username")
    tap_clicks_password = fields.Char(string="TapClicks Password")
    call_rail_destination_number = fields.Char(string="CallRail Destination Number")
    client_provided_tracking_email = fields.Char(string="Client-Provided Tracking Email")
    client_provided_utm_tracking_urls = fields.Char(string="Client-Provided UTM Tracking URLs")
    art_assets = fields.Char(string="Art Assets")


    @api.model
    def read_group(self, domain, fields, groupby,
                   offset=0, limit=None, orderby=False, lazy=True):
        if 'custom_filter_groupby' in self._context and \
                'parent_id' in groupby:
            domain = [('company_type', '=', 'person')]
        return super(Partner, self).read_group(
            domain, fields, groupby, offset=offset,
            limit=limit, orderby=orderby, lazy=lazy)

    @api.onchange('contact_company_type_id')
    def onchange_contact_company_type(self):
        if self.contact_company_type_id:
            self.street = self.contact_company_type_id.street or ''
            self.street2 = self.contact_company_type_id.street2 or ''
            self.state_id = self.contact_company_type_id.state_id.id or False
            self.zip = self.contact_company_type_id.zip or ''
            self.city = self.contact_company_type_id.city or ''
            self.country_id = self.contact_company_type_id.country_id.id or False
            self.email = self.contact_company_type_id.email or ''
            self.phone = self.contact_company_type_id.phone or False
            self.mobile = self.contact_company_type_id.mobile or False
            self.name = self.contact_company_type_id.display_name

    @api.onchange('contact_type_ids')
    def onchange_contact_display_name(self):
        for rec in self:
            if rec.contact_type_ids:
                rec.contact_display_kanban = ' ,'.join([
                    contact.nik for contact in rec.contact_type_ids
                ])
            else:
                rec.contact_display_kanban = ''

    @api.depends('is_company', 'is_owner', 'is_management')
    def _compute_company_type(self):
        for partner in self:
            if partner.is_company and not partner.is_owner and \
                    not partner.is_management and not partner.is_vendor:
                partner.company_type = 'company'
            elif partner.is_owner and not partner.is_management and \
                    not partner.is_vendor:
                partner.company_type = 'owner'
            elif partner.is_management and not partner.is_owner and \
                    not partner.is_vendor:
                partner.company_type = 'management'
            elif partner.is_vendor and not partner.is_owner and \
                    not partner.is_management:
                partner.company_type = 'vendor'
            else:
                partner.company_type = 'person'

    def properties_owner(self):
        self.ensure_one()
        domain = [
            '|', ('ownership_company_type_id', '=', self.id),
            ('ownership_company_type_id', 'in', self.child_ids.ids)
        ]
        action = self.env.ref(
            'contact_modification.action_contacts_list_owner'
        ).read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def properties_management(self):
        self.ensure_one()
        domain = [
            '|', ('management_company_type_id', 'in', [self.id]),
            ('management_company_type_id', 'in', self.child_ids.ids)
        ]
        action = self.env.ref(
            'contact_modification.action_contacts_list_managemet'
        ).read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def assignation_management(self):
        self.ensure_one()
        clx_child_ids = self.env['res.partner.clx.child'].search([
            ('child_id', '=', self.id)
        ])
        # parent_id = [
        # clx_child_id.parent_id.id for clx_child_id in clx_child_ids]
        domain = [('id', 'in', clx_child_ids.ids)]
        action = self.env.ref(
            'contact_modification.action_partner_assignation_contacts'
        ).read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        return dict(action, domain=domain, context=context)

    def _write_company_type(self):
        for partner in self:
            partner.set_contact_type_flag()

    @api.onchange('company_type')
    def onchange_company_type(self):
        self.set_contact_type_flag()

    def set_contact_type_flag(self):
        """
        To check current contact type
        to display parent for contact at form and in relation.
        :return: None
        """
        cmp_type = self.company_type
        self.is_company = True if cmp_type == 'company' else False
        self.is_vendor = True if cmp_type == 'vendor' else False
        self.is_owner = True if cmp_type == 'owner' else False
        self.is_management = True if cmp_type == 'management' else False
