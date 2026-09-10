from odoo import api,fields,models,_
from odoo.exceptions import ValidationError

class RentalReturnWizard(models.TransientModel):
    _name = 'rental.return.wizard'
    _description = 'Rental Return Wizard'

    rental_order_id = fields.Many2one('rental.order',string='Rental Order')
    expected_return_date = fields.Date('Expected Return Date',readonly=True)
    actual_return_date = fields.Date('Actual Return Date',default=fields.Date.context_today)
    equipment_condition = fields.Selection([
        ('good','Good'),
        ('damaged','Damaged')
    ],string='Condition on Return',default='good')
    late_days = fields.Integer('Late Days',compute="_compute_late_fee")
    daily_rate = fields.Float(related='rental_order_id.daily_rate',string='Daily Rate',readonly=True)
    late_fee_amount = fields.Float('Calculated Late Fee',compute="_compute_late_fee",store=False)
    damage_fee = fields.Float('Damage Fee',default=0.0)

    @api.depends('actual_return_date','expected_return_date','daily_rate')
    def _compute_late_fee(self):
        for rec in self:
            late_days = 0
            if rec.actual_return_date and rec.expected_return_date:
                delta = (rec.actual_return_date - rec.expected_return_date).days
                late_days = max(delta,0)
            rec.late_days = late_days
            rec.late_fee_amount = late_days * rec.daily_rate * 1.5

    @api.constrains('actual_return_date')
    def _check_actual_return_date(self):
        for rec in self:
            if rec.rental_order_id.date_start and rec.actual_return_date < rec.rental_order_id.date_start:
                raise ValidationError(_("Actual return date cannot be before the pick up date"))


    def action_confirm_return(self):
        self.ensure_one()
        order = self.rental_order_id
        total_late_fee = self.late_fee_amount + self.damage_fee

        order.write({
            'state':'returned',
            'date_actual_return':self.actual_return_date,
            'late_fee':total_late_fee
        })

        order.equipment_id.state = 'maintenance' if self.equipment_condition == 'damaged' else 'available'
        order.message_post(
            body=_(
                "Equipment returned on %s. Condition: %s. Late fee charged: %.2f"
                            ) % (self.actual_return_date, self.equipment_condition, total_late_fee)
        )
        return {'type':'ir.actions.act_window_close'}