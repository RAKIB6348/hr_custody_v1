from odoo import fields, models, api


class HrCustodyTransfer(models.Model):
    _name = 'hr.custody.transfer'
    _description = 'HR Custody Transfer'
    _rec_name = 'name'

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        copy=False,
        default='New',
    )

    employee_from_id = fields.Many2one(
        'hr.employee',
        string='Employee From',
        required=True,
    )

    department_from_id = fields.Many2one(
        'hr.department',
        string='From Department',
        related='employee_from_id.department_id',
        store=True,
        readonly=True,
    )

    company_from_id = fields.Many2one(
        'res.company',
        string='Company From',
        related='employee_from_id.company_id',
        store=True,
        readonly=True,
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        related='employee_from_id.custody_location_id',
        store=True,
        readonly=True,
    )
    employee_to_id = fields.Many2one(
        'hr.employee',
        string='Employee To',
        required=True,
    )

    department_to_id = fields.Many2one(
        'hr.department',
        string='To Department',
        related='employee_to_id.department_id',
        store=True,
        readonly=True,
    )

    company_to_id = fields.Many2one(
        'res.company',
        string='Company To',
        related='employee_to_id.company_id',
        store=True,
        readonly=True,
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        related='employee_to_id.custody_location_id',
        store=True,
        readonly=True,
    )
    transfer_date = fields.Date(
        string='Transfer Date',
        required=True,
        default=fields.Date.context_today,
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
    )

    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]",
    )

    custody_property_id = fields.Many2one(
        'custody.property',
        string='Asset',
        readonly=True,
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
