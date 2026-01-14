# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta

class MeetingStatistics(models.TransientModel):
    _name = 'meeting.statistics'
    _description = 'Thống kê sử dụng phòng họp'

    date_from = fields.Date(string='Từ ngày', required=True, default=lambda self: fields.Date.today() - timedelta(days=30))
    date_to = fields.Date(string='Đến ngày', required=True, default=fields.Date.today)
    room_ids = fields.Many2many('meeting.room', string='Phòng họp (để trống = tất cả)')
    
    def action_view_most_used_rooms(self):
        """Xem báo cáo phòng họp được sử dụng nhiều nhất"""
        self.ensure_one()
        
        # Build domain for date range
        domain = [
            ('state', '=', 'approved'),
            ('start_time', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('start_time', '<=', fields.Datetime.to_datetime(self.date_to))
        ]
        
        if self.room_ids:
            domain.append(('meeting_room_id', 'in', self.room_ids.ids))
        
        # Return tree view grouped by room
        return {
            'name': 'Phòng họp được sử dụng nhiều nhất',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.booking',
            'view_mode': 'graph,pivot,tree',
            'domain': domain,
            'context': {
                'search_default_group_room': 1,
                'graph_measure': '__count__',
                'graph_mode': 'bar',
                'graph_groupbys': ['meeting_room_id'],
            }
        }
    
    def action_view_peak_hours(self):
        """Xem báo cáo khung giờ cao điểm"""
        self.ensure_one()
        
        domain = [
            ('state', '=', 'approved'),
            ('start_time', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('start_time', '<=', fields.Datetime.to_datetime(self.date_to))
        ]
        
        if self.room_ids:
            domain.append(('meeting_room_id', 'in', self.room_ids.ids))
        
        return {
            'name': 'Khung giờ cao điểm',
            'type': 'ir.actions.act_window',
            'res_model': 'meeting.booking',
            'view_mode': 'graph,pivot,tree',
            'domain': domain,
            'context': {
                'graph_measure': '__count__',
                'graph_mode': 'bar',
                'graph_groupbys': ['start_time:hour'],
            }
        }
