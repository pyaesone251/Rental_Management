# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RentalReturnWizard(models.TransientModel):
    """
    CONCEPT: TransientModel vs Model ကွာခြားချက်။
    - models.Model         -> ထာဝရ data, အမြဲသိမ်းထားတယ် (equipment, order...)
    - models.TransientModel -> interaction တစ်ခုတည်းအတွက် ယာယီ data (wizard တွေ)။
      row တွေကို cron job တစ်ခုက နာရီအနည်းငယ်/ရက်အနည်းငယ်အကြာမှာ auto-delete လုပ်ပေးတယ်။
    Wizard တွေက "user ကို မေးခွန်းအနည်းငယ် မေးပြီးမှ တစ်ခုခု လုပ်ဆောင်ပေး" ဆိုတဲ့ flow ကို
    core business model ကို မရှုပ်ထွေးအောင် Odoo က ဘယ်လို handle လုပ်လဲဆိုတာ ပြသတာပါ။
    """
    _name = 'rental.return.wizard'
    _description = 'Process Equipment Return'

    rental_order_id = fields.Many2one(
        comodel_name='rental.order',
        string='Rental Order',
        required=True,
    )
    expected_return_date = fields.Date(string='Expected Return Date', readonly=True)
    actual_return_date = fields.Date(
        string='Actual Return Date',
        required=True,
        default=fields.Date.context_today,
    )
    equipment_condition = fields.Selection(
        selection=[
            ('good', 'Good Condition'),
            ('damaged', 'Damaged'),
        ],
        string='Condition on Return',
        default='good',
        required=True,
    )
    late_days = fields.Integer(string='Late Days', compute='_compute_late_fee')
    daily_rate = fields.Float(related='rental_order_id.daily_rate', string='Daily Rate', readonly=True)
    late_fee_amount = fields.Float(string='Calculated Late Fee', compute='_compute_late_fee', store=False)
    damage_fee = fields.Float(string='Damage Fee', default=0.0)

    @api.depends('actual_return_date', 'expected_return_date', 'daily_rate')
    def _compute_late_fee(self):
        """
        CONCEPT: wizard ထဲက business logic - late fee = နောက်ကျတဲ့ ရက်တစ်ရက်ကို daily rate x 1.5
        ဒါက related field (daily_rate) ကို depend လုပ်တဲ့ compute method ကို ဥပမာပြထားတာပါ။
        """
        for wizard in self:
            late_days = 0
            if wizard.actual_return_date and wizard.expected_return_date:
                delta = (wizard.actual_return_date - wizard.expected_return_date).days
                late_days = max(delta, 0)
            wizard.late_days = late_days
            wizard.late_fee_amount = late_days * wizard.daily_rate * 1.5

    @api.constrains('actual_return_date')
    def _check_actual_return_date(self):
        for wizard in self:
            if wizard.rental_order_id.date_start and wizard.actual_return_date < wizard.rental_order_id.date_start:
                raise ValidationError(_("Actual return date cannot be before the pickup date."))

    def action_confirm_return(self):
        """
        CONCEPT: wizard ရဲ့ "Confirm" button method။
        user ရိုက်ထည့်ထားတဲ့ data တွေကို ဖတ်ပြီး၊ real rental.order နဲ့
        rental.equipment record တွေပေါ်ကို ပြန်ရေးထည့်ပေးတယ်၊ နောက်ဆုံးမှာ
        popup ကို ပိတ်ပေးတယ် (action မပြန်ပေးဘဲ False ပြန်တာမျိုးမဟုတ်ဘဲ act_window_close သုံးတယ်)။
        """
        self.ensure_one()
        order = self.rental_order_id

        total_late_fee = self.late_fee_amount + self.damage_fee

        order.write({
            'state': 'returned',
            'date_actual_return': self.actual_return_date,
            'late_fee': total_late_fee,
        })

        # equipment condition ပေါ်မူတည်ပြီး equipment status ကို update လုပ်တယ်
        order.equipment_id.state = 'maintenance' if self.equipment_condition == 'damaged' else 'available'

        # CONCEPT: order ရဲ့ chatter ပေါ်မှာ message တစ်ခု post လုပ်တာ (mail.thread feature)
        order.message_post(
            body=_(
                "Equipment returned on %s. Condition: %s. Late fee charged: %.2f"
            ) % (self.actual_return_date, self.equipment_condition, total_late_fee)
        )

        return {'type': 'ir.actions.act_window_close'}  # CONCEPT: wizard popup ကို ပိတ်ပေးတယ်
