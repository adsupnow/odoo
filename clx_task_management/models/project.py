# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    demo_data = fields.Boolean()


class ProjectProject(models.Model):
    _inherit = 'project.project'

    req_form_id = fields.Many2one('request.form', string='Request Form')
    clx_state = fields.Selection([('new', 'NEW'), ('in_progress', 'In Progress'), ('done', 'Done')], string="State")
    clx_sale_order_ids = fields.Many2many('sale.order', string='Sale order')
    project_ads_link_ids = fields.One2many(related='partner_id.ads_link_ids', string="Ads Link", readonly=False)
    clx_project_manager_id = fields.Many2one('res.users', string="CS Team Member")
    clx_project_designer_id = fields.Many2one('res.users', string="CAT Team Member")
    ops_team_member_id = fields.Many2one("res.users", string="OPS Team Member")
    management_company_type_id = fields.Many2one(related='partner_id.management_company_type_id')
    google_analytics_cl_account_location = fields.Selection(related='partner_id.google_analytics_cl_account_location')
    cs_notes = fields.Text(related='partner_id.cs_notes')
    ops_notes = fields.Text(related='partner_id.ops_notes')
    cat_notes = fields.Text(related='partner_id.cat_notes')
    deadline = fields.Date(string='Deadline')
    priority = fields.Selection([('high', 'High'), ('regular', 'Regular')], default='regular', string="Priority")
    client_services_team = fields.Selection(related="partner_id.management_company_type_id.client_services_team",
                                            store=True)
    clx_attachment_ids = fields.Many2many(
        "ir.attachment", 'att_project_rel', 'attach_id', 'clx_id', string="Files", help="Upload multiple files here."
    )
    implementation_specialist_id = fields.Many2one(related="partner_id.implementation_specialist_id")

    def write(self, vals):
        res = super(ProjectProject, self).write(vals)
        if 'active' in vals:
            self.task_ids.write({'active': vals.get('active', False)})
        if vals.get('clx_project_manager_id', False):
            cs_team = self.env['clx.team'].search([('team_name', '=', 'CS')])
            for task in self.task_ids:
                if cs_team in task.team_ids:
                    task.clx_task_manager_id = self.clx_project_manager_id.id
            self.clx_state = 'in_progress'
        if vals.get('ops_team_member_id', False):
            for task in self.task_ids:
                task.ops_team_member_id = self.ops_team_member_id.id
        if vals.get('clx_project_manager_id', False):
            for task in self.task_ids:
                task.clx_project_manager_id = self.clx_project_manager_id.id
        if vals.get('clx_project_designer_id', False):
            self.task_ids.write({'clx_task_designer_id': self.clx_project_designer_id.id})
            # for task in self.task_ids:
            #     task.clx_project_designer_id = self.clx_project_designer_id.id
        return res

    def action_done_project(self):
        complete_stage = self.env.ref('clx_task_management.clx_project_stage_8')
        if all(task.stage_id.id == complete_stage.id for task in self.task_ids):
            self.clx_state = 'done'
        else:
            raise UserError(_("Please Complete All the Task First!!"))


class ProjectTask(models.Model):
    _inherit = 'project.task'

    repositary_task_id = fields.Many2one('main.task', string='Repository Task')
    sub_repositary_task_ids = fields.Many2many('sub.task',
                                               string='Repository Sub Task')
    req_type = fields.Selection([('new', 'New'), ('update', 'Update')],
                                string='Request Type')
    sub_task_id = fields.Many2one('sub.task', string="Sub Task from Master Table")
    team_ids = fields.Many2many('clx.team', string='Team')
    team_members_ids = fields.Many2many('res.users', string="Team Members")
    clx_sale_order_id = fields.Many2one('sale.order', string='Sale order')
    clx_sale_order_line_id = fields.Many2one('sale.order.line', string="Sale order Item")
    requirements = fields.Text(string='Requirements')
    clx_task_manager_id = fields.Many2one("res.users", string="CS Team Member")
    clx_task_designer_id = fields.Many2one("res.users", string="CAT Team Member")
    ops_team_member_id = fields.Many2one("res.users", string="OPS Team Member")

    management_company_type_id = fields.Many2one(related='project_id.partner_id.management_company_type_id')
    google_analytics_cl_account_location = fields.Selection(
        related='project_id.partner_id.google_analytics_cl_account_location')
    cs_notes = fields.Text(related='project_id.partner_id.cs_notes')
    ops_notes = fields.Text(related='project_id.partner_id.ops_notes')
    cat_notes = fields.Text(related='project_id.partner_id.cat_notes')
    vertical = fields.Selection(related='project_id.partner_id.vertical')
    account_user_id = fields.Many2one("res.users", string="Salesperson")
    website = fields.Char(related='project_id.partner_id.website')
    partner_id = fields.Many2one(related='project_id.partner_id', store=True)
    project_ads_link_ids = fields.One2many(related='project_id.project_ads_link_ids', string="Ads Link", readonly=False)
    art_assets = fields.Char(related='project_id.partner_id.art_assets')
    call_rail_destination_number = fields.Char(related='project_id.partner_id.call_rail_destination_number')
    dni = fields.Char(related='project_id.partner_id.dni')
    reviewer_user_id = fields.Many2one('res.users', string="Reviewer")
    fix = fields.Selection([('not_set', 'Not Set'), ('no', 'No'), ('yes', 'Yes')], string="Fix Needed",
                           default="not_set")
    clx_priority = fields.Selection([('high', 'High'), ('regular', 'Regular')], default='regular', string="Priority")
    client_services_team = fields.Selection(
        related="project_id.partner_id.management_company_type_id.client_services_team",
        store=True)
    sub_task_project_ids = fields.One2many(compute="_compute_sub_task_project_ids", comodel_name='sub.task.project',
                                           string="Sub Task")
    clx_attachment_ids = fields.Many2many(
        "ir.attachment", 'att_task_rel', 'attach_id', 'clx_id', string="Files", help="Upload multiple files here."
    )
    clx_description = fields.Html(related="parent_id.description", readonly=False)
    implementation_specialist_id = fields.Many2one(related="project_id.partner_id.implementation_specialist_id")
    product_id = fields.Many2one('product.product', string="Product")

    def _compute_sub_task_project_ids(self):
        task_list = []
        if not self.parent_id and self.repositary_task_id:
            sub_tasks = self.env['sub.task'].search([('parent_id', '=', self.repositary_task_id.id)])
            sub_task_project_obj = self.env['sub.task.project']
            child_task = self.child_ids
            for sub_task in sub_tasks:
                child_task_id = child_task.filtered(
                    lambda x: x.sub_task_id.id == sub_task.id and x.parent_id.id == self.id)
                vals = {
                    'sub_task_id': sub_task.id,
                    'task_id': child_task_id[0].id if child_task_id else False,
                    'sub_task_name': sub_task.sub_task_name,
                    'team_ids': sub_task.team_ids.ids if sub_task.team_ids else False,
                    'team_members_ids': sub_task.team_members_ids.ids if sub_task.team_members_ids else False,
                    'tag_ids': sub_task.tag_ids.ids if sub_task.tag_ids else False,
                    'stage_id': child_task_id[0].stage_id.id if child_task_id else False
                }
                task_id = sub_task_project_obj.create(vals)
                task_list.append(task_id.id)
        self.sub_task_project_ids = [(6, 0, task_list)]

    def prepared_sub_task_vals(self, sub_task, main_task):
        """
        Prepared vals for sub task
        :param sub_task: browsable object of the sub.task
        :param main_task: browsable object of the main.task
        :return: dictionary for the sub task
        """
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        if stage_id:
            vals = {
                'name': sub_task.sub_task_name,
                'project_id': main_task.project_id.id,
                'stage_id': stage_id.id,
                'sub_repositary_task_ids': sub_task.dependency_ids.ids,
                'parent_id': main_task.id,
                'sub_task_id': sub_task.id,
                'team_ids': sub_task.team_ids.ids if sub_task.team_ids else False,
                'team_members_ids': sub_task.team_members_ids.ids,
                'tag_ids': sub_task.tag_ids.ids if sub_task.tag_ids else False,
                'clx_attachment_ids': main_task.project_id.clx_attachment_ids.ids if main_task.project_id.clx_attachment_ids else False,
                'account_user_id': main_task.partner_id.account_user_id.id if main_task.partner_id.account_user_id else False
            }
            return vals

    def action_view_clx_so(self):
        """
        open sale order from project task form view via smart button
        :return:
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "views": [[False, "form"]],
            "res_id": self.clx_sale_order_id.id,
            "context": {"create": False, "show_sale": True},
        }

    def unlink(self):
        completed_stage = self.env.ref('clx_task_management.clx_project_stage_8')
        for task in self:
            task.project_id.message_post(type='comment', body=_("""
                <p>Task Has been Deleted By %s</p><br/>
                <p>Task Name : %s </p>
            """) % (self.env.user.name, task.name))
            if task.stage_id.id != completed_stage.id:
                params = self.env['ir.config_parameter'].sudo()
                auto_create_sub_task = bool(params.get_param('auto_create_sub_task')) or False
                if auto_create_sub_task:
                    main_task = task.project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
                    sub_tasks = self.env['sub.task'].search(
                        [('parent_id', 'in', main_task.ids), ('dependency_ids', 'in', task.sub_task_id.ids)])
                    for sub_task in sub_tasks:
                        vals = self.create_sub_task(sub_task, task.project_id)
                        self.create(vals)
        return super(ProjectTask, self).unlink()

    def create_sub_task(self, task, project_id):
        """
        prepared vals for subtask
        :param task: recordset of the sub.task
        :param project_id: recordset of the project.project
        :return: dictionary of the sub task for the project.task
        """
        stage_id = self.env.ref('clx_task_management.clx_project_stage_1')
        sub_task = self.project_id.task_ids.filtered(lambda x: x.sub_task_id.parent_id.id == task.parent_id.id)
        if stage_id:
            parent_id = self.project_id.task_ids.filtered(lambda x: x.name == task.parent_id.name)
            vals = {
                'name': task.sub_task_name,
                'project_id': project_id.id,
                'stage_id': stage_id.id,
                'sub_repositary_task_ids': task.dependency_ids.ids,
                'parent_id': parent_id[0].id if parent_id else self.parent_id.id,
                'sub_task_id': task.id,
                'team_ids': task.team_ids.ids if task.team_ids else False,
                'team_members_ids': task.team_members_ids.ids if task.team_members_ids else False,
                'tag_ids': task.tag_ids.ids if task.tag_ids else False,
                'date_deadline': project_id.deadline if project_id.deadline else False,
                'ops_team_member_id': self.ops_team_member_id.id if self.ops_team_member_id else False,
                'clx_task_designer_id': self.clx_task_designer_id.id if self.clx_task_designer_id else False,
                'clx_task_manager_id': self.clx_task_manager_id.id if self.clx_task_manager_id else False,
                'account_user_id': project_id.partner_id.account_user_id.id if project_id.partner_id.account_user_id else False,
                'clx_priority': project_id.priority,
                'description': self.description,
                'clx_attachment_ids': project_id.clx_attachment_ids.ids if project_id.clx_attachment_ids else False,
                'product_id': self.parent_id.product_id.id if self.parent_id.product_id else False
            }
            return vals

    @api.onchange('stage_id')
    def onchange_stage_id(self):
        complete_stage = self.env.ref('clx_task_management.clx_project_stage_8')
        if not self.parent_id and self.stage_id.id == complete_stage.id:
            raise UserError(_("You Can not Complete the Task until the all Sub Task are completed"))

    def write(self, vals):
        complete_stage = self.env.ref('clx_task_management.clx_project_stage_8')
        res = super(ProjectTask, self).write(vals)
        if 'active' in vals:
            for task in self.child_ids:
                self._cr.execute("UPDATE project_task SET active = %s WHERE id = %s", [vals.get('active'), task.id])
        if vals.get('date_deadline'):
            for task in self.child_ids:
                task.date_deadline = self.date_deadline
        sub_task_obj = self.env['sub.task']
        if vals.get('req_type', False) and vals.get('repositary_task_id', False):
            repositary_main_task = self.env['main.task'].browse(vals.get('repositary_task_id'))
            if repositary_main_task:
                repo_sub_tasks = sub_task_obj.search([('parent_id', '=', repositary_main_task.id),
                                                      ('dependency_ids', '=', False)])
                for sub_task in repo_sub_tasks:
                    vals = self.prepared_sub_task_vals(
                        sub_task, self)
                    self.create(vals)
                self.tag_ids = self.repositary_task_id.tag_ids.ids if self.repositary_task_id.tag_ids else False
                self.team_ids = self.repositary_task_id.team_ids.ids if self.repositary_task_id.team_ids else False
                self.team_members_ids = self.repositary_task_id.team_members_ids.ids if self.repositary_task_id.team_members_ids else False
                self.account_user_id = self.project_id.partner_id.user_id.id if self.project_id.partner_id.user_id else False

        stage_id = self.env['project.task.type'].browse(vals.get('stage_id'))
        cancel_stage = self.env.ref('clx_task_management.clx_project_stage_9')
        if vals.get('stage_id', False) and stage_id.id == complete_stage.id:
            if self.sub_task_id:
                parent_task_main_task = self.project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
                dependency_tasks = sub_task_obj.search(
                    [('dependency_ids', 'in', self.sub_task_id.ids),
                     ('parent_id', 'in', parent_task_main_task.ids)])
                for task in dependency_tasks:
                    count = 0
                    parent_task = task.dependency_ids.mapped('parent_id')
                    if len(parent_task) > 1:
                        all_task = self.project_id.task_ids.filtered(
                            lambda x: x.sub_task_id.id in task.dependency_ids.ids)
                    elif len(parent_task) == 1:
                        all_task = self.parent_id.child_ids.filtered(
                            lambda x: x.sub_task_id.id in task.dependency_ids.ids)
                    depedent_task_list = task.dependency_ids.ids
                    for depedent_task in task.dependency_ids:
                        task_found = all_task.filtered(lambda x: x.name == depedent_task.sub_task_name)
                        if task_found:
                            count += 1
                    if all(line.stage_id.id == complete_stage.id for line in all_task) and count == len(
                            depedent_task_list):
                        if task.id not in self.parent_id.child_ids.mapped('sub_task_id').ids:
                            vals = self.create_sub_task(task, self.project_id)
                            self.create(vals)
        if vals.get('stage_id', False) and self.parent_id and self.parent_id.child_ids:
            if all(line.stage_id.id == complete_stage.id for line in self.parent_id.child_ids):
                self.parent_id.stage_id = complete_stage.id
            if all(task.stage_id.id == complete_stage.id for task in self.project_id.task_ids):
                self.project_id.clx_state = 'done'

        elif vals.get('stage_id', False) and stage_id.id == cancel_stage.id:
            params = self.env['ir.config_parameter'].sudo()
            auto_create_sub_task = bool(params.get_param('auto_create_sub_task')) or False
            if auto_create_sub_task:
                main_task = self.project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
                sub_tasks = self.env['sub.task'].search(
                    [('parent_id', 'in', main_task.ids), ('dependency_ids', 'in', self.sub_task_id.ids)])
                for sub_task in sub_tasks:
                    vals = self.create_sub_task(sub_task, self.project_id)
                    self.create(vals)
        if vals.get('ops_team_member_id', False):
            for task in self.child_ids:
                task.ops_team_member_id = self.ops_team_member_id.id
        if vals.get('clx_task_designer_id', False):
            for task in self.child_ids:
                task.clx_task_designer_id = self.clx_task_designer_id.id
        if vals.get('clx_task_manager_id', False):
            for task in self.child_ids:
                task.clx_task_manager_id = self.clx_task_manager_id.id
        return res

    def action_view_popup_task(self):
        sub_tasks = self.sub_repositary_task_ids
        context = dict(self._context) or {}
        context.update({
            'project_id': self.project_id.id,
            'current_task': self.id,
            'default_sub_task_ids': sub_tasks.ids,
        })
        view_id = self.env.ref('clx_task_management.task_popup_warning_wizard_form_view').id
        return {'type': 'ir.actions.act_window',
                'name': _('Sub Task'),
                'res_model': 'task.popup.warning.wizard',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': context
                }

    def action_view_cancel_task(self):
        main_task = self.project_id.task_ids.mapped('sub_task_id').mapped('parent_id')
        sub_tasks = self.env['sub.task'].search(
            [('parent_id', 'in', main_task.ids), ('dependency_ids', 'in', self.sub_task_id.ids)])
        context = dict(self._context) or {}
        context.update({
            'project_id': self.project_id.id,
            'default_sub_task_ids': sub_tasks.ids,
            'current_task': self.id
        })
        view_id = self.env.ref('clx_task_management.task_cancel_warning_wizard_form_view').id
        return {'type': 'ir.actions.act_window',
                'name': _('Sub Task'),
                'res_model': 'task.cancel.warning.wizard',
                'target': 'new',
                'view_mode': 'form',
                'views': [[view_id, 'form']],
                'context': context
                }

    def unlink(self):
        for record in self:
            record.child_ids.unlink()
        return super(ProjectTask, self).unlink()
