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
from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrCustody(models.Model):
    """
        Hr custody contract creation model.
    """
    _name = 'hr.custody'
    _description = 'Hr Custody Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    is_read_only = fields.Boolean(string="Check Field")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """ Use this function to check weather
        the user has the permission
        to change the employee"""
        res_user = self.env['res.users'].browse(self._uid)
        if res_user.has_group('hr.group_hr_user'):
            self.is_read_only = True
        else:
            self.is_read_only = False

    def mail_reminder(self):
        """ Use this function to product return reminder mail"""
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([('state', '=', 'approved')])
        for i in match:
            if i.return_date:
                exp_date = fields.Date.from_string(i.return_date)
                if exp_date <= date_now:
                    base_url = self.env['ir.config_parameter'].get_param(
                        'web.base.url')
                    url = base_url + _(
                        '/web#id=%s&view_type=form&model=hr.custody&menu_id=') % i.id
                    mail_content = _(
                        'Hi %s,<br>As per the %s you took %s on %s for the reason of %s. S0 here we '
                        'remind you that you have to return that on or before %s. Otherwise, you can '
                        'renew the reference number(%s) by extending the return date through following '
                        'link.<br> <div style = "text-align: center; margin-top: 16px;"><a href = "%s"'
                        'style = "padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; '
                        'border-color:#875A7B;text-decoration: none; display: inline-block; '
                        'margin-bottom: 0px; font-weight: 400;text-align: center; vertical-align: middle; '
                        'cursor: pointer; white-space: nowrap; background-image: none; '
                        'background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px;">'
                        'Renew %s</a></div>') % \
                                   (i.employee_id.name, i.name,
                                    i.custody_property_id.name,
                                    i.date_request, i.purpose,
                                    date_now, i.name, url, i.name)
                    main_content = {
                        'subject': _('REMINDER On %s') % i.name,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.employee_id.work_email,
                    }
                    mail_id = self.env['mail.mail'].create(main_content)
                    mail_id.mail_message_id.body = mail_content
                    mail_id.send()
                    if i.employee_id.user_id:
                        mail_id.mail_message_id.write({
                            'partner_ids': [
                                (4, i.employee_id.user_id.partner_id.id)]})

    @api.model_create_multi
    def create(self, vals):
        """Create a new record for the HrCustody model.
            This method is responsible for creating a new
            record for the HrCustody model with the provided values.
            It automatically generates a unique name for
            the record using the 'ir.sequence'
            and assigns it to the 'name' field."""
        for val in vals:
            val['name'] = self.env['ir.sequence'].next_by_code('hr.custody')
        return super(HrCustody, self).create(vals)

    def _ensure_property_available(self):
        """Ensure no other approved custody exists for the same property."""
        for record in self:
            domain = [
                ('custody_property_id', '=', record.custody_property_id.id),
                ('state', '=', 'approved'),
                ('id', '!=', record.id),
            ]
            if self.search_count(domain):
                raise UserError(_("Custody is not available now"))

    def sent(self):
        """Move the current record to the 'to_approve' state."""
        self.state = 'to_approve'

    def send_mail(self):
        """Send email notification using a predefined template."""
        template = self.env.ref(
            'hr_custody.custody_email_notification_template')
        self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.is_mail_send = True

    def action_print_fixed_asset_pdf(self):
        """Print the fixed asset PDF for the selected custody records."""
        return self.env.ref(
            'hr_custody.action_report_fixed_asset_inventory_pdf'
        ).report_action(self)

    def action_print_fixed_asset_xlsx(self):
        """Print the fixed asset XLSX for the selected custody records."""
        return self.env.ref(
            'hr_custody.action_report_fixed_asset_inventory_xlsx'
        ).report_action(self)

    def set_to_draft(self):
        """Set the current record to the 'draft' state."""
        self.state = 'draft'

    def renew_approve(self):
        """The function Used to renew and approve
        the current custody record."""
        self._ensure_property_available()
        self.return_date = self.renew_date
        self.renew_date = ''
        self.state = 'approved'

    def renew_refuse(self):
        """the function used to refuse
        the renewal of the current custody record"""
        self._ensure_property_available()
        self.renew_date = ''
        self.state = 'approved'

    def approve(self):
        """The function used to approve
        the current custody record."""
        self._ensure_property_available()
        self.state = 'approved'

    def deliver(self):
        """The function used to set the current
        custody record to the 'delivered' state"""
        self._ensure_property_available()
        self._create_stock_transfer()
        self.state = 'delivered'

    def set_to_return(self):
        """The function used to set the current
        custody record to the 'returned' state"""
        for record in self:
            if not record.return_date:
                raise ValidationError(_('Please set a Return Date before returning the custody.'))
            record._create_stock_return_transfer()
            record.state = 'returned'

    @api.constrains('return_date')
    def validate_return_date(self):
        """The function validate the return
        date to ensure it is after the request date"""
        if self.return_date and self.return_date < self.date_request:
            raise ValidationError(_('Please Give Valid Return Date'))

    name = fields.Char(string='Code', copy=False,
                       help='A unique code assigned to this record.')
    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 hhelp='The company associated'
                                       ' with this record. ',
                                 default=lambda self: self.env.user.company_id)
    rejected_reason = fields.Text(string='Rejected Reason', copy=False,
                                  readonly=1, help="Reason for the rejection")
    renew_rejected_reason = fields.Text(string='Renew Rejected Reason',
                                        copy=False, readonly=1,
                                        help="Renew rejected reason")
    date_request = fields.Date(string='Requested Date', required=True,
                               track_visibility='always',
                               help='The date when the request was made',
                               default=datetime.now().strftime('%Y-%m-%d'))
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  required=True,
                                  help='The employee associated with '
                                       'this record.',
                                  default=lambda
                                      self: self.env.user.employee_id.id, )
    purpose = fields.Char(string='Reason', track_visibility='always',
                          required=True,
                          help='The reason or purpose of the custody')
    custody_property_id = fields.Many2one('custody.property',
                                          string='Property', required=True,
                                          help='The property associated '
                                               'with this custody record'
                                          )
    quantity = fields.Integer(string='Quantity', default=1,
                              help='Quantity of the selected property')
    stock_picking_id = fields.Many2one(
        'stock.picking', string='Stock Transfer', copy=False, readonly=True,
        help='Internal transfer generated when the custody is delivered.')
    stock_return_picking_id = fields.Many2one(
        'stock.picking', string='Return Transfer', copy=False, readonly=True,
        help='Incoming transfer generated when the custody is returned.')
    return_date = fields.Date(string='Return Date',
                              track_visibility='always',
                              help='The date when the custody '
                                   'is expected to be returned. ')
    renew_date = fields.Date(string='Renewal Return Date',
                             track_visibility='always',
                             help="Return date for the renewal", readonly=True,
                             copy=False)
    notes = fields.Html(string='Notes', help='Note for Custody')
    is_renew_return_date = fields.Boolean(default=False, copy=False,
                                          help='Rejected Renew Date')
    is_renew_reject = fields.Boolean(default=False, copy=False,
                                     help='Indicates whether '
                                          'the renewal is rejected or not.')
    state = fields.Selection(
        [('draft', 'Draft'), ('to_approve', 'Waiting For Approval'),
         ('approved', 'Approved'), ('delivered', 'Delivered'),
         ('returned', 'Returned'), ('rejected', 'Refused')], string='Status',
        default='draft',
        track_visibility='always', help='Custody states visible in statusbar')
    is_mail_send = fields.Boolean(string="Mail Send",
                                  help='Indicates whether an email has '
                                       'been sent or not.')

    @api.constrains('quantity')
    def _check_quantity(self):
        """Ensure the quantity is strictly positive."""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than zero.'))

    def _create_stock_transfer(self):
        """Create an outgoing transfer for the custody product."""
        picking_model = self.env['stock.picking'].sudo()
        picking_type_model = self.env['stock.picking.type'].sudo()
        warehouse_model = self.env['stock.warehouse'].sudo()
        for record in self:
            if record.stock_picking_id:
                continue
            company = record.company_id
            source = (company.custody_stock_source_location_id
                      or getattr(company, 'kio_source_location_id', False))
            destination = (
                record.employee_id.custody_location_id  # NEW: use employee-specific custody location
                or company.custody_stock_destination_location_id
                or getattr(company, 'kio_employee_location_id', False)
            )

            # Get the product
            product = record.custody_property_id.product_id
            if not product:
                raise UserError(_("Please set a product on %s to move stock.") % record.custody_property_id.name)

            # Source location: company stock source
            source = record.company_id.custody_stock_source_location_id \
                    or getattr(record.company_id, 'kio_source_location_id', False)

            # Destination location: now comes from employee field, not inventory settings
            destination = record.employee_id.custody_location_id
            if not source or not destination:
                raise UserError(_("Please configure the custody source in Inventory settings "
                                "and select an employee custody location."))
            if record.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than zero.'))
            warehouse = warehouse_model.search([('company_id', '=', company.id)], limit=1)
            picking_type = warehouse.out_type_id if warehouse else False

            destination = record.employee_id.custody_location_id or destination
            if not picking_type:
                picking_type = picking_type_model.search([
                    ('code', '=', 'outgoing'),
                    '|', ('warehouse_id.company_id', '=', company.id),
                         ('warehouse_id', '=', False),
                    '|', ('company_id', '=', company.id),
                         ('company_id', '=', False),
                ], limit=1)
            if not picking_type:
                raise UserError(_("No delivery operation type available for %s.")
                                % company.name)
            partner = (record.employee_id.user_id.partner_id
                       or record.employee_id.work_contact_id
                       or record.employee_id.address_home_id
                       or self.env.user.partner_id)
            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': source.id,
                'location_dest_id': destination.id,
                'origin': record.name,
                'company_id': company.id,
                'partner_id': partner.id if partner else False,
                'move_ids_without_package': [(0, 0, {
                    'name': product.display_name,
                    'product_id': product.id,
                    'product_uom_qty': record.quantity,
                    'product_uom': product.uom_id.id,
                    'location_id': source.id,
                    'location_dest_id': destination.id,
                    'company_id': company.id,
                })],
            }
            picking = picking_model.create(picking_vals)
            picking.action_confirm()
            picking.action_assign()
            picking.move_ids_without_package._set_quantity_done(record.quantity)
            picking.with_context(skip_backorder=True,
                                 skip_delivery_approval=True).button_validate()
            record.stock_picking_id = picking.id

    def _create_stock_return_transfer(self):
        """Create an incoming transfer when custody is returned."""
        picking_model = self.env['stock.picking'].sudo()
        picking_type_model = self.env['stock.picking.type'].sudo()
        warehouse_model = self.env['stock.warehouse'].sudo()

        for record in self:
            if record.stock_return_picking_id:
                continue
            if not record.stock_picking_id:
                continue

            company = record.company_id

            # ✅ CORRECT FLOW
            source = record.employee_id.custody_location_id   # FROM employee
            destination = company.custody_stock_source_location_id  # TO company

            # ✅ Clean validation
            if not source:
                raise UserError(_("Please set a Custody Location on the Employee."))

            if not destination:
                raise UserError(_("Please configure the custody source location in Inventory settings."))

            product = record.custody_property_id.product_id
            if not product:
                raise UserError(_("Please set a product on %s to move stock.")
                                % record.custody_property_id.name)

            if record.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than zero.'))

            warehouse = warehouse_model.search([('company_id', '=', company.id)], limit=1)
            picking_type = warehouse.in_type_id if warehouse else False

            if not picking_type:
                picking_type = picking_type_model.search([
                    ('code', '=', 'incoming'),
                    '|', ('warehouse_id.company_id', '=', company.id), ('warehouse_id', '=', False),
                    '|', ('company_id', '=', company.id), ('company_id', '=', False),
                ], limit=1)

            if not picking_type:
                raise UserError(_("No receipt operation type available for %s.") % company.name)

            picking_vals = {
                'picking_type_id': picking_type.id,
                'location_id': source.id,
                'location_dest_id': destination.id,
                'origin': _('%s Return') % record.name,
                'company_id': company.id,
                # ❌ REMOVE partner_id (multi-company issue)
                'move_ids_without_package': [(0, 0, {
                    'name': product.display_name,
                    'product_id': product.id,
                    'product_uom_qty': record.quantity,
                    'product_uom': product.uom_id.id,
                    'location_id': source.id,
                    'location_dest_id': destination.id,
                    'company_id': company.id,
                })],
            }

            picking = picking_model.create(picking_vals)
            picking.action_confirm()
            picking.action_assign()
            picking.move_ids_without_package._set_quantity_done(record.quantity)
            picking.with_context(skip_backorder=True,
                                skip_delivery_approval=True).button_validate()

            record.stock_return_picking_id = picking.id
    @api.constrains('employee_id')
    def _check_employee_location(self):
        for record in self:
            if record.state == 'delivered' and not record.employee_id.custody_location_id:
                raise ValidationError(
                    "Please set a Custody Location on the Employee before delivering items."
                )
