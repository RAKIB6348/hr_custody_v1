from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one(
        'custody.brand',
        string='Brand',
        help='Brand used by custody properties and asset reports.')
    model_name = fields.Char(
        string='Model Name',
        help='Asset model name copied into custody property records.')
    specification = fields.Text(
        string='Specification',
        help='Default specification copied into custody property records.')
