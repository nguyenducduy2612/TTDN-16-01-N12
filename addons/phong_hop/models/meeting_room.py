# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MeetingRoom(models.Model):
    _name = 'meeting.room'
    _description = 'Quản lý phòng họp'
    _rec_name = 'name'

    name = fields.Char(string='Tên phòng', required=True)
    capacity = fields.Integer(string='Sức chứa', default=10)
    location = fields.Char(string='Vị trí')
    equipment_ids = fields.Many2many('tai_san', string='Thiết bị đi kèm')
    
    # Manual status field (để set "Bảo trì" thủ công)
    manual_status = fields.Selection([
        ('auto', 'Tự động'),
        ('maintenance', 'Bảo trì')
    ], string='Quản lý thủ công', default='auto')
    
    # Computed status field - Real-time!
    status = fields.Selection([
        ('free', 'Rảnh'),
        ('occupied', 'Đang sử dụng'),
        ('maintenance', 'Bảo trì')
    ], string='Trạng thái', compute='_compute_status', search='_search_status', store=False)
    
    # Computed fields cho thống kê
    booking_count = fields.Integer(string='Số lần đặt', compute='_compute_booking_stats', store=True)
    total_hours_used = fields.Float(string='Tổng giờ sử dụng', compute='_compute_booking_stats', store=True)
    booking_ids = fields.One2many('meeting.booking', 'meeting_room_id', string='Lịch đặt phòng')

    def _compute_status(self):
        """Tính toán trạng thái real-time dựa trên booking hiện tại"""
        now = fields.Datetime.now()
        for room in self:
            # Nếu đang bảo trì thủ công
            if room.manual_status == 'maintenance':
                room.status = 'maintenance'
            else:
                # Check xem có booking nào đang diễn ra không
                current_booking = self.env['meeting.booking'].search([
                    ('meeting_room_id', '=', room.id),
                    ('state', '=', 'approved'),
                    ('start_time', '<=', now),
                    ('end_time', '>', now)
                ], limit=1)
                
                room.status = 'occupied' if current_booking else 'free'
    
    def _search_status(self, operator, value):
        """
        Override search để filter theo status real-time
        Ví dụ: domain=[('status', '=', 'free')] sẽ tìm phòng rảnh ngay lúc này
        """
        now = fields.Datetime.now()
        
        # Tìm các phòng đang bảo trì
        maintenance_room_ids = self.search([('manual_status', '=', 'maintenance')]).ids
        
        # Tìm các booking đang diễn ra
        current_bookings = self.env['meeting.booking'].search([
            ('state', '=', 'approved'),
            ('start_time', '<=', now),
            ('end_time', '>', now)
        ])
        occupied_room_ids = current_bookings.mapped('meeting_room_id').ids
        
        # Tìm các phòng rảnh (không bảo trì và không có booking)
        all_room_ids = self.search([]).ids
        free_room_ids = list(set(all_room_ids) - set(occupied_room_ids) - set(maintenance_room_ids))
        
        # Xử lý các operator
        if operator == '=':
            if value == 'free':
                return [('id', 'in', free_room_ids)]
            elif value == 'occupied':
                return [('id', 'in', occupied_room_ids)]
            elif value == 'maintenance':
                return [('id', 'in', maintenance_room_ids)]
        elif operator == '!=':
            if value == 'free':
                return [('id', 'in', occupied_room_ids + maintenance_room_ids)]
            elif value == 'occupied':
                return [('id', 'in', free_room_ids + maintenance_room_ids)]
            elif value == 'maintenance':
                return [('id', 'in', free_room_ids + occupied_room_ids)]
        elif operator == 'in' and isinstance(value, list):
            result_ids = []
            if 'free' in value:
                result_ids.extend(free_room_ids)
            if 'occupied' in value:
                result_ids.extend(occupied_room_ids)
            if 'maintenance' in value:
                result_ids.extend(maintenance_room_ids)
            return [('id', 'in', result_ids)]
        
        # Default fallback
        return [('id', 'in', [])]
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """Override read_group để group by status được"""
        
        # Nếu group by status
        if groupby and 'status' in groupby:
            now = fields.Datetime.now()
            
            # Tính real-time
            maintenance_count = self.search_count([('manual_status', '=', 'maintenance')])
            
            current_bookings = self.env['meeting.booking'].search([
                ('state', '=', 'approved'),
                ('start_time', '<=', now),
                ('end_time', '>', now)
            ])
            occupied_count = len(current_bookings.mapped('meeting_room_id'))
            
            total_count = self.search_count(domain if domain else [])
            free_count = total_count - occupied_count - maintenance_count
            
            # Return kết quả group
            return [
                {
                    'status': 'free',
                    'status_count': free_count,
                    '__domain': domain + [('status', '=', 'free')] if domain else [('status', '=', 'free')],
                },
                {
                    'status': 'occupied', 
                    'status_count': occupied_count,
                    '__domain': domain + [('status', '=', 'occupied')] if domain else [('status', '=', 'occupied')],
                },
                {
                    'status': 'maintenance',
                    'status_count': maintenance_count,
                    '__domain': domain + [('status', '=', 'maintenance')] if domain else [('status', '=', 'maintenance')],
                }
            ]
        
        return super(MeetingRoom, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.depends('booking_ids', 'booking_ids.state', 'booking_ids.start_time', 'booking_ids.end_time')
    def _compute_booking_stats(self):
        """Tính toán thống kê sử dụng phòng"""
        for room in self:
            # Chỉ đếm các booking đã được duyệt
            approved_bookings = room.booking_ids.filtered(lambda b: b.state == 'approved')
            room.booking_count = len(approved_bookings)
            
            # Tính tổng số giờ
            total_hours = 0.0
            for booking in approved_bookings:
                if booking.start_time and booking.end_time:
                    duration = booking.end_time - booking.start_time
                    total_hours += duration.total_seconds() / 3600  # Convert to hours
            room.total_hours_used = total_hours

