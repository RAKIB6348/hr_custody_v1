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
from odoo import fields, models


class ResCompany(models.Model):
    """Add custody stock configuration on company."""
    _inherit = 'res.company'

    custody_stock_source_location_id = fields.Many2one(
        'stock.location', string='Custody Source Location',
        help='Location used as the source when delivering custody items.')
    custody_stock_destination_location_id = fields.Many2one(
        'stock.location', string='Custody Destination Location',
        help='Location used as the destination when delivering custody items.')


class ResConfigSettings(models.TransientModel):
    """Expose custody stock locations in inventory settings."""
    _inherit = 'res.config.settings'

    custody_stock_source_location_id = fields.Many2one(
        related='company_id.custody_stock_source_location_id',
        readonly=False)
    custody_stock_destination_location_id = fields.Many2one(
        related='company_id.custody_stock_destination_location_id',
        readonly=False)
