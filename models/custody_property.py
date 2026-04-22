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
from odoo import api, fields, models


class CustodyProperty(models.Model):
    """
        Hr property creation model.
    """
    _name = 'custody.property'
    _description = 'Custody Property'

    name = fields.Char(string='Property Name', required=True,
                       help='Enter the name of the custody property')
    image = fields.Image(string="Image",
                         help="This field holds the image used for "
                              "this provider, limited to 1024x1024px")
    image_medium = fields.Binary(
        "Medium-sized image", attachment=True,
        help="Medium-sized image of this provider. It is automatically "
             "resized as a 128x128px image, with aspect ratio preserved. "
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary(
        "Small-sized image", attachment=True,
        help="Small-sized image of this provider. It is automatically "
             "resized as a 64x64px image, with aspect ratio preserved. "
             "Use this field anywhere a small image is required.")
    desc = fields.Html(string='Description',
                       help='A detailed description of the item.')
    company_id = fields.Many2one('res.company', 'Company',
                                 help='The company associated with '
                                      'this record.',
                                 default=lambda self: self.env.user.company_id)
    brand_id = fields.Many2one(
        'custody.brand', string='Brand',
        help='Brand associated with this property.')
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id), '|', ('company_id', '=', company_id), ('company_id', '=', False)]",
        help='Product lot/serial number used as the asset identifier.')
    asset_id = fields.Char(
        string='Asset ID',
        help='Editable asset identifier shown in reports.')
    asset_model = fields.Char(
        string='Model',
        help='Model number or model name of the asset.')
    specification = fields.Text(
        string='Specification',
        help='Technical specification shown in fixed asset reports.')
    serial_service_tag = fields.Char(
        string='Serial/Service Tag',
        compute='_compute_serial_service_tag',
        store=True,
        help='Serial/service tag mirrored from the selected lot/serial number.')
    purchase_date = fields.Date(
        string='Purchase Date',
        help='Purchase date of the asset.')
    vendor_name = fields.Char(
        string='Vendor Name',
        help='Vendor or supplier name shown in the report.')
    price = fields.Float(
        string='Price',
        help='Purchase price of the asset.')
    purchase_details = fields.Char(
        string='Purchase Details',
        help='Additional purchase reference or details.')
    received_by = fields.Char(
        string='Received By',
        help='Person who received the asset.')
    remark = fields.Char(
        string='Remark',
        help='Additional note printed in the report.')
    property_selection = fields.Selection([('empty', 'No Connection'),
                                           ('product', 'Products')],
                                          default='empty',
                                          string='Property From',
                                          help="Select the property")

    product_id = fields.Many2one('product.product',
                                 string='Product', help="Select the Product")
    current_custody_id = fields.Many2one(
        'hr.custody',
        string='Current Custody',
        compute='_compute_current_custody',
        help='Latest active custody used for inventory reporting.')
    current_employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        compute='_compute_current_custody',
        help='Employee currently holding this asset.')
    current_company_id = fields.Many2one(
        'res.company',
        string='Current Company',
        compute='_compute_current_custody',
        help='Company of the current employee.')
    current_department_id = fields.Many2one(
        'hr.department',
        string='Department',
        compute='_compute_current_custody',
        help='Department of the current employee.')
    current_job_id = fields.Many2one(
        'hr.job',
        string='Designation',
        compute='_compute_current_custody',
        help='Job position of the current employee.')
    current_work_location_id = fields.Many2one(
        'hr.work.location',
        string='Location',
        compute='_compute_current_custody',
        help='Work location of the current employee.')

    def _get_asset_display_name(self):
        """Build the same display value for Property Name and Asset ID."""
        self.ensure_one()
        if self.product_id and self.lot_id:
            return f"ASSET-{self.product_id.display_name.upper()}-{self.lot_id.name.upper()}"
        elif self.product_id:
            return f"ASSET-{self.product_id.display_name}"
        return False

    @api.onchange('product_id')
    def onchange_product(self):
        """The function is used to
            change product Automatic
            fill name field"""
        if self.product_id:
            product_tmpl = self.product_id.product_tmpl_id
            self.brand_id = product_tmpl.brand_id
            self.asset_model = product_tmpl.model_name
            self.specification = product_tmpl.specification
            self.price = self.product_id.list_price
            purchase_lines = self.env['purchase.order.line'].search([
                ('product_id', '=', self.product_id.id),
                ('order_id.state', 'in', ['purchase', 'done']),
            ])
            purchase_line = purchase_lines.sorted(
                key=lambda line: (
                    line.order_id.date_approve or line.order_id.date_order or False,
                    line.id,
                ),
                reverse=True,
            )[:1]
            if purchase_line:
                # Use the latest confirmed purchase as the default purchase source.
                self.purchase_date = (
                    purchase_line.order_id.date_approve.date()
                    if purchase_line.order_id.date_approve
                    else purchase_line.order_id.date_order.date()
                    if purchase_line.order_id.date_order
                    else False
                )
                self.vendor_name = purchase_line.order_id.partner_id.name
            else:
                self.purchase_date = False
                self.vendor_name = False
            # Auto-pick the latest lot/serial for the selected product.
            lot = self.env['stock.lot'].search([
                ('product_id', '=', self.product_id.id),
                '|', ('company_id', '=', self.company_id.id), ('company_id', '=', False),
            ], order='id desc', limit=1)
            self.lot_id = lot

            display_value = self._get_asset_display_name()
            self.name = display_value or False
            self.asset_id = display_value or False
            
        elif self.lot_id and self.lot_id.product_id != self.product_id:
            self.lot_id = False
            self.name = False
            self.asset_id = False

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """Mirror the selected lot/serial into the serial/service tag
           and sync Property Name + Asset ID."""
        self.serial_service_tag = self.lot_id.name or False
        display_value = self._get_asset_display_name()
        self.name = display_value or False
        self.asset_id = display_value or False

    @api.depends('lot_id', 'lot_id.name')
    def _compute_serial_service_tag(self):
        """Use the selected product lot/serial as the serial/service tag."""
        for record in self:
            record.serial_service_tag = record.lot_id.name or False

    def _compute_current_custody(self):
        """Use the latest approved or delivered custody as the active holder."""
        custody_model = self.env['hr.custody']
        for record in self:
            custody = custody_model.search([
                ('custody_property_id', '=', record.id),
                ('state', 'in', ['approved', 'delivered']),
            ], order='date_request desc, id desc', limit=1)
            employee = custody.employee_id
            record.current_custody_id = custody
            record.current_employee_id = employee
            record.current_company_id = employee.company_id or record.company_id
            record.current_department_id = employee.department_id
            record.current_job_id = employee.job_id
            record.current_work_location_id = employee.work_location_id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            value = rec._get_asset_display_name()
            if value:
                rec.name = value
                rec.asset_id = value
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'product_id' in vals or 'lot_id' in vals:
            for rec in self:
                value = rec._get_asset_display_name()
                rec.name = value or False
                rec.asset_id = value or False
        return res