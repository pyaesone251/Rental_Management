# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class RentalOrder(models.Model):
    _name = 'rental.order'
    _description = 'Rental Order'
    _order = 'date_start desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # chatter + activity (follow-up, reminder) ရဖို့
    _rec_name = 'name'

    # CONCEPT: sequence ကနေ auto-generate လုပ်တဲ့ reference number၊ data/rental_sequence.xml ထဲက ir.sequence နဲ့ set လုပ်ထားတယ်
    name = fields.Char(string='Order Reference', copy=False, readonly=True, default='New')

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        tracking=True,
    )
    equipment_id = fields.Many2one(
        comodel_name='rental.equipment',
        string='Equipment',
        required=True,
        tracking=True,
        # CONCEPT: domain က dropdown ထဲမှာ ဘယ် record တွေ ပြမလဲ ကန့်သတ်ပေးတယ် -
        # 'available' state ရှိတဲ့ equipment ကိုသာ ရွေးလို့ရမယ်
        domain="[('state', '=', 'available')]",
    )

    date_start = fields.Date(string='Pickup Date', required=True, default=fields.Date.context_today)
    date_end = fields.Date(string='Planned Return Date', required=True)
    date_actual_return = fields.Date(string='Actual Return Date', readonly=True, copy=False)

    # CONCEPT: WORKFLOW STATE MACHINE ပိုင်း
    # ဒီ selection field နဲ့ အောက်က button method တွေ (action_confirm, action_pickup, စသဖြင့်)
    # ပေါင်းစပ်ပြီး Odoo ရဲ့ classic workflow pattern ကို implement လုပ်ထားတာပါ။
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('picked_up', 'Picked Up'),
            ('returned', 'Returned'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        copy=False,
    )

    daily_rate = fields.Float(
        string='Daily Rate',
        related='equipment_id.daily_rate',  # CONCEPT: related field - equipment ရဲ့ rate ကို mirror လုပ်ပြထားတယ်
        readonly=True,
        store=True,  # SQL-level search/report တွေမှာ သုံးလို့ရအောင် store လုပ်ထားတယ်
    )

    # CONCEPT: Computed ဖြစ်ပြီး store လုပ်ထားတဲ့ field, @api.depends နဲ့ ချိတ်ထားတယ်။
    # 'store=True' ဆိုတာ DB column အစစ်တစ်ခုအဖြစ် သိမ်းတယ် (search/group_by လုပ်လို့ရတယ်)၊
    # date_start (သို့) date_end ပြောင်းတိုင်း အလိုအလျောက် ပြန်တွက်ပေးမယ်။
    rental_days = fields.Integer(string='Rental Days', compute='_compute_rental_days', store=True)

    amount_total = fields.Float(string='Total Amount', compute='_compute_amount_total', store=True)

    late_fee = fields.Float(string='Late Fee', copy=False, default=0.0)
    notes = fields.Text(string='Internal Notes')

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,  # CONCEPT: env ကနေ ခေါ်တဲ့ lambda သုံးပြီး default သတ်မှတ်နည်း
    )

    @api.depends('date_start', 'date_end')
    def _compute_rental_days(self):
        for order in self:
            if order.date_start and order.date_end and order.date_end >= order.date_start:
                order.rental_days = (order.date_end - order.date_start).days + 1
            else:
                order.rental_days = 0

    @api.depends('rental_days', 'daily_rate', 'late_fee')
    def _compute_amount_total(self):
        for order in self:
            order.amount_total = (order.rental_days * order.daily_rate) + order.late_fee

    @api.onchange('date_start')
    def _onchange_date_start(self):
        """
        CONCEPT: @api.onchange က UI (form view) ထဲမှာသာ run ပါတယ်၊
        user ကို save မလုပ်ခင် live feedback ပေးဖို့ / field တခြားတွေ auto-fill လုပ်ဖို့ သုံးတယ်။
        code (သို့) API ကနေ ခေါ်တဲ့ create()/write() တွေမှာတော့ run မှာ မဟုတ်ပါ -
        အဲ့ဒီလို logic တွေအတွက်တော့ @api.constrains နဲ့ compute method တွေကို သုံးရမယ်။
        """
        if self.date_start and (not self.date_end or self.date_end < self.date_start):
            self.date_end = self.date_start + timedelta(days=1)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for order in self:
            if order.date_start and order.date_end and order.date_end < order.date_start:
                raise ValidationError(_("Return date cannot be before the pickup date."))

    @api.model_create_multi
    def create(self, vals_list):
        """
        CONCEPT: sequence number auto-generate ဖို့ create() ကို override လုပ်ထားတယ်။
        @api.model_create_multi ဆိုတာ ဒီ method က vals dict LIST (batch creation) ကို
        လက်ခံရယူတယ် - ဒါက modern Odoo standard ပါ (တစ်ခုချင်း create လုပ်တာထက် ပိုမြန်တယ်)။
        ORM က actual insert ကို လုပ်ဆောင်နိုင်ဖို့ super() ကို အမြဲခေါ်ပေးရမယ်။
        """
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('rental.order') or 'New'
        return super().create(vals_list)

    # ---------------------------------------------------------------------
    # WORKFLOW ACTIONS (form view ထဲက button တွေက ခေါ်တာ)
    # ---------------------------------------------------------------------

    def action_confirm(self):
        for order in self:
            if order.state != 'draft':
                raise UserError(_("Only draft orders can be confirmed."))
            order.state = 'confirmed'

    def action_pickup(self):
        for order in self:
            if order.state != 'confirmed':
                raise UserError(_("Order must be confirmed before pickup."))
            order.state = 'picked_up'
            order.equipment_id.state = 'rented'  # CONCEPT: related record တစ်ခုကို write ပြန်လုပ်နည်း

    def action_cancel(self):
        for order in self:
            if order.state in ('returned',):
                raise UserError(_("Cannot cancel an order that is already returned."))
            order.state = 'cancelled'
            if order.equipment_id.state == 'rented':
                order.equipment_id.state = 'available'

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def action_open_return_wizard(self):
        """
        CONCEPT: button တစ်ခုက WIZARD ကို ဘယ်လို ဖွင့်လဲဆိုတာ ဒီမှာ ပြထားတယ်။
        state ကို တိုက်ရိုက်ပြောင်းမယ့်အစား, client ကို rental.return.wizard
        popup ကို ဖွင့်ဖို့ action dict တစ်ခု ပြန်ပေးလိုက်တယ်၊ context data
        (လက်ရှိ order ရဲ့ id) ကို ကြိုတင် fill ထားပေးတယ်။
        """
        self.ensure_one()  # CONCEPT: safety check - ဒီ action က record 1 ခုအတွက်ပဲ အဓိပ္ပါယ်ရှိတယ်
        if self.state != 'picked_up':
            raise UserError(_("Only picked-up orders can be returned."))
        return {
            'name': _('Process Return'),
            'type': 'ir.actions.act_window',
            'res_model': 'rental.return.wizard',
            'view_mode': 'form',
            'target': 'new',  # 'new' = popup dialog အနေနဲ့ ဖွင့်တယ်
            'context': {
                'default_rental_order_id': self.id,
                'default_expected_return_date': self.date_end,
            },
        }
