# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    custody_count = fields.Integer(compute='_compute_custody_count',
                                   string='# Custody',
                                   help='This field represents '
                                        'the count of custodies.')
    equipment_count = fields.Integer(compute='_compute_equipment_count',
                                     string='# Equipments',
                                     help='This field represents '
                                          'the count of equipments.',
                                     )
    custody_location_id = fields.Many2one(
        'stock.location',
        string='Custody Location',
        help='Select the location where custody items for this employee should be delivered'
    )

    @api.depends('custody_count')
    def _compute_custody_count(self):
        """The compute function
        the count of custody
        associated with each employee."""
        for each in self:
            custody_ids = self.env['hr.custody'].search(
                [('employee_id', '=', each.id)])
            each.custody_count = len(custody_ids)

    @api.depends('equipment_count')
    def _compute_equipment_count(self):
        """The Compute function the count
        of distinct equipment
        properties associated
        with each employee. """
        for each in self:
            equipment_obj = self.env['hr.custody'].search(
                [('employee_id', '=', each.id), ('state', '=', 'approved')])
            equipment_ids = []
            for each1 in equipment_obj:
                if each1.custody_property_id.id not in equipment_ids:
                    equipment_ids.append(each1.custody_property_id.id)
            each.equipment_count = len(equipment_ids)

    def custody_view(self):
        for emp in self:
            custody_ids = self.env['hr.custody'].search([('employee_id', '=', emp.id)]).ids

            view = self.env.ref('hr_custody.hr_custody_view_form', raise_if_not_found=False)

            if custody_ids:
                if len(custody_ids) == 1:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _('Custody'),
                        'res_model': 'hr.custody',
                        'view_mode': 'form',
                        'views': [(view.id, 'form')] if view else [(False, 'form')],
                        'res_id': custody_ids[0],
                        'target': 'current',
                    }
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Custody'),
                    'res_model': 'hr.custody',
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', custody_ids)],
                    'target': 'current',
                }

    def equipment_view(self):
        for emp in self:
            equipment_ids = []
            equipment_obj = self.env['hr.custody'].search([
                ('employee_id', '=', emp.id),
                ('state', '=', 'approved')
            ])
            for rec in equipment_obj:
                if rec.custody_property_id.id not in equipment_ids:
                    equipment_ids.append(rec.custody_property_id.id)

            view = self.env.ref('hr_custody.custody_property_view_form', raise_if_not_found=False)

            if equipment_ids:
                if len(equipment_ids) == 1:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': _('Equipments'),
                        'res_model': 'custody.property',
                        'view_mode': 'form',
                        'views': [(view.id, 'form')] if view else [(False, 'form')],
                        'res_id': equipment_ids[0],
                        'target': 'current',
                    }
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Equipments'),
                    'res_model': 'custody.property',
                    'view_mode': 'tree,form',
                    'domain': [('id', 'in', equipment_ids)],
                    'target': 'current',
                }

