from odoo import models


class FixedAssetInventoryXlsx(models.AbstractModel):
    _name = 'report.hr_custody.fixed_asset_inventory_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Fixed Asset Inventory XLSX'

    def _headers(self):
        return [
            'SL',
            'EmpID',
            'Emp Name',
            'Designation',
            'Department',
            'Company',
            'Location',
            'AssetID',
            'Asset Name',
            'Brand',
            'Model',
            'Specification',
            'Serial/Service Tag',
            'Purchase Date',
            'Vendor Name',
            'Price',
            'Purchase Details',
            'Received By',
            'Remark',
        ]

    def _employee_identifier(self, employee):
        return employee.identification_id or employee.barcode or employee.id or ''

    def _location_name(self, location):
        if not location:
            return ''
        return (location.complete_name or '').split('/')[-1] or location.name or ''

    def _row_values(self, record, index):
        employee = record.employee_id
        asset = record.custody_property_id
        return [
            index,
            self._employee_identifier(employee),
            employee.name or '',
            employee.job_id.name or '',
            employee.department_id.name or '',
            employee.company_id.name or record.company_id.name or '',
            self._location_name(employee.custody_location_id),
            asset.asset_id or '',
            asset.name or '',
            asset.brand_id.name or '',
            asset.asset_model or '',
            asset.specification or '',
            asset.lot_id.name or '',
            str(asset.purchase_date or ''),
            asset.vendor_name or '',
            asset.price or 0.0,
            asset.purchase_details or '',
            asset.received_by or '',
            asset.remark or '',
        ]

    def generate_xlsx_report(self, workbook, data, records):
        sheet = workbook.add_worksheet('Fixed Assets')
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 18,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': '#0070C0',
            'bg_color': '#F2D8C8',
            'border': 1,
        })
        header_format = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#F2D8C8',
        })
        text_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'top',
        })
        center_format = workbook.add_format({
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        amount_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
        })

        headers = self._headers()
        sheet.set_row(0, 30)
        sheet.merge_range(0, 0, 0, len(headers) - 1,
                          'Fixed Asset Inventory | Bangla Trac Group',
                          title_format)

        widths = [6, 12, 24, 20, 18, 24, 14, 12, 22, 12, 18, 32, 18, 14, 20, 12, 20, 18, 18]
        for col, width in enumerate(widths):
            sheet.set_column(col, col, width)
            sheet.write(2, col, headers[col], header_format)

        for row_index, record in enumerate(records, start=3):
            values = self._row_values(record, row_index - 2)
            for col_index, value in enumerate(values):
                fmt = amount_format if headers[col_index] == 'Price' else text_format
                if headers[col_index] in {'SL', 'EmpID', 'Purchase Date'}:
                    fmt = center_format
                sheet.write(row_index, col_index, value, fmt)
