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
    
    # Participant management fields
    participant_employee_ids = fields.Many2many(
        'nhan_vien',
        'meeting_booking_participant_rel',
        'booking_id',
        'employee_id',
        string='Danh sách người tham gia',
        help='Danh sách nhân viên tham gia cuộc họp (không bao gồm người tổ chức)'
    )
    total_attendees = fields.Integer(
        string='Tổng số người tham gia',
        compute='_compute_total_attendees',
        store=True,
        help='Tổng số người = Người tổ chức (1) + Số người tham gia'
    )
    
    # Approval workflow fields
    state = fields.Selection([
        ('draft', 'Chờ duyệt'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', required=True, tracking=True)
    approved_by = fields.Many2one('nhan_vien', string='Người phê duyệt', readonly=True)
    approved_date = fields.Datetime(string='Ngày phê duyệt', readonly=True)
    cancelled_by = fields.Many2one('nhan_vien', string='Người hủy', readonly=True)
    cancelled_date = fields.Datetime(string='Ngày hủy', readonly=True)
    
    # Computed field to check if booking is currently active
    is_current = fields.Boolean(string='Đang diễn ra', compute='_compute_is_current', store=False)
    is_in_progress = fields.Boolean(string='Đang diễn ra (Real-time)', compute='_compute_is_in_progress', store=False)

    @api.depends('organizer_id', 'participant_employee_ids')
    def _compute_total_attendees(self):
        """Tính tổng số người tham gia = 1 (organizer) + số participants"""
        for booking in self:
            booking.total_attendees = 1 + len(booking.participant_employee_ids)
    
    @api.depends('start_time', 'end_time', 'state')
    def _compute_is_current(self):
        """Kiểm tra xem lịch họp có đang diễn ra không (legacy field)"""
        now = fields.Datetime.now()
        for booking in self:
            booking.is_current = (
                booking.state == 'approved' and
                booking.start_time <= now <= booking.end_time
            )
    
    @api.depends('start_time', 'end_time', 'state')
    def _compute_is_in_progress(self):
        """Kiểm tra xem cuộc họp có đang diễn ra không (real-time)"""
        now = fields.Datetime.now()
        for booking in self:
            booking.is_in_progress = (
                booking.state == 'approved' and
                booking.start_time <= now <= booking.end_time
            )

    @api.constrains('start_time', 'end_time', 'meeting_room_id', 'state')
    def _check_overlap(self):
        """Kiểm tra trùng lịch và validate thời gian"""
        for booking in self:
            # Validate 1: start_time < end_time
            if booking.start_time >= booking.end_time:
                raise ValidationError("Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc!")
            
            # Validate 2: Không cho booking quá khứ (trừ admin)
            if not self.env.user.has_group('base.group_system'):
                if booking.start_time < fields.Datetime.now():
                    raise ValidationError("Không thể đặt phòng vào thời gian trong quá khứ!")

            # Validate 3: Chỉ check trùng lịch với các booking đã duyệt
            domain = [
                ('meeting_room_id', '=', booking.meeting_room_id.id),
                ('id', '!=', booking.id),
                ('state', '=', 'approved'),  # Chỉ check booking đã duyệt
                ('start_time', '<', booking.end_time),
                ('end_time', '>', booking.start_time),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(f"Phòng {booking.meeting_room_id.name} đã được đặt trong khoảng thời gian này!")
    
    @api.constrains('total_attendees', 'meeting_room_id')
    def _check_room_capacity(self):
        """Kiểm tra số người tham gia không vượt sức chứa phòng"""
        for booking in self:
            if booking.total_attendees > booking.meeting_room_id.capacity:
                raise ValidationError(
                    f"Số người tham gia ({booking.total_attendees}) "
                    f"vượt sức chứa phòng ({booking.meeting_room_id.capacity})."
                )
    
    @api.constrains('organizer_id', 'participant_employee_ids')
    def _check_participants(self):
        """Validate danh sách người tham gia"""
        for booking in self:
            # Rule: Organizer không được trong danh sách participants
            if booking.organizer_id in booking.participant_employee_ids:
                raise ValidationError(
                    "Người tổ chức không được xuất hiện trong danh sách người tham gia!"
                )

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
    
    def action_cancel(self):
        """Hủy đăng ký phòng họp"""
        for booking in self:
            if booking.state == 'cancelled':
                raise ValidationError("Đăng ký đã được hủy trước đó!")
            
            # Lấy employee_id nếu có
            cancelled_by_id = False
            if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
                cancelled_by_id = self.env.user.employee_id.id
            
            booking.write({
                'state': 'cancelled',
                'cancelled_by': cancelled_by_id,
                'cancelled_date': fields.Datetime.now()
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
