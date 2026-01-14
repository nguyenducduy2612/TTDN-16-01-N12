from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime

class MeetingBooking(models.Model):
    _name = 'meeting.booking'
    _description = 'Đăng ký phòng họp'
    _rec_name = 'description'
    _order = 'start_time desc'

    meeting_room_id = fields.Many2one('meeting.room', string='Phòng họp', required=True)
    start_time = fields.Datetime(string='Thời gian bắt đầu', required=True)
    end_time = fields.Datetime(string='Thời gian kết thúc', required=True)
    organizer_id = fields.Many2one('nhan_vien', string='Người tổ chức', required=True)
    nguoi_muon = fields.Many2one('nhan_vien', string='Người mượn phòng', readonly=True,
                                  help='Người tạo yêu cầu mượn phòng (tự động)')
    description = fields.Char(string='Mục đích/Ghi chú', required=True)
    
    # Approval workflow fields
    state = fields.Selection([
        ('draft', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối')
    ], string='Trạng thái', default='draft', required=True, tracking=True)
    approved_by = fields.Many2one('nhan_vien', string='Người phê duyệt', readonly=True)
    approved_date = fields.Datetime(string='Ngày phê duyệt', readonly=True)
    
    # Computed field to check if booking is currently active
    is_current = fields.Boolean(string='Đang diễn ra', compute='_compute_is_current', store=False)

    @api.depends('start_time', 'end_time', 'state')
    def _compute_is_current(self):
        """Kiểm tra xem lịch họp có đang diễn ra không"""
        now = fields.Datetime.now()
        for booking in self:
            booking.is_current = (
                booking.state == 'approved' and
                booking.start_time <= now <= booking.end_time
            )

    @api.constrains('start_time', 'end_time', 'meeting_room_id', 'state')
    def _check_overlap(self):
        """Kiểm tra trùng lịch - chỉ check với các booking đã được duyệt"""
        for booking in self:
            if booking.start_time >= booking.end_time:
                raise ValidationError("Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc!")

            # Chỉ check trùng lịch với các booking đã duyệt
            domain = [
                ('meeting_room_id', '=', booking.meeting_room_id.id),
                ('id', '!=', booking.id),
                ('state', '=', 'approved'),  # Chỉ check booking đã duyệt
                ('start_time', '<', booking.end_time),
                ('end_time', '>', booking.start_time),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(f"Phòng {booking.meeting_room_id.name} đã được đặt trong khoảng thời gian này!")

    def action_approve(self):
        """Phê duyệt đăng ký phòng họp - với kiểm tra quyền"""
        # Check quyền phê duyệt
        if not self._user_can_approve():
            raise ValidationError("Bạn không có quyền phê duyệt yêu cầu mượn phòng!")
        
        for booking in self:
            if booking.state != 'draft':
                raise ValidationError("Chỉ có thể phê duyệt đăng ký ở trạng thái 'Chờ duyệt'!")
            
            # Lấy employee_id nếu có
            approved_by_id = False
            if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
                approved_by_id = self.env.user.employee_id.id
            
            booking.write({
                'state': 'approved',
                'approved_by': approved_by_id,
                'approved_date': fields.Datetime.now()
            })
        return True

    def action_reject(self):
        """Từ chối đăng ký phòng họp - với kiểm tra quyền"""
        # Check quyền phê duyệt
        if not self._user_can_approve():
            raise ValidationError("Bạn không có quyền từ chối yêu cầu mượn phòng!")
        
        for booking in self:
            if booking.state != 'draft':
                raise ValidationError("Chỉ có thể từ chối đăng ký ở trạng thái 'Chờ duyệt'!")
            
            # Lấy employee_id nếu có
            approved_by_id = False
            if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
                approved_by_id = self.env.user.employee_id.id
            
            booking.write({
                'state': 'rejected',
                'approved_by': approved_by_id,
                'approved_date': fields.Datetime.now()
            })
        return True

    def action_reset_to_draft(self):
        """Đưa đăng ký về trạng thái chờ duyệt"""
        for booking in self:
            booking.write({
                'state': 'draft',
                'approved_by': False,
                'approved_date': False
            })
        return True
    
    # ========== PERMISSION METHODS ==========
    
    def _user_can_approve(self):
        """
        Kiểm tra user có quyền phê duyệt không
        Returns: Boolean
        """
        # Admin luôn có quyền
        if self.env.user.has_group('base.group_system'):
            return True
        
        Permission = self.env['phong_hop.permission']
        user = self.env.user
        
        # Lấy employee của user
        employee = False
        if hasattr(user, 'employee_id') and user.employee_id:
            employee = user.employee_id
        
        # Check theo nhân viên
        if employee:
            if Permission.search([
                ('permission_type', '=', 'user'),
                ('nhan_vien_id', '=', employee.id),
                ('can_approve', '=', True)
            ], limit=1):
                return True
        
        # Check theo phòng ban
        if employee and hasattr(employee, 'phong_ban_id') and employee.phong_ban_id:
            if Permission.search([
                ('permission_type', '=', 'phong_ban'),
                ('phong_ban_id', '=', employee.phong_ban_id.id),
                ('can_approve', '=', True)
            ], limit=1):
                return True
        
        # Check theo chức vụ
        if employee and hasattr(employee, 'chuc_vu_id') and employee.chuc_vu_id:
            if Permission.search([
                ('permission_type', '=', 'chuc_vu'),
                ('chuc_vu_id', '=', employee.chuc_vu_id.id),
                ('can_approve', '=', True)
            ], limit=1):
                return True
        
        return False
    
    def _user_has_auto_approve(self):
        """
        Kiểm tra user có quyền tự động phê duyệt không
        Returns: Boolean
        """
        # Admin luôn có quyền
        if self.env.user.has_group('base.group_system'):
            return True
        
        Permission = self.env['phong_hop.permission']
        user = self.env.user
        
        # Lấy employee của user
        employee = False
        if hasattr(user, 'employee_id') and user.employee_id:
            employee = user.employee_id
        
        # Check theo nhân viên (qua user_id)
        if employee:
            if Permission.search([
                ('permission_type', '=', 'user'),
                ('nhan_vien_id', '=', employee.id),
                ('auto_approve', '=', True)
            ], limit=1):
                return True
        
        # Check theo phòng ban
        if employee and hasattr(employee, 'phong_ban_id') and employee.phong_ban_id:
            if Permission.search([
                ('permission_type', '=', 'phong_ban'),
                ('phong_ban_id', '=', employee.phong_ban_id.id),
                ('auto_approve', '=', True)
            ], limit=1):
                return True
        
        # Check theo chức vụ
        if employee and hasattr(employee, 'chuc_vu_id') and employee.chuc_vu_id:
            if Permission.search([
                ('permission_type', '=', 'chuc_vu'),
                ('chuc_vu_id', '=', employee.chuc_vu_id.id),
                ('auto_approve', '=', True)
            ], limit=1):
                return True
        
        return False
    
    def _user_can_create_booking(self):
        """
        Kiểm tra user có quyền tạo booking không
        Returns: Boolean
        """
        # Admin luôn có quyền
        if self.env.user.has_group('base.group_system'):
            return True
        
        Permission = self.env['phong_hop.permission']
        user = self.env.user
        
        # Lấy employee của user
        employee = False
        if hasattr(user, 'employee_id') and user.employee_id:
            employee = user.employee_id
        
        # Check theo nhân viên
        if employee:
            if Permission.search([
                ('permission_type', '=', 'user'),
                ('nhan_vien_id', '=', employee.id),
                ('can_create_booking', '=', True)
            ], limit=1):
                return True
        
        # Check theo phòng ban
        if employee and hasattr(employee, 'phong_ban_id') and employee.phong_ban_id:
            if Permission.search([
                ('permission_type', '=', 'phong_ban'),
                ('phong_ban_id', '=', employee.phong_ban_id.id),
                ('can_create_booking', '=', True)
            ], limit=1):
                return True
        
        # Check theo chức vụ
        if employee and hasattr(employee, 'chuc_vu_id') and employee.chuc_vu_id:
            if Permission.search([
                ('permission_type', '=', 'chuc_vu'),
                ('chuc_vu_id', '=', employee.chuc_vu_id.id),
                ('can_create_booking', '=', True)
            ], limit=1):
                return True
        
        return False
    
    @api.model
    def create(self, vals):
        """Override create để check quyền và tự động phê duyệt nếu user có quyền"""
        # Check quyền tạo booking
        if not self._user_can_create_booking():
            raise ValidationError("Bạn không có quyền tạo yêu cầu mượn phòng!")
        
        # Tự động set người mượn phòng = employee của user hiện tại
        if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
            vals['nguoi_muon'] = self.env.user.employee_id.id
        
        booking = super(MeetingBooking, self).create(vals)
        
        # Check xem user có quyền tự động duyệt không
        if booking._user_has_auto_approve():
            # Lấy employee_id nếu có
            approved_by_id = False
            if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
                approved_by_id = self.env.user.employee_id.id
            
            booking.write({
                'state': 'approved',
                'approved_by': approved_by_id,
                'approved_date': fields.Datetime.now()
            })
        
        return booking
