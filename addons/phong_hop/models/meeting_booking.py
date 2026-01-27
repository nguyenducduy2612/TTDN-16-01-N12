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
    
    # Computed fields for UI permission visibility
    user_can_approve_ui = fields.Boolean(string='User có quyền phê duyệt (UI)', 
                                          compute='_compute_user_permissions_ui', store=False)
    user_can_manage_booking_ui = fields.Boolean(string='User có quyền quản lý lịch (UI)', 
                                                 compute='_compute_user_permissions_ui', store=False)
    is_booking_creator = fields.Boolean(string='Là người tạo lịch', 
                                        compute='_compute_user_permissions_ui', store=False)
    
    # Asset borrowing integration
    don_muon_tai_san_id = fields.Many2one(
        'don_muon_tai_san',
        string='Đơn mượn tài sản',
        readonly=True,
        help='Đơn mượn tài sản tự động tạo khi booking được duyệt'
    )
    tai_san_muon_ids = fields.Many2many(
        'phan_bo_tai_san',
        string='Tài sản cần mượn',
        help='Chọn tài sản cần mượn từ phòng ban quản lý phòng họp'
    )
    
    # Duration field for statistics
    duration_hours = fields.Float(
        string='Thời lượng (giờ)',
        compute='_compute_duration_hours',
        store=True,
        help='Thời lượng cuộc họp tính bằng giờ'
    )
    
    @api.depends('start_time', 'end_time')
    def _compute_duration_hours(self):
        """Tính thời lượng cuộc họp bằng giờ"""
        for booking in self:
            if booking.start_time and booking.end_time:
                duration = booking.end_time - booking.start_time
                booking.duration_hours = duration.total_seconds() / 3600
            else:
                booking.duration_hours = 0.0
    
    @api.onchange('meeting_room_id')
    def _onchange_meeting_room_id(self):
        """Filter tài sản theo phòng ban quản lý của phòng họp"""
        if self.meeting_room_id and self.meeting_room_id.phong_ban_quan_ly_id:
            return {
                'domain': {
                    'tai_san_muon_ids': [('phong_ban_id', '=', self.meeting_room_id.phong_ban_quan_ly_id.id)]
                }
            }
        else:
            return {
                'domain': {
                    'tai_san_muon_ids': [('id', '=', False)]  # Không hiển thị tài sản nào
                }
            }

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
    
    def _compute_user_permissions_ui(self):
        """Tính toán quyền của user hiện tại để hiển thị/ẩn nút trên UI"""
        for booking in self:
            # Check quyền phê duyệt
            booking.user_can_approve_ui = booking._user_can_approve()
            
            # Check quyền quản lý lịch họp
            booking.user_can_manage_booking_ui = booking._user_can_manage_bookings()
            
            # Check xem user hiện tại có phải người tạo lịch không
            current_employee = False
            if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
                current_employee = self.env.user.employee_id
            
            booking.is_booking_creator = (
                current_employee and booking.nguoi_muon and 
                current_employee.id == booking.nguoi_muon.id
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
            
            # Validate 3: Không cho đặt phòng đang bảo trì
            if booking.meeting_room_id.manual_status == 'maintenance':
                raise ValidationError(f"Phòng {booking.meeting_room_id.name} đang trong trạng thái bảo trì, không thể đặt phòng!")

            # Validate 4: Chỉ check trùng lịch với các booking đã duyệt
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
            
            # ⭐ CẬP NHẬT TRẠNG THÁI ĐƠN MƯỢN TÀI SẢN
            if booking.don_muon_tai_san_id:
                booking.don_muon_tai_san_id.write({
                    'trang_thai': 'da-duyet'
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
            
            # ⭐ HỦY ĐƠN MƯỢN TÀI SẢN NẾU CÓ
            if booking.don_muon_tai_san_id:
                booking.don_muon_tai_san_id.write({
                    'trang_thai': 'da-huy'
                })
        return True

    def action_reset_to_draft(self):
        """Đưa đăng ký về trạng thái chờ duyệt"""
        for booking in self:
            # Không cho phép đặt lại chờ duyệt nếu đơn đã bị hủy
            if booking.state == 'cancelled':
                raise ValidationError("Không thể đặt lại chờ duyệt cho đơn đã bị hủy!")
            
            booking.write({
                'state': 'draft',
                'approved_by': False,
                'approved_date': False
            })
            
            # ⭐ ĐẶT LẠI TRẠNG THÁI ĐƠN MƯỢN TÀI SẢN
            if booking.don_muon_tai_san_id:
                booking.don_muon_tai_san_id.write({
                    'trang_thai': 'dang-cho'
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
            
            # ⭐ HỦY ĐƠN MƯỢN TÀI SẢN NẾU CÓ
            if booking.don_muon_tai_san_id:
                booking.don_muon_tai_san_id.write({
                    'trang_thai': 'da-huy'
                })
        
        return True
    
    # ========== ASSET BORROWING INTEGRATION ==========
    
    def _create_asset_borrowing(self, initial_state='dang-cho'):
        """
        Tạo đơn mượn tài sản cho thiết bị user đã chọn
        
        Args:
            initial_state: Trạng thái ban đầu của đơn mượn ('dang-cho' hoặc 'da-duyet')
        """
        # Chỉ tạo nếu:
        # 1. User đã chọn tài sản
        # 2. Phòng có phòng ban quản lý
        # 3. Chưa có đơn mượn (tránh duplicate)
        if not self.tai_san_muon_ids:
            return  # Không chọn tài sản → không cần tạo đơn mượn
        
        if not self.meeting_room_id.phong_ban_quan_ly_id:
            raise ValidationError(
                f"Phòng họp '{self.meeting_room_id.name}' chưa có phòng ban quản lý! "
                "Vui lòng cấu hình phòng ban quản lý trước."
            )
        
        if self.don_muon_tai_san_id:
            return  # Đã có đơn mượn rồi
        
        phong_ban_cho_muon = self.meeting_room_id.phong_ban_quan_ly_id
        
        # Xác định nhân viên mượn
        nhan_vien_muon_id = False
        if self.nguoi_muon:
            nhan_vien_muon_id = self.nguoi_muon.id
        elif self.organizer_id:
            nhan_vien_muon_id = self.organizer_id.id
        
        if not nhan_vien_muon_id:
            raise ValidationError(
                "Không xác định được nhân viên mượn tài sản! "
                "Vui lòng kiểm tra lại thông tin người mượn phòng hoặc người tổ chức."
            )
        
        # Tạo mã đơn mượn
        ma_don_muon = f"MTS-PHONG-{self.id}-{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Tạo đơn mượn với trạng thái được chỉ định
        don_muon = self.env['don_muon_tai_san'].create({
            'ma_don_muon': ma_don_muon,
            'ten_don_muon': f'Mượn tài sản phòng {self.meeting_room_id.name}',
            'phong_ban_cho_muon_id': phong_ban_cho_muon.id,
            'thoi_gian_muon': self.start_time,
            'thoi_gian_tra': self.end_time,
            'nhan_vien_muon_id': nhan_vien_muon_id,
            'ly_do': f'Cuộc họp: {self.description}',
            'trang_thai': initial_state,  # Trạng thái linh hoạt
        })
        
        # Thêm các tài sản user đã chọn vào đơn mượn
        for phan_bo in self.tai_san_muon_ids:
            self.env['don_muon_tai_san_line'].create({
                'don_muon_id': don_muon.id,
                'phan_bo_tai_san_id': phan_bo.id,
            })
        
        # Lưu link đến đơn mượn
        self.don_muon_tai_san_id = don_muon.id
    
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
        has_auto_approve = booking._user_has_auto_approve()
        
        if has_auto_approve:
            # Lấy employee_id nếu có
            approved_by_id = False
            if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
                approved_by_id = self.env.user.employee_id.id
            
            booking.write({
                'state': 'approved',
                'approved_by': approved_by_id,
                'approved_date': fields.Datetime.now()
            })
            
            # ⭐ TẠO ĐƠN MƯỢN TÀI SẢN VỚI TRẠNG THÁI "ĐÃ DUYỆT"
            booking._create_asset_borrowing(initial_state='da-duyet')
        else:
            # ⭐ TẠO ĐƠN MƯỢN TÀI SẢN VỚI TRẠNG THÁI "ĐANG CHỜ"
            booking._create_asset_borrowing(initial_state='dang-cho')
        
        return booking
    
    def _user_can_manage_bookings(self):
        """
        Kiểm tra user có quyền quản lý (sửa/xóa) lịch họp không
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
                ('can_manage_bookings', '=', True)
            ], limit=1):
                return True
        
        # Check theo phòng ban
        if employee and hasattr(employee, 'phong_ban_id') and employee.phong_ban_id:
            if Permission.search([
                ('permission_type', '=', 'phong_ban'),
                ('phong_ban_id', '=', employee.phong_ban_id.id),
                ('can_manage_bookings', '=', True)
            ], limit=1):
                return True
        
        # Check theo chức vụ
        if employee and hasattr(employee, 'chuc_vu_id') and employee.chuc_vu_id:
            if Permission.search([
                ('permission_type', '=', 'chuc_vu'),
                ('chuc_vu_id', '=', employee.chuc_vu_id.id),
                ('can_manage_bookings', '=', True)
            ], limit=1):
                return True
        
        return False
    
    def write(self, vals):
        """Override write để kiểm tra quyền quản lý lịch họp"""
        for booking in self:
            # Admin luôn có quyền (kể cả sửa đơn đã hủy)
            if self.env.user.has_group('base.group_system'):
                continue
            
            # Không cho phép chỉnh sửa đơn đã bị hủy (trừ admin)
            if booking.state == 'cancelled':
                raise ValidationError("Không thể chỉnh sửa đơn mượn phòng đã bị hủy!")
            
            # Lấy employee của user hiện tại
            current_employee = False
            if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
                current_employee = self.env.user.employee_id
            
            # Người tạo lịch họp được phép sửa lịch của chính họ
            is_creator = current_employee and booking.nguoi_muon and current_employee.id == booking.nguoi_muon.id
            
            # Nếu không phải người tạo và không có quyền quản lý
            if not is_creator and not booking._user_can_manage_bookings():
                raise ValidationError("Bạn không có quyền quản lý lịch họp!")
        
        return super(MeetingBooking, self).write(vals)
    
    def unlink(self):
        """Override unlink để kiểm tra quyền xóa lịch họp"""
        for booking in self:
            # Admin luôn có quyền
            if self.env.user.has_group('base.group_system'):
                continue
            
            # Lấy employee của user hiện tại
            current_employee = False
            if hasattr(self.env.user, 'employee_id') and self.env.user.employee_id:
                current_employee = self.env.user.employee_id
            
            # Người tạo lịch họp được phép xóa lịch của chính họ
            is_creator = current_employee and booking.nguoi_muon and current_employee.id == booking.nguoi_muon.id
            
            # Nếu không phải người tạo và không có quyền quản lý
            if not is_creator and not booking._user_can_manage_bookings():
                raise ValidationError("Bạn không có quyền quản lý lịch họp!")
        
        return super(MeetingBooking, self).unlink()
