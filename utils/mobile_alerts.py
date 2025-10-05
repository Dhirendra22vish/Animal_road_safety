import os
import logging
import requests
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SMSAlertSystem:
    """Unified SMS System - Supports Fast2SMS and MSG91"""
    
    def __init__(self):
        """Initialize SMS Alert System with multiple providers"""
        # Load API keys
        self.fast2sms_key = os.getenv('FAST2SMS_API_KEY', '').strip()
        self.msg91_key = os.getenv('MSG91_AUTH_KEY', '').strip()
        
        self.active_provider = None
        self.is_initialized = False
        
        # Debug: Log status
        logger.info("=" * 50)
        logger.info("SMS SYSTEM INITIALIZATION")
        logger.info("=" * 50)
        logger.info(f"Fast2SMS: {'✅ Found' if self.fast2sms_key else '❌ Missing'}")
        logger.info(f"MSG91: {'✅ Found' if self.msg91_key else '❌ Missing'}")
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available SMS providers"""
        
        # Try MSG91 first (easier for demo, no DLT)
        if self.msg91_key:
            logger.info("\n🔍 Testing MSG91...")
            if self._test_msg91():
                self.active_provider = "MSG91"
                self.is_initialized = True
                logger.info("✅ MSG91 is ACTIVE!")
                logger.info("=" * 50)
                return
        
        # Fallback to Fast2SMS
        if self.fast2sms_key:
            logger.info("\n🔍 Testing Fast2SMS...")
            if self._test_fast2sms():
                self.active_provider = "FAST2SMS"
                self.is_initialized = True
                logger.info("✅ Fast2SMS is ACTIVE!")
                logger.info("=" * 50)
                return
        
        # No provider available
        logger.warning("\n⚠️ No SMS provider configured!")
        logger.warning("Running in SIMULATION mode.")
        logger.warning("")
        logger.warning("To enable REAL SMS, add to .env file:")
        logger.warning("")
        logger.warning("Option 1 - MSG91 (Recommended for Demo):")
        logger.warning("  MSG91_AUTH_KEY=your_msg91_key")
        logger.warning("  Get it: https://msg91.com (Free ₹20 credit)")
        logger.warning("")
        logger.warning("Option 2 - Fast2SMS:")
        logger.warning("  FAST2SMS_API_KEY=your_fast2sms_key")
        logger.warning("  Get it: https://www.fast2sms.com")
        logger.info("=" * 50)
    
    def _test_msg91(self) -> bool:
        """Test MSG91 connection"""
        try:
            url = "https://control.msg91.com/api/v5/otp"
            headers = {
                'authkey': self.msg91_key,
                'content-type': "application/json"
            }
            payload = {"mobile": "1234567890"}
            
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            
            # If we get auth error, key is wrong. If we get other error, key is valid
            if 'authkey' in response.text.lower() and 'invalid' in response.text.lower():
                logger.error("   ❌ Invalid MSG91 Auth Key")
                return False
            
            logger.info("   ✅ MSG91 key validated")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ MSG91 test failed: {str(e)}")
            return False
    
    def _test_fast2sms(self) -> bool:
        """Test Fast2SMS connection"""
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            headers = {
                "authorization": self.fast2sms_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            payload = {
                "route": "q",
                "message": "test",
                "language": "english",
                "numbers": "9999999999"
            }
            
            response = requests.post(url, data=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for DND error
                if "DND" in str(result.get('message', '')):
                    logger.warning("   ⚠️ Fast2SMS: Number in DND list")
                    logger.warning("   💡 Use MSG91 instead (no DND issue)")
                    return False
                
                logger.info("   ✅ Fast2SMS key validated")
                return True
            else:
                logger.error(f"   ❌ Fast2SMS error: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"   ❌ Fast2SMS test failed: {str(e)}")
            return False
    
    def send_sms_alert(self, phone_number: str, alert_data: Dict, alert_type: str = "warning") -> bool:
        """Send SMS using active provider"""
        
        # Validate phone
        if not self.validate_phone_number(phone_number):
            logger.error(f"❌ Invalid phone: {phone_number}")
            return False
        
        formatted_phone = self.format_phone_number(phone_number)
        message = self._create_alert_message(alert_data, alert_type)
        
        # Send using active provider
        if self.is_initialized and self.active_provider:
            if self.active_provider == "MSG91":
                return self._send_via_msg91(formatted_phone, message)
            elif self.active_provider == "FAST2SMS":
                return self._send_via_fast2sms(formatted_phone, message)
        
        # Simulation mode
        logger.info(f"📱 SMS SIMULATION MODE")
        self._print_simulation_sms(formatted_phone, message)
        return True
    
    def _send_via_msg91(self, phone: str, message: str) -> bool:
        """Send SMS via MSG91"""
        try:
            logger.info(f"📱 Sending via MSG91 to {phone}...")
            
            url = "https://control.msg91.com/api/sendhttp.php"
            params = {
                'authkey': self.msg91_key,
                'mobiles': phone,
                'message': message,
                'sender': 'UPWLDF',  # Your sender ID
                'route': '4',  # Transactional
                'country': '91'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"✅ SMS SENT via MSG91!")
                self._print_sent_sms(phone, message, "MSG91")
                return True
            else:
                logger.error(f"❌ MSG91 error: {response.text}")
                self._print_simulation_sms(phone, message)
                return False
                
        except Exception as e:
            logger.error(f"❌ MSG91 failed: {str(e)}")
            self._print_simulation_sms(phone, message)
            return False
    
    def _send_via_fast2sms(self, phone: str, message: str) -> bool:
        """Send SMS via Fast2SMS"""
        try:
            logger.info(f"📱 Sending via Fast2SMS to {phone}...")
            
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "route": "q",
                "message": message,
                "language": "english",
                "flash": 0,
                "numbers": phone
            }
            headers = {
                "authorization": self.fast2sms_key,
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(url, data=payload, headers=headers)
            result = response.json()
            
            if result.get('return') == True:
                logger.info(f"✅ SMS SENT via Fast2SMS!")
                self._print_sent_sms(phone, message, "Fast2SMS")
                return True
            else:
                logger.error(f"❌ Fast2SMS error: {result.get('message')}")
                self._print_simulation_sms(phone, message)
                return False
                
        except Exception as e:
            logger.error(f"❌ Fast2SMS failed: {str(e)}")
            self._print_simulation_sms(phone, message)
            return False
    
    def _print_sent_sms(self, phone: str, message: str, provider: str):
        """Print sent SMS confirmation"""
        print("\n" + "=" * 50)
        print(f"✅ SMS SENT via {provider}")
        print("=" * 50)
        print(f"To: +91{phone}")
        print("-" * 50)
        print(message)
        print("=" * 50 + "\n")
    
    def _print_simulation_sms(self, phone: str, message: str):
        """Print simulated SMS"""
        print("\n" + "=" * 50)
        print("📱 SMS SIMULATION")
        print("=" * 50)
        print(f"To: +91{phone}")
        print("-" * 50)
        print(message)
        print("=" * 50)
        print("💡 To send real SMS:")
        print("   Add MSG91_AUTH_KEY or FAST2SMS_API_KEY to .env")
        print("=" * 50 + "\n")
    
    def _create_alert_message(self, alert_data: Dict, alert_type: str) -> str:
        """Create formatted SMS message"""
        species = alert_data.get('species', 'wildlife').title().replace('_', ' ')
        zone = alert_data.get('zone_name', 'Wildlife Zone')
        dist = alert_data.get('distance', alert_data.get('distance_from_vehicle', 0))
        conf = alert_data.get('confidence', 0.85)
        speed = alert_data.get('recommended_speed', 30)
        
        urgency_map = {
            "critical": ("🚨 CRITICAL", "STOP NOW"),
            "animal_detected": ("🦌 ALERT", "SLOW DOWN"),
            "emergency": ("🆘 EMERGENCY", "CALL HELP"),
            "warning": ("⚠️ WARNING", "BE CAREFUL")
        }
        
        urgency, action = urgency_map.get(alert_type, urgency_map["warning"])
        
        message = f"{urgency}\n{species} at {zone}\n{dist:.1f}km ahead | {conf*100:.0f}%\nSpeed: {speed}kmph\n{action}\n-UP Wildlife"
        
        return message.strip()
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate Indian phone number"""
        if not phone_number:
            return False
        
        cleaned = ''.join(c for c in phone_number if c.isdigit())
        
        if cleaned.startswith('91') and len(cleaned) == 12:
            cleaned = cleaned[2:]
        
        if len(cleaned) == 10 and cleaned[0] in '6789':
            return True
        
        return False
    
    def format_phone_number(self, phone_number: str) -> str:
        """Format to 10-digit Indian number"""
        cleaned = ''.join(c for c in phone_number if c.isdigit())
        
        if cleaned.startswith('91') and len(cleaned) == 12:
            return cleaned[2:]
        
        return cleaned
    
    def get_status(self) -> Dict:
        """Get SMS system status"""
        return {
            "initialized": self.is_initialized,
            "provider": self.active_provider or "NONE",
            "mode": "ACTIVE 🟢" if self.is_initialized else "SIMULATION 🟡",
            "msg91": "✅" if self.msg91_key else "❌",
            "fast2sms": "✅" if self.fast2sms_key else "❌",
            "ready_for_sms": self.is_initialized
        }

# Global SMS system instance
sms_system = SMSAlertSystem()

def send_mobile_alert(alert_data: Dict, alert_type: str = "warning") -> Dict:
    """Send mobile alert (in-app + SMS)"""
    import streamlit as st
    
    if 'mobile_alerts' not in st.session_state:
        st.session_state.mobile_alerts = []
        logger.info("✅ Initialized mobile_alerts")
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    alert_templates = {
        "animal_detected": (
            f"🚨 {alert_data.get('species', 'wildlife').title().replace('_', ' ')} DETECTED",
            f"Live animal at {alert_data.get('distance_from_vehicle', 0):.1f}km with {alert_data.get('confidence', 0)*100:.0f}% confidence"
        ),
        "critical": (
            "🚨 CRITICAL ALERT",
            f"High-risk zone: {alert_data.get('zone_name', 'Unknown')} at {alert_data.get('distance', 0):.1f}km - SLOW DOWN!"
        ),
        "emergency": (
            "🆘 EMERGENCY ALERT",
            f"Emergency: {alert_data.get('species', 'wildlife').title()} collision risk - STOP NOW!"
        ),
        "warning": (
            "⚠️ WILDLIFE WARNING",
            f"Approaching {alert_data.get('zone_name', 'Unknown')} at {alert_data.get('distance', 0):.1f}km - Reduce speed"
        )
    }
    
    title, message = alert_templates.get(alert_type, alert_templates["warning"])
    
    priority_map = {
        "critical": "high",
        "emergency": "critical", 
        "animal_detected": "high",
        "warning": "medium"
    }
    
    alert = {
        "id": len(st.session_state.mobile_alerts) + 1,
        "timestamp": timestamp,
        "title": title,
        "message": message,
        "type": alert_type,
        "priority": priority_map.get(alert_type, "medium"),
        "read": False,
        "data": alert_data,
        "sms_sent": False,
        "sms_recipient": None
    }
    
    st.session_state.mobile_alerts.append(alert)
    logger.info(f"✅ Alert created: {title}")
    
    # Send SMS if enabled
    try:
        enable_sms = st.session_state.get('enable_sms_alerts', False)
        user_phone = st.session_state.get('user_phone_number', '').strip()
        
        logger.info(f"SMS Settings - Enabled: {enable_sms}, Phone: {user_phone[:3] if user_phone else 'None'}...")
        
        if enable_sms and user_phone:
            if sms_system.validate_phone_number(user_phone):
                formatted_phone = sms_system.format_phone_number(user_phone)
                logger.info(f"📱 Sending SMS to: {formatted_phone}")
                
                sms_success = sms_system.send_sms_alert(formatted_phone, alert_data, alert_type)
                
                if sms_success or not sms_system.is_initialized:
                    alert['sms_sent'] = True
                    alert['sms_recipient'] = f"+91{formatted_phone}"
                    logger.info(f"✅ SMS {'sent' if sms_system.is_initialized else 'simulated'}")
                else:
                    logger.warning(f"⚠️ SMS sending failed")
            else:
                logger.warning(f"⚠️ Invalid phone number: {user_phone}")
        else:
            if not enable_sms:
                logger.info("ℹ️ SMS alerts disabled")
            if not user_phone:
                logger.info("ℹ️ No phone number configured")
    
    except Exception as e:
        logger.error(f"❌ Error in SMS: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Keep only last 50 alerts
    if len(st.session_state.mobile_alerts) > 50:
        st.session_state.mobile_alerts = st.session_state.mobile_alerts[-50:]
    
    return alert

def send_emergency_sms(alert_data: Dict) -> bool:
    """Send emergency SMS to all contacts"""
    try:
        import streamlit as st
        emergency_contacts = st.session_state.get('emergency_contacts', [])
        
        if not emergency_contacts:
            logger.warning("⚠️ No emergency contacts configured")
            return False
        
        logger.info(f"📞 Sending emergency SMS to {len(emergency_contacts)} contacts...")
        
        success_count = 0
        for contact in emergency_contacts:
            phone = contact.get('number', '').strip()
            name = contact.get('name', 'Unknown')
            
            if sms_system.validate_phone_number(phone):
                formatted_phone = sms_system.format_phone_number(phone)
                logger.info(f"   → Sending to {name}: {formatted_phone}")
                
                if sms_system.send_sms_alert(formatted_phone, alert_data, "emergency"):
                    success_count += 1
                    logger.info(f"     ✅ Sent to {name}")
            else:
                logger.warning(f"   ⚠️ Invalid number for {name}: {phone}")
        
        logger.info(f"✅ Emergency SMS: {success_count}/{len(emergency_contacts)} successful")
        return success_count > 0
    
    except Exception as e:
        logger.error(f"❌ Error sending emergency SMS: {str(e)}")
        return False

def get_mobile_alerts() -> List[Dict]:
    """Get all mobile alerts"""
    import streamlit as st
    if 'mobile_alerts' not in st.session_state:
        st.session_state.mobile_alerts = []
    return st.session_state.mobile_alerts

def get_unread_count() -> int:
    """Get unread alerts count"""
    return len([a for a in get_mobile_alerts() if not a.get('read', False)])

def get_sms_system_status() -> Dict:
    """Get SMS system status"""
    return sms_system.get_status()

def test_sms_system() -> Dict:
    """Test SMS system"""
    status = sms_system.get_status()
    return {
        "success": status['initialized'],
        "message": f"Active provider: {status['provider']}" if status['initialized'] else "No provider configured",
        "details": status
    }