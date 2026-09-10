from odoo import api,fields,models,_
from odoo.exceptions import ValidationError,UserError
from datetime import timedelta

class RentalOrder(models.Model):
    _name = 'rental.order'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char('Order Reference',copy=False,default='New',readonly=True)
    partner_id = fields.Many2one('res.partner',string='Customer',tracking=True)
    equipment_id = fields.Many2one('rental.equipment',string='Equipment',tracking=True)
    date_start = fields.Date('Picking Date',default=fields.Date.context_today)
    date_end = fields.Date('Return Date')
    date_actual_return = fields.Date('Actual Return Date',copy=False)
    state = fields.Selection([
        ('draft','Draft'),
        ('confirmed','Confirmed'),
        ('picked_up','Picked Up'),
        ('returned','Returned'),
        ('cancelled','Cancelled')
    ],string='Status',default='draft',tracking=True,copy=False)
    daily_rate = fields.Float(related="equipment_id.daily_rate",string='Daily Rate',readonly=True,store=True)

    rental_days = fields.Integer('Rental Days',compute="_compute_rental_days",store=True)
    total_amount = fields.Float('Total Amount',compute="_compute_total_amount",store=True)
    late_fee = fields.Float('Late Fee',copy=False,default=0.0)
    notes = fields.Text('Internal Notes')
    company_id = fields.Many2one('res.company',string='Company',default=lambda c : c.env.company)

    @api.depends('date_start','date_end')
    def _compute_rental_days(self):
        for order in self:
            if order.date_start and order.date_end and order.date_end >= order.date_start:
                order.rental_days = (order.date_end - order.date_start).days +1
            else:
                order.rental_days = 0

    @api.depends('rental_days','daily_rate','late_fee')
    def _compute_total_amount(self):
        for order in self:
            order.total_amount = (order.rental_days * order.daily_rate) + order.late_fee

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start and (not self.date_end or self.date_end < self.date_start):
            self.date_end = self.date_start + timedelta(days=1)

    @api.constrains('date_start','date_end')
    def _check_dates(self):
        for order in self:
            if order.date_start and order.date_end and order.date_end < order.date_start:
                raise ValidationError(_("Return date cannot be before tha date start"))

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('name','New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.order')or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Only draft orders can be confirmed."))
            rec.state = 'confirmed'

    def action_pickup(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(_("Order must be confirmed before pickup"))
            rec.state = 'picked_up'
            rec.equipment_id.state = 'rented'

    def action_cancel(self):
        for rec in self:
            if rec.state in('returned'):
                raise UserError(_("Cannot be an order that is already returned."))
            rec.state = 'cancelled'
            if rec.equipment_id.state == 'rented':
               rec.equipment_id.state = 'available'

    def action_reset(self):
        self.state = 'draft'

    def action_open_renturn_wizard(self):
        self.ensure_one()
        if self.state != 'picked_up':
            raise UserError(_("Only picked_up orders can be returned."))
        return {
            'name':_('Process Return'),
            'type':'ir.actions.act_window',
            'res_model':'rental.return.wizard',
            'view_mode':'form',
            'target':'new',
            'context' : {
                'default_rental_order_id':self.id,
                'default_expected_return_date':self.date_end
            },
        }