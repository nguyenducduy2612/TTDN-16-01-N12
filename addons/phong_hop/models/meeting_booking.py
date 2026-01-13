from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MeetingBooking(models.Model):
    _name = 'meeting.booking'
    _description = 'Đăng ký phòng họp'
    _rec_name = 'description'
    _order = 'start_time desc'

    meeting_room_id = fields.Many2one('meeting.room', string='Phòng họp', required=True)
    start_time = fields.Datetime(string='Thời gian bắt đầu', required=True)
    end_time = fields.Datetime(string='Thời gian kết thúc', required=True)
    organizer_id = fields.Many2one('nhan_vien', string='Người tổ chức', required=True)
    description = fields.Char(string='Mục đích/Ghi chú', required=True)

    @api.constrains('start_time', 'end_time', 'meeting_room_id')
    def _check_overlap(self):
        for booking in self:
            if booking.start_time >= booking.end_time:
                raise ValidationError("Thời gian bắt đầu phải nhỏ hơn thời gian kết thúc!")

            domain = [
                ('meeting_room_id', '=', booking.meeting_room_id.id),
                ('id', '!=', booking.id),
                ('start_time', '<', booking.end_time),
                ('end_time', '>', booking.start_time),
            ]
            if self.search_count(domain) > 0:
                raise ValidationError(f"Phòng {booking.meeting_room_id.name} đã được đặt trong khoảng thời gian này!")
