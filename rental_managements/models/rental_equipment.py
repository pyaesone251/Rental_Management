# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RentalEquipment(models.Model):
    """
    CONCEPT: Model အခြေခံ definition။
    _name က နေရာတိုင်းမှာ သုံးမယ့် technical name ပါ (DB table က rental_equipment ဖြစ်သွားမယ်)။
    _description က dev mode / log တွေမှာ ပေါ်ပါတယ်။
    _order က search/tree view တွေမှာ default sort order ကို သတ်မှတ်ပါတယ်။
    """
    _name = 'rental.equipment'
    _description = 'Rental Equipment'
    _order = 'name asc'
    # CONCEPT: mail.thread ကို inherit လုပ်ရင် ဒီ model မှာ chatter (log/track changes) ရလာမယ်
    # _inherit = ['mail.thread', 'main.activity.mixin']

    name = fields.Char(string='Equipment Name', required=True, tracking=True)
    code = fields.Char(string='Internal Code', copy=False)
    description = fields.Text(string='Description')

    # CONCEPT: Selection field = ရွေးစရာ fix လုပ်ထားတဲ့ dropdown, DB မှာ varchar column အဖြစ် သိမ်းတယ်
    # ဒါက ရိုးရိုး "status" field ပါ (rental.order ထဲက အပြည့်အစုံ workflow state နဲ့ မတူပါ)
    state = fields.Selection(
        selection=[
            ('available', 'Available'),
            ('rented', 'Rented Out'),
            ('maintenance', 'Under Maintenance'),
        ],
        string='Status',
        default='available',
        tracking=True,
    )

    daily_rate = fields.Float(string='Daily Rate', required=True, default=0.0)

    # CONCEPT: One2many - equipment တစ်ခုက rental order များစွာမှာ ပါဝင်နိုင်တယ်။
    # ဒီနေရာက 'equipment_id' က rental.order ပေါ်က Many2one field name နဲ့ ကိုက်ညီမှ ရမယ်။
    rental_order_ids = fields.One2many(
        comodel_name='rental.order',
        inverse_name='equipment_id',
        string='Rental History',
    )

    # CONCEPT: Computed field - rental order အရေအတွက်ကို ပြတယ်၊
    # rental_order_ids ပြောင်းတိုင်း (@api.depends ကြောင့်) အလိုအလျောက် ပြန်တွက်ပေးမယ်။
    rental_count = fields.Integer(string='Times Rented', compute='_compute_rental_count')

    active = fields.Boolean(default=True)  # CONCEPT: 'active' field က archive လုပ်ထားတဲ့ record တွေကို auto-filter လုပ်ပေးတယ်

    @api.depends('rental_order_ids')
    def _compute_rental_count(self):
        """
        CONCEPT: Computed field method ရေးနည်း။
        - 'self' ကို loop လှည့်ရမယ် (recordset တစ်ခုမှာ record တစ်ခုထက်ပိုပြီး ပါနိုင်တယ်)။
        - loop ထဲက record တိုင်းအတွက် value ကို အမြဲတမ်း assign ပေးရမယ်၊
          မဟုတ်ရင် Odoo က value မရတဲ့ record အတွက် error တက်လိမ့်မယ်။
        """
        for equipment in self:
            equipment.rental_count = len(equipment.rental_order_ids)

    # CONCEPT: SQL constraint - database level မှာ enforce လုပ်တာ၊ မြန်ဆန်ပြီး
    # ရိုးရှင်းတဲ့ uniqueness/range check တွေအတွက် အသင့်တော်ဆုံးပါ။
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Equipment code must be unique!'),
        ('daily_rate_positive', 'CHECK(daily_rate >= 0)', 'Daily rate cannot be negative!'),
    ]

    @api.constrains('daily_rate')
    def _check_daily_rate(self):
        """
        CONCEPT: Python constraint - SQL နဲ့ check လုပ်ဖို့ ရှုပ်သွားတဲ့အခါ သုံးပါ
        (ဥပမာ - field တစ်ခုထက်ပိုပြီး နှိုင်းယှဉ်ရတာ၊ method ခေါ်ရတာမျိုး)။
        @api.constrains ထဲမှာ ဖော်ပြထားတဲ့ field တွေကို create/write လုပ်တိုင်း အလိုအလျောက် run လိမ့်မယ်။
        """
        for equipment in self:
            if equipment.daily_rate > 100000:
                raise ValidationError(
                    "Daily rate for %s looks unusually high. Please double-check it."
                    % equipment.name
                )

    def name_get(self):
        """
        CONCEPT: name_get က record ရဲ့ name ကို ဘယ်လို ပြသမလဲဆိုတာ customize လုပ်ပေးတယ်
        (ဥပမာ - Many2one dropdown, breadcrumb တွေမှာ)။ ဒီနေရာမှာ "[CODE] Name" ပုံစံ ပြပေးမယ်။
        မှတ်ချက်: Odoo 17+ မှာ name_get အစား _compute_display_name ကို override
        လုပ်လည်း ရပါတယ် - ဒီနေရာမှာတော့ name_get က codebase အနှံ့မှာ ကျယ်ကျယ်ပြန့်ပြန့်
        သုံးနေတုန်းဆိုတော့ ရှင်းရှင်းလင်းလင်း နားလည်နိုင်ဖို့ ဒီကနေ စလေ့လာပါ။
        """
        result = []
        for equipment in self:
            label = f"[{equipment.code}] {equipment.name}" if equipment.code else equipment.name
            result.append((equipment.id, label))
        return result
