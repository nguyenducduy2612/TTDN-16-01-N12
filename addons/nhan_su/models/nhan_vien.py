from odoo import models, fields, api  


class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Bảng chứa thông tin nhân viên'
    _rec_name = 'ho_ten'

    ma_dinh_danh = fields.Char("Mã định danh", required=True)
    ho_ten = fields.Char("Họ tên", required=True, default='')
    ngay_sinh = fields.Date("Ngày sinh")
    que_quan = fields.Char("Quê quán")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số điện thoại")
    lich_su_cong_tac_ids = fields.One2many("lich_su_cong_tac",string="Danh sách lịch sử công tác", inverse_name="nhan_vien_id")
    tuoi = fields.Integer("Tuổi", compute="_compute_tuoi", store=True)
    
    # Link với user Odoo
    user_id = fields.Many2one('res.users', string='Tài khoản người dùng',
                              help='Link nhân viên với tài khoản Odoo để phân quyền')

    # ids_van_ban_di = fields.One2many(comodel_name='van_ban_di', inverse_name='id_nguoi_phat_hanh', string="Số văn bản đi")

    @api.depends('ngay_sinh')
    def _compute_tuoi(self):
        for record in self:
            if record.ngay_sinh:
                record.tuoi = (fields.Date.today() - record.ngay_sinh).days // 365


class ResUsers(models.Model):
    _inherit = 'res.users'
    
    # Tạo inverse relationship để user.employee_id hoạt động
    employee_id = fields.Many2one('nhan_vien', string='Nhân viên',
                                   compute='_compute_employee_id', store=False)
    
    def _compute_employee_id(self):
        """Tìm nhân viên được link với user này"""
        for user in self:
            employee = self.env['nhan_vien'].search([('user_id', '=', user.id)], limit=1)
            user.employee_id = employee.id if employee else False
