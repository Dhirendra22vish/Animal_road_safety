import streamlit as st
from datetime import datetime
import json

class MobileAlertSystem:
    def __init__(self):
        self.alerts = []
        self.emergency_contacts = [
            {"name": "Forest Department", "number": "+91-9305573854", "type": "official"},
            {"name": "Wildlife Rescue", "number": "+91-9876543211", "type": "rescue"},
            {"name": "Highway Patrol", "number": "+91-9876543212", "type": "patrol"},
            {"name": "Local Police", "number": "+91-9876543213", "type": "police"},
            {"name": "Ambulance", "number": "108", "type": "medical"}
        ]
    
    def send_alert(self, alert_data, alert_type="warning"):
        """Send mobile alert with different templates"""
        
        alert_templates = {
            "warning": {
                "title": "🚨 WILDLIFE WARNING",
                "template": "Animal crossing zone ahead: {zone_name}. Reduce speed to {recommended_speed} km/h. Distance: {distance}km.",
                "priority": "medium"
            },
            "critical": {
                "title": "🚨 CRITICAL ALERT", 
                "template": "IMMEDIATE DANGER: {species} detected at {distance}km! STOP VEHICLE. Location: {zone_name}.",
                "priority": "high"
            },
            "animal_detected": {
                "title": "🦌 ANIMAL DETECTED",
                "template": "LIVE ANIMAL: {species} spotted at {distance_from_vehicle}km. Confidence: {confidence}%. Take immediate precautions.",
                "priority": "high"
            },
            "emergency": {
                "title": "🚑 EMERGENCY ALERT",
                "template": "WILDLIFE COLLISION RISK: {species} in immediate path! EMERGENCY BRAKING REQUIRED.",
                "priority": "critical"
            }
        }
        
        template = alert_templates.get(alert_type, alert_templates["warning"])
        
        # Format message with alert data
        message = template["template"].format(
            zone_name=alert_data.get('zone_name', 'Unknown'),
            species=alert_data.get('species', 'unknown').title(),
            distance=alert_data.get('distance', 'unknown'),
            recommended_speed=alert_data.get('recommended_speed', 'unknown'),
            distance_from_vehicle=alert_data.get('distance_from_vehicle', 'unknown'),
            confidence=alert_data.get('confidence', 0) * 100
        )
        
        alert = {
            "id": len(self.alerts) + 1,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "title": template["title"],
            "message": message,
            "type": alert_type,
            "priority": template["priority"],
            "species": alert_data.get('species', 'unknown'),
            "location": alert_data.get('zone_name', 'Unknown location'),
            "read": False,
            "sent_to_mobile": True
        }
        
        self.alerts.append(alert)
        
        # Keep only last 50 alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
        
        return alert
    
    def send_emergency_sms(self, alert_data):
        """Send emergency SMS to all contacts"""
        emergency_message = f"""
🚨 URGENT: Wildlife Emergency 🚨
Animal: {alert_data.get('species', 'unknown').title()}
Location: {alert_data.get('zone_name', 'Unknown')}
Distance: {alert_data.get('distance', alert_data.get('distance_from_vehicle', 'Unknown'))}km
Time: {datetime.now().strftime('%H:%M:%S')}
Priority: CRITICAL - Immediate action required!

Sent via UP Animal Safety System
        """
        
        sent_alerts = []
        
        # Simulate sending to each emergency contact
        for contact in self.emergency_contacts:
            sms_alert = {
                "id": len(self.alerts) + 1,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "title": f"📞 SMS Sent to {contact['name']}",
                "message": f"Emergency SMS: {emergency_message}",
                "type": "emergency_sms",
                "priority": "critical",
                "contact": contact,
                "read": False
            }
            
            self.alerts.append(sms_alert)
            sent_alerts.append(sms_alert)
        
        return sent_alerts
    
    def simulate_push_notification(self, alert_data):
        """Simulate mobile push notification"""
        notification = {
            "id": f"push_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "title": "🐘 UP Animal Safety Alert",
            "body": f"{alert_data.get('species', 'Wildlife').title()} detected nearby - Stay alert!",
            "data": alert_data,
            "type": "push_notification"
        }
        
        self.alerts.append(notification)
        return notification
    
    def get_unread_alerts_count(self):
        """Get count of unread alerts"""
        return len([alert for alert in self.alerts if not alert.get('read', False)])
    
    def mark_all_read(self):
        """Mark all alerts as read"""
        for alert in self.alerts:
            alert['read'] = True
    
    def get_alerts_by_priority(self, priority):
        """Get alerts filtered by priority"""
        return [alert for alert in self.alerts if alert.get('priority') == priority]
    
    def get_recent_alerts(self, count=10):
        """Get most recent alerts"""
        return self.alerts[-count:] if self.alerts else []
    
    def clear_alerts(self):
        """Clear all alerts"""
        self.alerts = []

# Global instance
mobile_alerts = MobileAlertSystem()

def send_mobile_alert(alert_data, alert_type="warning"):
    """Global function to send mobile alerts"""
    return mobile_alerts.send_alert(alert_data, alert_type)

def send_emergency_sms(alert_data):
    """Global function to send emergency SMS"""
    return mobile_alerts.send_emergency_sms(alert_data)

def get_mobile_alerts():
    """Get all mobile alerts"""
    return mobile_alerts.alerts

def get_unread_count():
    """Get unread alerts count"""
    return mobile_alerts.get_unread_alerts_count()