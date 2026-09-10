from odoo import api,fields,models
from odoo.exceptions import ValidationError

class RentalEquipment(models.Model):
    _name = 'rental.equipment'
    _description = 'Rental Equipment'
    _order = 'name asc'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char('Equipment Name',tracking=True)
    code = fields.Char('Internal Code',copy=False)
    description = fields.Text('Description')
    state = fields.Selection([
        ('available','Available'),
        ('rented','Rented'),
        ('maintenance','Maintenance')
    ],string='Status',default='available',tracking=True)
    daily_rate = fields.Float('Daily Rate',default=0.0)
    active =fields.Boolean(default=True)

    rental_order_ids = fields.One2many('rental.order','equipment_id',string='Rental History')
    rental_count = fields.Integer('Times Rented',compute="_compute_rental_count")

    _sql_constraints = [
        ('code_unique','UNIQUE(code)','Equipment code must be unique'),
        ('daily_rate_positive','CHECK(daily_rate >= 0)','Daily rate cannot be negative')
    ]

    @api.constrains('daily_rate')
    def _check_daily_rate(self):
        for rec in self:
            if rec.daily_rate > 100000:
                raise ValidationError(
                    "Daily rate for %s looks unusually high. Please double-check it."
                    % rec.name
                )

    @api.depends('rental_order_ids')
    def _compute_rental_count(self):
        for rec in self:
            rec.rental_count = len(rec.rental_order_ids)

    @api.depends('code','name')
    def _compute_display_name(self):
        for rec in self:
            if rec.code:
                rec.display_name = f"[{rec.code}][{rec.name}]"
            else:
                rec.display_name = rec.name or ""