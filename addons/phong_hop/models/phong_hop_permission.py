# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class PhongHopPermission(models.Model):
    _name = 'phong_hop.permission'
    _description = 'Phân quyền phòng họp'
    _rec_name = 'ten_quyen'

    ten_quyen = fields.Char('Tên nhóm quyền',
                            help='Đặt tên cho nhóm quyền này, VD: "Nhân viên phòng Hành chính"')
    
    # Phân quyền theo
    permission_type = fields.Selection([
        ('user', 'Theo người dùng'),
        ('phong_ban', 'Theo phòng ban'),
        ('chuc_vu', 'Theo chức vụ')
    ], string='Loại phân quyền', required=True, default='user')
    
    # Link đến đối tượng
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân viên')
    phong_ban_id = fields.Many2one('phong_ban', string='Phòng ban')
    chuc_vu_id = fields.Many2one('chuc_vu', string='Chức vụ')
    
    # Quyền hạn
    can_create_booking = fields.Boolean('Được mượn phòng', default=True,
                                        help='Cho phép tạo yêu cầu mượn phòng họp')
    can_approve = fields.Boolean('Được phê duyệt',
                                  help='Cho phép phê duyệt/từ chối yêu cầu mượn phòng')
    auto_approve = fields.Boolean('Tự động phê duyệt khi mượn',
                                   help='Yêu cầu mượn phòng sẽ tự động được duyệt')
    
    @api.constrains('permission_type', 'nhan_vien_id', 'phong_ban_id', 'chuc_vu_id')
    def _check_permission_target(self):
        """Kiểm tra phải chọn đúng đối tượng theo loại phân quyền"""
        for record in self:
            if record.permission_type == 'user' and not record.nhan_vien_id:
                raise ValidationError("Vui lòng chọn nhân viên!")
            elif record.permission_type == 'phong_ban' and not record.phong_ban_id:
                raise ValidationError("Vui lòng chọn phòng ban!")
            elif record.permission_type == 'chuc_vu' and not record.chuc_vu_id:
                raise ValidationError("Vui lòng chọn chức vụ!")
    
    @api.onchange('permission_type')
    def _onchange_permission_type(self):
        """Reset các field không liên quan khi đổi loại phân quyền"""
        if self.permission_type == 'user':
            self.phong_ban_id = False
            self.chuc_vu_id = False
        elif self.permission_type == 'phong_ban':
            self.nhan_vien_id = False
            self.chuc_vu_id = False
        elif self.permission_type == 'chuc_vu':
            self.nhan_vien_id = False
            self.phong_ban_id = False
