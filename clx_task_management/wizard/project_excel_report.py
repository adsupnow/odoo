# -*- coding: utf-8 -*-
# Part of Odoo, CLx Media
# See LICENSE file for full copyright & licensing details.

from odoo import models
import base64
import io
import xlsxwriter


class ProjectTaskExcelReport(models.TransientModel):
    _name = "project.task.excel.report"
    _description = "Project Task Excel Report"

    def download_report(self):
        project_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        tasks = self.env[active_model].browse(project_ids)
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('Tasks')
        worksheet.freeze_panes(1, 0)
        header_format = workbook.add_format({'bold': True})
        row = 0
        col = 0
        headers = ['Title', 'Project Name', 'Customer', 'Account Manager', 'CS Team Member', 'Ops Team Member',
                   'CAT Team Member', 'Team', 'Team Members', 'Tags', 'Task Creation Date',
                   'Task Completion Date', 'Deadline', 'Priority', 'Client Services Team', 'State',
                   'Total Days Task complete'
                   ]
        for header in headers:
            worksheet.write(row, col, header, header_format)
            col += 1
        row += 1
        col = 0
        for task in tasks:
            worksheet.write(row, col, task.name)
            worksheet.write(row, col + 1, task.project_id.name)
            worksheet.write(row, col + 2, task.partner_id.name if task.partner_id else " ")
            worksheet.write(row, col + 3, task.account_user_id.name if task.account_user_id else " ")
            worksheet.write(row, col + 4, task.clx_task_manager_id.name if task.clx_task_manager_id else " ")
            worksheet.write(row, col + 5, task.ops_team_member_id.name if task.ops_team_member_id else " ")
            worksheet.write(row, col + 6, task.clx_task_designer_id.name if task.clx_task_designer_id else " ")
            worksheet.write(row, col + 7, ",".join(task.team_ids.mapped('team_name')) if task.team_ids else " ")
            worksheet.write(row, col + 8,
                            ",".join(task.team_members_ids.mapped('name')) if task.team_members_ids else " ")
            worksheet.write(row, col + 9, ",".join(task.tag_ids.mapped('name')) if task.tag_ids else " ")
            worksheet.write(row, col + 10, task.create_date.strftime("%m/%d/%Y, %H:%M:%S"))
            worksheet.write(row, col + 11,
                            task.task_complete_date.strftime("%m/%d/%Y, %H:%M:%S") if task.task_complete_date else " ")
            worksheet.write(row, col + 12, task.date_deadline.strftime("%m/%d/%Y")) if task.date_deadline else " "
            worksheet.write(row, col + 13, task.clx_priority)
            worksheet.write(row, col + 14, task.client_services_team)
            worksheet.write(row, col + 15, task.stage_id.name)
            worksheet.write(row, col + 16,
                            task.task_complete_date - task.create_date if task.task_complete_date and task.create_date else False)
            row += 1
        workbook.close()
        fp.seek(0)
        result = base64.b64encode(fp.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'project_task_excel_report.xlsx', 'display_name': 'Project_task_excel_report.xlsx',
             'datas': result})
        download_url = '/web/content/' + \
                       str(attachment_id.id) + '?download=True'

        return {
            "type": "ir.actions.act_url",
            "url": str(download_url),
            "target": "new",
            'nodestroy': False,
        }


class ProjectExcelReport(models.TransientModel):
    _name = "project.excel.report"
    _description = "Project Excel Report"

    def download_report(self):
        project_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')
        projects = self.env[active_model].browse(project_ids)
        fp = io.BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        worksheet = workbook.add_worksheet('Projects')
        worksheet.freeze_panes(1, 0)
        header_format = workbook.add_format({'bold': True})
        row = 0
        col = 0
        headers = ['Project Name', 'Customer', 'Account Manager', 'CS Team Member', 'Ops Team Member',
                   'CAT Team Member', 'Project Creation Date', 'Project Completion Date', 'Deadline', 'Priority',
                   'Client Services Team', 'State', "Total Days Project complete"
                   ]
        for header in headers:
            worksheet.write(row, col, header, header_format)
            col += 1
        col = 0
        row += 1
        for project in projects:
            worksheet.write(row, col, project.name)
            worksheet.write(row, col + 1, project.partner_id.name)
            worksheet.write(row, col + 2, project.user_id.name)
            worksheet.write(row, col + 3,
                            project.clx_project_manager_id.name if project.clx_project_manager_id else " ")
            worksheet.write(row, col + 4, project.ops_team_member_id.name if project.ops_team_member_id else " ")
            worksheet.write(row, col + 5,
                            project.clx_project_designer_id.name if project.clx_project_designer_id else " ")
            worksheet.write(row, col + 6, project.create_date.strftime("%m/%d/%Y, %H:%M:%S"))
            worksheet.write(row, col + 7,
                            project.completion_date.strftime("%m/%d/%Y, %H:%M:%S") if project.completion_date else " ")
            worksheet.write(row, col + 8, project.deadline.strftime("%m/%d/%Y") if project.deadline else " ")
            worksheet.write(row, col + 9, project.priority)
            worksheet.write(row, col + 10, project.client_services_team)
            worksheet.write(row, col + 11, project.clx_state)
            worksheet.write(row, col + 12,
                            project.completion_date - project.create_date if project.completion_date and project.create_date else False)
            row += 1
        workbook.close()
        fp.seek(0)
        result = base64.b64encode(fp.read())
        attachment_obj = self.env['ir.attachment']
        attachment_id = attachment_obj.create(
            {'name': 'project_excel_report.xlsx', 'display_name': 'Project_excel_report.xlsx', 'datas': result})
        download_url = '/web/content/' + \
                       str(attachment_id.id) + '?download=True'

        return {
            "type": "ir.actions.act_url",
            "url": str(download_url),
            "target": "new",
            'nodestroy': False,
        }
