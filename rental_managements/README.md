# Equipment Rental Management — Learning Module (Odoo 19)

Junior → Mid-level ဖြစ်ဖို့ လိုအပ်တဲ့ Odoo development concept တွေကို
"Equipment Rental" domain တစ်ခုတည်းနဲ့ ပြသထားတဲ့ teaching module ဖြစ်ပါတယ်။

## Install လုပ်နည်း

1. ဒီ folder ကို သင့်ရဲ့ Odoo `addons` path (custom_addons) ထဲ ကူးထည့်ပါ
2. Odoo ကို `-u all` သို့မဟုတ် Apps list refresh (`--dev=all` mode မှာ "Update Apps List") လုပ်ပါ
3. Apps menu ထဲ "Equipment Rental Management" ကို ရှာပြီး Install နှိပ်ပါ
4. Demo data ပါချင်ရင် database ကို demo data enable ထားပြီး install လုပ်ပါ

## Folder Structure ဘာကြောင့် ဒီလို ဖွဲ့ထားလဲ

```
rental_management/
├── __manifest__.py          # module metadata + data file loading order
├── __init__.py               # imports models/, wizard/
├── models/
│   ├── rental_equipment.py   # basic Model: fields, selection, sql/python constraints, One2many
│   └── rental_order.py       # core Model: state machine, computed/related fields, create() override
├── wizard/
│   ├── rental_return_wizard.py       # TransientModel example
│   └── rental_return_wizard_views.xml
├── views/                     # list/form views, statusbar workflow, menus
├── report/                    # ir.actions.report + QWeb PDF template
├── security/                  # groups + ir.model.access.csv
└── data/                      # ir.sequence for auto-numbering
```

## ဒီ Module ကနေ ဘာတွေ လေ့လာရမလဲ (Checklist)

- [ ] **Model basics** — `_name`, `_description`, `_order`, `_rec_name`
- [ ] **Field types** — Char, Text, Float, Integer, Date, Selection, Many2one, One2many
- [ ] **Computed fields** — `store=True` vs non-stored, `@api.depends`
- [ ] **Related fields** — `related='equipment_id.daily_rate'`
- [ ] **Constraints** — SQL (`_sql_constraints`) vs Python (`@api.constrains`)
- [ ] **Onchange** — `@api.onchange` for live UI feedback (not persisted logic!)
- [ ] **create() override** — `@api.model_create_multi`, calling `super()`
- [ ] **State machine pattern** — selection field + button methods that transition state
- [ ] **Wizards** — `TransientModel`, opening via `type: 'ir.actions.act_window', target: 'new'`
- [ ] **Chatter/mail.thread** — `tracking=True`, `message_post()`
- [ ] **Security** — groups, `implied_ids`, `ir.model.access.csv`
- [ ] **QWeb PDF Reports** — `ir.actions.report` + `web.external_layout`
- [ ] **View inheritance basics** — statusbar, badge decorations, stat buttons

## Try These Exercises (Mid-level ဖြစ်ဖို့ လက်တွေ့လုပ်ကြည့်ပါ)

1. **Record rule ထည့်ပါ** — Rental User group က သူ့ကိုယ်ပိုင် orders (`create_uid = uid`) ကိုပဲ မြင်ရအောင်
   `ir.rule` သုံးပြီး ရေးကြည့်ပါ (security/ folder ထဲ)။
2. **Existing view ကို inherit လုပ်ကြည့်ပါ** — အသစ် module တစ်ခု ဆောက်ပြီး
   `rental.order` form ပေါ်မှာ field အသစ်တစ်ခု xpath နဲ့ ထည့်ကြည့်ပါ။
   (ဒါဟာ "existing module ကို customize" workflow ကို လေ့ကျင့်ရာရောက်ပါတယ်)
3. **Scheduled action (`ir.cron`) ထည့်ပါ** — Overdue rentals (date_end < today, state='picked_up')
   တွေကို daily check လုပ်ပြီး activity/email reminder ပို့တဲ့ cron job ရေးကြည့်ပါ။
4. **Unit test ရေးပါ** — `TransactionCase` သုံးပြီး late fee calculation logic ကို test ရေးကြည့်ပါ
   (`tests/test_rental_order.py`, `tests/__init__.py` ထည့်ဖို့ လိုပါမယ်)။
5. **Multi-company support** — `company_id` ကို view/domain တွေမှာ ထည့်သွင်းစဉ်းစားပြီး
   record rule နဲ့ company isolation လုပ်ကြည့်ပါ။

## Common Gotchas (ကိုယ်တိုင်ကြုံဖူးမယ့် အမှားများ)

- Compute method ထဲမှာ record တစ်ခုချင်းစီအတွက် value assign မလုပ်ရင် error တက်တတ်ပါတယ်
  (loop ထဲ `for rec in self:` ကို မမေ့ပါနဲ့)
- `@api.onchange` ထဲမှာ ORM write() logic (ဥပမာ - other model ကို write) မထည့်သင့်ပါ —
  UI preview အတွက်သာ၊ save မလုပ်ဘူးလို့လည်း ဖြစ်နိုင်တယ်။
- Manifest ရဲ့ `data` list ထဲက file order က အရေးကြီးပါတယ် — security ကို view/access
  csv ထက် အရင် load ရပါမယ်။
- Wizard ကနေ parent record ကို write လုပ်ပြီးရင် `return {'type': 'ir.actions.act_window_close'}`
  ကို မမေ့ပါနဲ့ (မဟုတ်ရင် popup မပိတ်ပါ)။
