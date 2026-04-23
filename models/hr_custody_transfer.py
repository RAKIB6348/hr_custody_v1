from odoo import fields, models, api
from odoo.exceptions import ValidationError


class HrCustodyTransfer(models.Model):
    _name = 'hr.custody.transfer'
    _description = 'HR Custody Transfer'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
    )

    employee_from_id = fields.Many2one(
        'hr.employee',
        string='Employee From',
        required=True,
        tracking=True,
    )

    department_from_id = fields.Many2one(
        'hr.department',
        string='From Department',
        related='employee_from_id.department_id',
        store=True,
        readonly=True,
        tracking=True,
    )

    company_from_id = fields.Many2one(
        'res.company',
        string='Company From',
        related='employee_from_id.company_id',
        store=True,
        readonly=True,
        tracking=True,
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        related='employee_from_id.custody_location_id',
        store=True,
        readonly=True,
        tracking=True,
    )
    employee_to_id = fields.Many2one(
        'hr.employee',
        string='Employee To',
        required=True,
        tracking=True,
    )

    department_to_id = fields.Many2one(
        'hr.department',
        string='To Department',
        related='employee_to_id.department_id',
        store=True,
        readonly=True,
        tracking=True,
    )

    company_to_id = fields.Many2one(
        'res.company',
        string='Company To',
        related='employee_to_id.company_id',
        store=True,
        readonly=True,
        tracking=True,
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        related='employee_to_id.custody_location_id',
        store=True,
        readonly=True,
        tracking=True,
    )
    transfer_date = fields.Date(
        string='Transfer Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        tracking=True,
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]",
        tracking=True,
    )

    custody_property_id = fields.Many2one(
        'custody.property',
        string='Asset',
        readonly=True,
        tracking=True,
    )

    quantity = fields.Integer(
        string='Quantity',
        default=1,
        tracking=True,
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('transfer', 'Transferred'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'hr.custody.transfer'
                ) or 'New'
        return super().create(vals_list)

    def action_transfer(self):
        self.state = 'transfer'

    def action_cancel(self):
        self.state = 'cancel'

    def action_reset(self):
        self.state = 'draft'

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError("Quantity must be greater than 0")
