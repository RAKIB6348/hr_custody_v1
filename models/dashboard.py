from datetime import timedelta

from odoo import _, api, fields, models
from odoo.tools import format_date, html_escape


class HrCustodyDashboard(models.TransientModel):
    _name = 'hr.custody.dashboard'
    _description = 'HR Custody Dashboard'
    _rec_name = 'name'

    name = fields.Char(default='Custody Dashboard', readonly=True)
    total_assets = fields.Integer(readonly=True, compute='_compute_metrics')
    assigned_assets = fields.Integer(readonly=True, compute='_compute_metrics')
    available_assets = fields.Integer(readonly=True, compute='_compute_metrics')
    pending_approval = fields.Integer(readonly=True, compute='_compute_metrics')
    overdue_returns = fields.Integer(readonly=True, compute='_compute_metrics')
    due_soon = fields.Integer(readonly=True, compute='_compute_metrics')
    today_count = fields.Integer(readonly=True, compute='_compute_metrics')
    draft_count = fields.Integer(readonly=True, compute='_compute_metrics')
    approved_count = fields.Integer(readonly=True, compute='_compute_metrics')
    delivered_count = fields.Integer(readonly=True, compute='_compute_metrics')
    returned_count = fields.Integer(readonly=True, compute='_compute_metrics')
    rejected_count = fields.Integer(readonly=True, compute='_compute_metrics')

    brand_summary_html = fields.Html(readonly=True, compute='_compute_summaries')
    department_summary_html = fields.Html(readonly=True, compute='_compute_summaries')
    due_soon_html = fields.Html(readonly=True, compute='_compute_summaries')

    @api.model
    def action_open_dashboard(self):
        dashboard = self.create({'name': 'Custody Dashboard'})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Custody Dashboard'),
            'res_model': 'hr.custody.dashboard',
            'view_mode': 'form',
            'res_id': dashboard.id,
            'target': 'current',
        }

    def name_get(self):
        return [(record.id, 'Custody Dashboard') for record in self]

    def _active_custody_domain(self):
        return [('state', 'in', ['approved', 'delivered'])]

    @api.depends()
    def _compute_metrics(self):
        property_model = self.env['custody.property']
        custody_model = self.env['hr.custody']
        today = fields.Date.context_today(self)
        due_limit = today + timedelta(days=7)

        total_assets = property_model.search_count([])
        active_custodies = custody_model.search(self._active_custody_domain())
        assigned_assets = len(active_custodies.mapped('custody_property_id'))
        today_count = custody_model.search_count([('date_request', '=', today)])
        pending_approval = custody_model.search_count([('state', '=', 'to_approve')])
        draft_count = custody_model.search_count([('state', '=', 'draft')])
        approved_count = custody_model.search_count([('state', '=', 'approved')])
        delivered_count = custody_model.search_count([('state', '=', 'delivered')])
        returned_count = custody_model.search_count([('state', '=', 'returned')])
        rejected_count = custody_model.search_count([('state', '=', 'rejected')])
        overdue_returns = custody_model.search_count([
            ('state', 'in', ['approved', 'delivered']),
            ('return_date', '!=', False),
            ('return_date', '<', today),
        ])
        due_soon = custody_model.search_count([
            ('state', 'in', ['approved', 'delivered']),
            ('return_date', '!=', False),
            ('return_date', '>=', today),
            ('return_date', '<=', due_limit),
        ])

        for record in self:
            record.total_assets = total_assets
            record.assigned_assets = assigned_assets
            record.available_assets = max(total_assets - assigned_assets, 0)
            record.today_count = today_count
            record.pending_approval = pending_approval
            record.overdue_returns = overdue_returns
            record.due_soon = due_soon
            record.draft_count = draft_count
            record.approved_count = approved_count
            record.delivered_count = delivered_count
            record.returned_count = returned_count
            record.rejected_count = rejected_count

    @api.depends()
    def _compute_summaries(self):
        property_model = self.env['custody.property']
        custody_model = self.env['hr.custody']
        today = fields.Date.context_today(self)
        due_limit = today + timedelta(days=7)

        properties = property_model.search([])
        brand_counts = {}
        for prop in properties:
            key = prop.brand_id.name or 'No Brand'
            brand_counts[key] = brand_counts.get(key, 0) + 1

        active_custodies = custody_model.search(self._active_custody_domain())
        department_counts = {}
        for custody in active_custodies:
            key = custody.employee_id.department_id.name or 'No Department'
            department_counts[key] = department_counts.get(key, 0) + 1

        due_soon_records = custody_model.search([
            ('state', 'in', ['approved', 'delivered']),
            ('return_date', '!=', False),
            ('return_date', '>=', today),
            ('return_date', '<=', due_limit),
        ], order='return_date asc', limit=5)

        brand_html = self._render_summary_list(
            'Assets By Brand',
            sorted(brand_counts.items(), key=lambda item: (-item[1], item[0]))[:5],
            empty_label='No assets found.',
        )
        department_html = self._render_summary_list(
            'Assets By Department',
            sorted(department_counts.items(), key=lambda item: (-item[1], item[0]))[:5],
            empty_label='No assigned assets found.',
        )
        due_soon_html = self._render_due_soon_list(due_soon_records)

        for record in self:
            record.brand_summary_html = brand_html
            record.department_summary_html = department_html
            record.due_soon_html = due_soon_html

    def _render_summary_list(self, title, items, empty_label):
        if not items:
            return (
                f"<div><strong>{html_escape(title)}</strong></div>"
                f"<div>{html_escape(empty_label)}</div>"
            )
        rows = ''.join(
            f"<tr><td>{html_escape(name)}</td><td style='text-align:right;'>{count}</td></tr>"
            for name, count in items
        )
        return (
            f"<div><strong>{html_escape(title)}</strong></div>"
            "<table style='width:100%; border-collapse:collapse; margin-top:8px;'>"
            "<tbody>"
            f"{rows}"
            "</tbody></table>"
        )

    def _render_due_soon_list(self, records):
        if not records:
            return (
                "<div><strong>Assets Due Soon</strong></div>"
                "<div>No upcoming returns in the next 7 days.</div>"
            )
        rows = ''.join(
            "<tr>"
            f"<td>{html_escape(record.name or '')}</td>"
            f"<td>{html_escape(record.employee_id.name or '')}</td>"
            f"<td>{html_escape(record.custody_property_id.name or '')}</td>"
            f"<td style='text-align:right;'>{html_escape(format_date(self.env, record.return_date))}</td>"
            "</tr>"
            for record in records
        )
        return (
            "<div><strong>Assets Due Soon</strong></div>"
            "<table style='width:100%; border-collapse:collapse; margin-top:8px;'>"
            "<thead>"
            "<tr>"
            "<th style='text-align:left;'>Ref</th>"
            "<th style='text-align:left;'>Employee</th>"
            "<th style='text-align:left;'>Asset</th>"
            "<th style='text-align:right;'>Return Date</th>"
            "</tr>"
            "</thead>"
            f"<tbody>{rows}</tbody>"
            "</table>"
        )

    def _open_action(self, name, model, domain, view_mode='tree,form', context=None):
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': model,
            'view_mode': view_mode,
            'domain': domain,
            'target': 'current',
            'context': context or {},
        }

    def action_view_total_assets(self):
        return self._open_action('All Assets', 'custody.property', [])

    def action_view_assigned_assets(self):
        return self._open_action(
            'Assigned Assets',
            'hr.custody',
            self._active_custody_domain(),
        )

    def action_view_available_assets(self):
        active_asset_ids = self.env['hr.custody'].search(
            self._active_custody_domain()
        ).mapped('custody_property_id').ids
        return self._open_action(
            'Available Assets',
            'custody.property',
            [('id', 'not in', active_asset_ids)],
        )

    def action_view_pending_approval(self):
        return self._open_action(
            'Pending Approvals',
            'hr.custody',
            [('state', '=', 'to_approve')],
        )

    def action_view_overdue_returns(self):
        today = fields.Date.context_today(self)
        return self._open_action(
            'Overdue Returns',
            'hr.custody',
            [
                ('state', 'in', ['approved', 'delivered']),
                ('return_date', '!=', False),
                ('return_date', '<', today),
            ],
        )

    def action_view_due_soon(self):
        today = fields.Date.context_today(self)
        due_limit = today + timedelta(days=7)
        return self._open_action(
            'Assets Due Soon',
            'hr.custody',
            [
                ('state', 'in', ['approved', 'delivered']),
                ('return_date', '!=', False),
                ('return_date', '>=', today),
                ('return_date', '<=', due_limit),
            ],
        )

    def action_view_today(self):
        today = fields.Date.context_today(self)
        return self._open_action(
            "Today's Custodies",
            'hr.custody',
            [('date_request', '=', today)],
        )

    def action_view_draft(self):
        return self._open_action('Draft Custodies', 'hr.custody', [('state', '=', 'draft')])

    def action_view_approved(self):
        return self._open_action('Approved Custodies', 'hr.custody', [('state', '=', 'approved')])

    def action_view_delivered(self):
        return self._open_action('Delivered Custodies', 'hr.custody', [('state', '=', 'delivered')])

    def action_view_returned(self):
        return self._open_action('Returned Custodies', 'hr.custody', [('state', '=', 'returned')])

    def action_view_rejected(self):
        return self._open_action('Refused Custodies', 'hr.custody', [('state', '=', 'rejected')])
